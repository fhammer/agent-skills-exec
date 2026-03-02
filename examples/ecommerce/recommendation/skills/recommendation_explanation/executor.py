"""推荐解释 Skill 执行器

生成自然语言的推荐理由说明
"""

from typing import Dict, Any, List

# LLMBase 类型提示（实际不依赖具体实现）
try:
    from agent.llm_base import LLMProvider as LLMBase
except ImportError:
    LLMBase = Any


# 属性描述模板
ATTRIBUTE_DESCRIPTIONS = {
    "processor": {
        "骁龙8 Gen2": "旗舰处理器，性能强劲，游戏、多任务处理轻松应对",
        "骁龙8+ Gen1": "高端处理器，性能表现出色",
        "天玑9200": "旗舰芯片，性能强劲，功耗控制优秀",
    },
    "screen": {
        "120Hz": "高刷新率屏幕，滑动流畅，游戏体验佳",
        "144Hz": "超高刷新率，电竞级体验",
        "2K": "超清分辨率，显示细腻",
        "护眼屏": "专业护眼认证，长时间使用不疲劳",
    },
    "battery": {
        "5000mAh": "大容量电池，续航持久",
        "5500mAh": "超大电池，重度使用也能撑一天",
    },
    "charging": {
        "120W快充": "超级快充，充电10分钟就能玩好几局",
        "100W快充": "快充加持，短时间内即可充满",
        "150W快充": "业内领先快充速度",
    },
    "camera": {
        "5000万像素": "高像素主摄，拍照清晰细腻",
    }
}


def execute(llm: LLMBase, sub_task: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """执行推荐解释"""

    recommendations = context.get("recommendations", [])
    user_input = context.get("user_input", "")

    if not recommendations:
        return {
            "structured": {"response_type": "no_results"},
            "text": "抱歉，没有找到符合您需求的商品。您可以调整一下筛选条件试试。"
        }

    # 生成推荐文本
    text = _generate_recommendation_text(recommendations, user_input)

    return {
        "structured": {
            "response_type": "recommendation",
            "products_count": len(recommendations)
        },
        "text": text
    }


def _generate_recommendation_text(recommendations: List[Dict], user_input: str) -> str:
    """生成推荐文本"""

    lines = []

    # 开头
    if "推荐" in user_input or "买" in user_input:
        lines.append("根据您的需求，我为您推荐以下几款商品：\n")
    else:
        lines.append("为您找到以下商品：\n")

    # 首选推荐
    if recommendations:
        top_product = recommendations[0]
        product = top_product.get("product", {})
        lines.append(f"**首选推荐：{product.get('name', 'Unknown')} (¥{product.get('price', 0)})**\n")
        lines.append("\n推荐理由：\n")

        # 生成推荐理由
        reasons = top_product.get("recommendation_reasons", [])
        for i, reason in enumerate(reasons[:5], 1):
            lines.append(f"{i}. {reason}\n")

        # 添加详细卖点
        lines.append("\n主要特点：\n")
        attributes = product.get("attributes", {})
        for attr_name, attr_value in attributes.items():
            if attr_value in ATTRIBUTE_DESCRIPTIONS.get(attr_name, {}):
                lines.append(f"- {ATTRIBUTE_DESCRIPTIONS[attr_name][attr_value]}\n")
            else:
                lines.append(f"- {attr_value}\n")

    # 备选方案
    if len(recommendations) > 1:
        lines.append("\n**备选方案：**\n")
        for i, item in enumerate(recommendations[1:6], 2):
            product = item.get("product", {})
            reasons = item.get("recommendation_reasons", [])
            highlight_reason = reasons[0] if reasons else "性价比高"
            lines.append(
                f"{i}. **{product.get('name', 'Unknown')} (¥{product.get('price', 0)})** "
                f"- {highlight_reason}\n"
            )

    # 结尾
    lines.append("\n需要我详细介绍哪款商品的更多信息吗？")

    return "".join(lines)


def _generate_product_highlights(product: Dict[str, Any]) -> List[str]:
    """生成商品亮点"""

    highlights = []

    attributes = product.get("attributes", {})

    # 性能亮点
    processor = attributes.get("processor", "")
    if "骁龙8" in processor or "天玑9" in processor:
        highlights.append("旗舰性能")

    # 屏幕亮点
    screen = attributes.get("screen", "")
    if "120Hz" in screen or "144Hz" in screen:
        highlights.append("高刷屏")
    if "2K" in screen:
        highlights.append("超清屏")

    # 充电亮点
    charging = attributes.get("charging", "")
    if "100W" in charging or "120W" in charging or "150W" in charging:
        highlights.append("超级快充")

    # 电池亮点
    battery = attributes.get("battery", "")
    if "5000mAh" in battery:
        highlights.append("长续航")

    return highlights[:3]
