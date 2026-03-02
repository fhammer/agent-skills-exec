"""
智能导购 Agent - 需求分析执行器

分析用户输入，提取商品类别、预算、品牌偏好、使用场景等约束条件。
"""

import re
import json
from typing import Dict, List, Any, Optional
from examples.ecommerce.recommendation.schema import (
    DemandAnalysisResult,
    DemandConstraints,
    PriceRange,
    IntentType,
)


class DemandAnalysisExecutor:
    """需求分析执行器"""

    # 类别关键词映射
    CATEGORY_KEYWORDS = {
        "手机": ["手机", "phone", "iphone", "华为", "小米", "oppo", "vivo"],
        "电脑": ["电脑", "笔记本", "laptop", "macbook", "thinkpad"],
        "耳机": ["耳机", "earphone", "headphone", "airpods"],
        "平板": ["平板", "tablet", "ipad"],
        "相机": ["相机", "camera", "单反"],
        "手表": ["手表", "watch", "手环"],
        "电视": ["电视", "tv", "电视机"],
    }

    # 使用场景关键词
    USE_CASE_KEYWORDS = {
        "gaming": ["游戏", "玩", "游戏本", "电竞"],
        "office": ["办公", "工作", "文档"],
        "photography": ["拍照", "摄影", "拍照好"],
        "music": ["音乐", "听歌", "音质"],
        "video": ["视频", "看视频", "追剧"],
    }

    # 品牌列表
    BRANDS = [
        "苹果", "Apple", "iPhone",
        "华为", "Huawei",
        "小米", "Xiaomi",
        "OPPO", "Vivo",
        "三星", "Samsung",
        "联想", "Lenovo",
        "戴尔", "Dell",
        "惠普", "HP",
        "华硕", "ASUS",
        "索尼", "Sony",
    ]

    # 特性关键词
    FEATURE_KEYWORDS = {
        "性能": ["性能", "处理器", "cpu", "速度快", "流畅"],
        "屏幕": ["屏幕", "显示", "分辨率", "刷新率"],
        "续航": ["续航", "电池", "充电"],
        "拍照": ["拍照", "摄影", "相机"],
        "轻薄": ["轻薄", "便携", "轻"],
        "性价比": ["性价比", "便宜", "实惠"],
    }

    def __init__(self):
        self.brands_pattern = re.compile("|".join(self.BRANDS), re.IGNORECASE)

    def execute(self, user_input: str, conversation_history: Optional[List[Dict]] = None) -> DemandAnalysisResult:
        """
        执行需求分析

        Args:
            user_input: 用户输入
            conversation_history: 对话历史

        Returns:
            需求分析结果
        """
        # 识别意图
        intent = self._detect_intent(user_input)

        # 提取约束条件
        constraints = self._extract_constraints(user_input)

        # 识别缺失信息
        missing_info = self._identify_missing_info(constraints)

        # 计算置信度
        confidence = self._calculate_confidence(constraints, missing_info)

        return DemandAnalysisResult(
            intent=intent,
            constraints=constraints,
            missing_info=missing_info,
            confidence=confidence,
            raw_text=user_input,
        )

    def _detect_intent(self, user_input: str) -> IntentType:
        """检测用户意图"""
        user_input_lower = user_input.lower()

        # 推荐意图
        if any(word in user_input for word in ["推荐", "有什么", "哪个好", "建议"]):
            return IntentType.RECOMMENDATION

        # 对比意图
        if any(word in user_input for word in ["对比", "区别", "哪个更好", "和"]):
            return IntentType.COMPARISON

        # 价格咨询
        if "多少钱" in user_input or "价格" in user_input:
            return IntentType.PRICE_INQUIRY

        # 商品咨询（默认）
        return IntentType.PRODUCT_INQUIRY

    def _extract_constraints(self, user_input: str) -> DemandConstraints:
        """提取约束条件"""
        constraints = DemandConstraints()

        # 提取类别
        constraints.category = self._extract_category(user_input)

        # 提取价格范围
        constraints.price_range = self._extract_price_range(user_input)

        # 提取品牌偏好
        constraints.brands = self._extract_brands(user_input)

        # 提取使用场景
        constraints.use_case = self._extract_use_case(user_input)

        # 提取优先特性
        constraints.priority_features = self._extract_features(user_input)

        return constraints

    def _extract_category(self, user_input: str) -> Optional[str]:
        """提取商品类别"""
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword in user_input for keyword in keywords):
                return category
        return None

    def _extract_price_range(self, user_input: str) -> Optional[PriceRange]:
        """提取价格范围"""
        # 匹配 "2000-3000" 或 "2000到3000" 或 "2000~3000"
        range_pattern = r'(\d+)\s*[-~到]\s*(\d+)'
        range_match = re.search(range_pattern, user_input)

        if range_match:
            min_price = int(range_match.group(1))
            max_price = int(range_match.group(2))
            return PriceRange(min=min_price, max=max_price)

        # 匹配 "2000以下" 或 "3000以上"
        below_pattern = r'(\d+)\s*(以下|以内|之内)'
        below_match = re.search(below_pattern, user_input)
        if below_match:
            return PriceRange(max=int(below_match.group(1)))

        above_pattern = r'(\d+)\s*(以上|超过)'
        above_match = re.search(above_pattern, user_input)
        if above_match:
            return PriceRange(min=int(above_match.group(1)))

        # 匹配单独的价格
        single_pattern = r'(?<![以下以上以内超过])(\d{3,5})元?(?![0-9])'
        single_match = re.search(single_pattern, user_input)
        if single_match:
            price = int(single_match.group(1))
            # 假设是预算上限
            return PriceRange(max=price)

        return None

    def _extract_brands(self, user_input: str) -> List[str]:
        """提取品牌偏好"""
        brands = []
        for brand in self.BRANDS:
            if brand in user_input:
                brands.append(brand)

        # 处理排除品牌 "不要xxx" 或 "不要xxx牌"
        exclude_pattern = r'(不要|不喜欢|非|排除)\s*({})'.format("|".join(self.BRANDS))
        exclude_matches = re.findall(exclude_pattern, user_input)
        if exclude_matches:
            return []  # 如果有排除品牌，暂不返回偏好品牌

        return brands

    def _extract_use_case(self, user_input: str) -> Optional[str]:
        """提取使用场景"""
        for use_case, keywords in self.USE_CASE_KEYWORDS.items():
            if any(keyword in user_input for keyword in keywords):
                return use_case
        return None

    def _extract_features(self, user_input: str) -> List[str]:
        """提取优先特性"""
        features = []
        for feature, keywords in self.FEATURE_KEYWORDS.items():
            if any(keyword in user_input for keyword in keywords):
                features.append(feature)
        return features

    def _identify_missing_info(self, constraints: DemandConstraints) -> List[str]:
        """识别缺失信息"""
        missing = []

        if not constraints.category:
            missing.append("商品类别")

        if not constraints.price_range:
            missing.append("预算范围")

        if not constraints.use_case:
            missing.append("使用场景/用途")

        if not constraints.brands:
            missing.append("品牌偏好")

        return missing

    def _calculate_confidence(self, constraints: DemandConstraints, missing_info: List[str]) -> float:
        """计算置信度"""
        total_fields = 5  # category, price_range, brands, use_case, priority_features
        filled_fields = 0

        if constraints.category:
            filled_fields += 1
        if constraints.price_range and constraints.price_range.is_valid():
            filled_fields += 1
        if constraints.brands:
            filled_fields += 1
        if constraints.use_case:
            filled_fields += 1
        if constraints.priority_features:
            filled_fields += 1

        return filled_fields / total_fields


# 对外接口函数
def execute(user_input: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    执行需求分析

    Args:
        user_input: 用户输入
        context: 上下文信息

    Returns:
        分析结果字典
    """
    executor = DemandAnalysisExecutor()
    result = executor.execute(user_input)

    return {
        "structured": result.to_dict(),
        "text": f"已识别您的需求：{result.constraints.category or '未指定类别'}" +
               (f"，预算{result.constraints.price_range.min}-{result.constraints.price_range.max}元" if result.constraints.price_range else "") +
               (f"，用于{result.constraints.use_case}" if result.constraints.use_case else "") +
               (f"\n还需要了解：{', '.join(result.missing_info)}" if result.missing_info else ""),
    }
