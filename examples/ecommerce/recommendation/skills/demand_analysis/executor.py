"""需求分析 Skill 执行器

分析用户需求，提取商品类别、预算、品牌偏好、使用场景等约束条件
"""

import re
import json
from typing import Dict, Any, List, Optional

# LLMBase 类型提示（实际不依赖具体实现）
try:
    from agent.llm_base import LLMProvider as LLMBase
except ImportError:
    LLMBase = Any


# 价格关键词映射
PRICE_KEYWORDS = {
    "便宜": {"max": 1000},
    "平价": {"min": 500, "max": 1500},
    "中端": {"min": 1500, "max": 3000},
    "高端": {"min": 3000, "max": 6000},
    "旗舰": {"min": 5000},
    "性价比": {"min": 1500, "max": 3000},
}

# 品牌列表
BRANDS = [
    "小米", "华为", "苹果", "OPPO", "vivo", "一加", "真我", "荣耀",
    "三星", "Redmi", "iQOO", "魅族", "努比亚", "联想", "戴尔", "华硕",
    "索尼", "Bose", "森海塞尔", "铁三角", "JBL", "HarmanKardon"
]

# 类别关键词
CATEGORY_KEYWORDS = {
    "手机": ["手机", "iPhone", "安卓机"],
    "耳机": ["耳机", "耳塞", "头戴式", "入耳式"],
    "电脑": ["电脑", "笔记本", "台式机", "笔记本"],
    "平板": ["平板", "iPad", "tablet"],
    "手表": ["手表", "手环", "智能手表", "watch"],
    "相机": ["相机", "摄像机", "单反", "微单"],
}

# 使用场景
USE_CASES = {
    "游戏": ["游戏", "玩游戏", "电竞", "开黑"],
    "办公": ["办公", "工作", "文档", "商务"],
    "拍照": ["拍照", "摄影", "拍照", "摄像"],
    "学习": ["学习", "上课", "网课", "读书"],
    "运动": ["运动", "跑步", "健身", "锻炼"],
    "音乐": ["听歌", "音乐", "音质", "听音乐"],
}


def execute(llm: LLMBase, sub_task: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """执行需求分析"""

    user_input = context.get("user_input", sub_task)
    conversation_history = context.get("conversation_history", [])

    # 提取类别
    category = _extract_category(user_input)

    # 提取价格区间
    price_range = _extract_price_range(user_input)

    # 提取品牌偏好
    brand_preference = _extract_brands(user_input)

    # 提取使用场景
    use_case = _extract_use_case(user_input)

    # 提取特殊要求
    special_requirements = _extract_special_requirements(user_input)

    # 检查缺失信息
    missing_info = []
    if not category:
        missing_info.append("商品类别")
    if not price_range:
        missing_info.append("预算范围")
    if not use_case:
        missing_info.append("使用场景")

    # 构建结构化输出
    structured = {
        "intent": "product_inquiry" if category else "clarification_needed",
        "category": category,
        "constraints": {
            "price_range": price_range,
            "brands": brand_preference,
            "use_case": use_case,
            "special_requirements": special_requirements,
        },
        "missing_info": missing_info,
    }

    # 生成回复文本
    if missing_info:
        text = _generate_clarification_question(structured)
    else:
        text = _generate_confirmation_text(structured)

    return {
        "structured": structured,
        "text": text
    }


def _extract_category(text: str) -> Optional[str]:
    """提取商品类别"""
    text_lower = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category
    return None


def _extract_price_range(text: str) -> Optional[Dict[str, int]]:
    """提取价格区间"""
    # 匹配具体价格区间: "2000-3000元", "2000到3000"
    range_pattern = r'(\d+)\s*[-~到至]\s*(\d+)\s*[元块]'
    match = re.search(range_pattern, text)
    if match:
        return {"min": int(match.group(1)), "max": int(match.group(2))}

    # 匹配价格上限: "2000元以下", "不超过2000"
    max_pattern = r'(\d+)\s*[元块]\s*(以下|以内|不超过|内)'
    match = re.search(max_pattern, text)
    if match:
        return {"min": 0, "max": int(match.group(1))}

    # 匹配价格下限: "2000元以上"
    min_pattern = r'(\d+)\s*[元块]\s*(以上|超过|起)'
    match = re.search(min_pattern, text)
    if match:
        return {"min": int(match.group(1)), "max": 99999}

    # 匹配关键词
    for keyword, price_range in PRICE_KEYWORDS.items():
        if keyword in text:
            return price_range

    return None


def _extract_brands(text: str) -> List[str]:
    """提取品牌偏好"""
    found_brands = []
    for brand in BRANDS:
        if brand in text:
            found_brands.append(brand)
    return found_brands


def _extract_use_case(text: str) -> Optional[str]:
    """提取使用场景"""
    for use_case, keywords in USE_CASES.items():
        if any(keyword in text for keyword in keywords):
            return use_case
    return None


def _extract_special_requirements(text: str) -> List[str]:
    """提取特殊要求"""
    requirements = []

    special_keywords = {
        "轻薄": ["轻薄", "轻便", "便携"],
        "续航": ["续航", "电池", "持久"],
        "高刷": ["高刷", "高刷新率", "120Hz", "144Hz"],
        "防水": ["防水", "防水"],
        "降噪": ["降噪", "主动降噪", "ANC"],
        "无线": ["无线", "蓝牙", "无线"],
    }

    for requirement, keywords in special_keywords.items():
        if any(keyword in text for keyword in keywords):
            requirements.append(requirement)

    return requirements


def _generate_clarification_question(structured: Dict) -> str:
    """生成澄清问题"""
    missing = structured.get("missing_info", [])

    category = structured.get("category")
    constraints = structured.get("constraints", {})
    price_range = constraints.get("price_range")

    if "商品类别" in missing:
        return "请问您想购买哪类商品呢？比如手机、耳机、电脑等。"

    if "预算范围" in missing:
        if category:
            return f"好的，您想买{category}。请问您的预算大概是多少？"
        return "请问您的预算大概是多少？"

    if "使用场景" in missing:
        if category and price_range:
            budget_text = f"{price_range['min']}-{price_range['max']}元" if price_range else ""
            return f"好的，您想买{budget_text}的{category}。请问主要用途是什么？比如办公、游戏、拍照等。"

    return "请问还有什么特殊要求吗？比如品牌偏好、颜色等。"


def _generate_confirmation_text(structured: Dict) -> str:
    """生成确认文本"""
    category = structured.get("category")
    constraints = structured.get("constraints", {})
    price_range = constraints.get("price_range")
    brands = constraints.get("brands", [])
    use_case = constraints.get("use_case")
    special = constraints.get("special_requirements", [])

    parts = []
    if price_range:
        parts.append(f"预算{price_range['min']}-{price_range['max']}元")
    if category:
        parts.append(f"购买{category}")
    if brands:
        parts.append(f"偏好{','.join(brands)}品牌")
    if use_case:
        parts.append(f"主要用于{use_case}")
    if special:
        parts.append(f"需要{','.join(special)}功能")

    if parts:
        return "已记录您的需求：" + "，".join(parts) + "。"

    return "收到您的需求，正在为您搜索合适的商品..."
