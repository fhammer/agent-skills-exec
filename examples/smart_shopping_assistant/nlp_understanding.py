"""
自然语言理解模块 - NLP Understanding Module

负责理解用户的自然语言输入，包括意图识别和槽位填充。
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from .types import (
    IntentType, ParsedIntent, SearchCriteria, Sentiment,
    UrgencyLevel, ResponseTone, SemanticUnderstandingResult,
    IntentClassification, SentimentResult
)


@dataclass
class SlotDefinition:
    """槽位定义"""
    name: str
    slot_type: str
    required: bool = False
    description: str = ""
    examples: List[str] = field(default_factory=list)


@dataclass
class ExtractedEntity:
    """提取的实体"""
    entity_type: str
    value: Any
    raw_text: str
    confidence: float = 1.0
    start_pos: int = 0
    end_pos: int = 0


class IntentRecognizer:
    """意图识别器"""

    # 意图关键词映射
    INTENT_KEYWORDS = {
        IntentType.PRODUCT_SEARCH: [
            "找", "搜索", "查", "有没有", "推荐", "想要", "想买", "需要", "看看", "浏览",
            "search", "find", "look for", "recommend", "want", "buy", "need"
        ],
        IntentType.COMPARISON: [
            "对比", "比较", "哪个好", "区别", "差异", "vs", "versus", "compare"
        ],
        IntentType.PRICE_INQUIRY: [
            "多少钱", "价格", "贵不贵", "便宜", "优惠", "打折", "多少钱", "how much", "price", "cost"
        ],
        IntentType.FEATURE_INQUIRY: [
            "功能", "配置", "参数", "性能", "怎么样", "有什么", "feature", "spec", "config"
        ],
        IntentType.GREETING: [
            "你好", "您好", "嗨", "hello", "hi", "早上好", "下午好", "晚上好", "hey"
        ],
        IntentType.PURCHASE_INTENT: [
            "下单", "购买", "付款", "结算", "order", "purchase", "buy", "checkout"
        ],
        IntentType.NAVIGATION: [
            "返回", "后退", "主页", "首页", "分类", "back", "home", "category"
        ]
    }

    # 紧急程度指示词
    URGENCY_INDICATORS = {
        UrgencyLevel.HIGH: ["急需", "马上", "立即", "urgent", "asap", "immediately"],
        UrgencyLevel.MEDIUM: ["尽快", "快点", "soon", "quickly"],
    }

    def recognize(self, user_input: str) -> Tuple[IntentType, float, Dict[str, Any]]:
        """
        识别用户意图

        Returns:
            (意图类型, 置信度, 附加信息)
        """
        user_input_lower = user_input.lower().strip()
        scores = {}
        matched_keywords = {}

        # 计算每个意图的匹配分数
        for intent_type, keywords in self.INTENT_KEYWORDS.items():
            score = 0
            matched = []
            for keyword in keywords:
                if keyword in user_input_lower:
                    # 完全匹配权重更高
                    if keyword == user_input_lower:
                        score += 3
                    # 单词边界匹配
                    elif re.search(r'\b' + re.escape(keyword) + r'\b', user_input_lower):
                        score += 2
                    else:
                        score += 1
                    matched.append(keyword)

            if score > 0:
                scores[intent_type] = score
                matched_keywords[intent_type.value] = matched

        if not scores:
            # 无法识别意图，返回通用聊天意图
            return IntentType.GENERAL_QUERY, 0.3, {"reason": "no_keyword_match"}

        # 找出最高分意图
        best_intent = max(scores, key=scores.get)
        confidence = min(scores[best_intent] / 5, 1.0)  # 归一化置信度

        # 检查是否有歧义
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_scores) > 1:
            score_diff = sorted_scores[0][1] - sorted_scores[1][1]
            if score_diff <= 1:
                confidence *= 0.7  # 降低置信度

        # 检查紧急程度
        urgency = UrgencyLevel.LOW
        for level, indicators in self.URGENCY_INDICATORS.items():
            for indicator in indicators:
                if indicator in user_input_lower:
                    urgency = level
                    break

        return best_intent, confidence, {
            "matched_keywords": matched_keywords.get(best_intent.value, []),
            "all_scores": {k.value: v for k, v in scores.items()},
            "urgency": urgency,
            "ambiguity": len(sorted_scores) > 1 and sorted_scores[0][1] - sorted_scores[1][1] <= 1
        }


class SlotExtractor:
    """槽位提取器"""

    # 价格模式
    PRICE_PATTERNS = [
        r'(\d+)\s*元?\s*以[下内]',
        r'(\d+)\s*元?\s*以[上外]',
        r'(\d+)\s*元?\s*左右?',
        r'[在到至]\s*(\d+)\s*元?',
        r'(\d+)\s*元',
        r'(\d+)\s*块',
        r'(\d+)\s*k',
        r'(\d+)\s*千',
        r'预算[大概约]?\s*(\d+)',
    ]

    # 类别关键词
    CATEGORY_KEYWORDS = {
        "手机": ["手机", "phone", "mobile", "smartphone"],
        "笔记本": ["笔记本", "laptop", "computer", "电脑", "macbook"],
        "平板": ["平板", "tablet", "ipad"],
        "耳机": ["耳机", "headphone", "earphone", "airpod", "earbud"],
        "相机": ["相机", "camera", "单反", "微单"],
        "手表": ["手表", "watch", "手环", "智能手表"],
        "电视": ["电视", "tv", "显示器", "display"],
    }

    # 品牌关键词
    BRAND_KEYWORDS = {
        "苹果": ["苹果", "apple", "iphone", "mac", "ipad", "airpod"],
        "华为": ["华为", "huawei", "mate", "pura", "p系列"],
        "小米": ["小米", "xiaomi", "mi", "redmi", "红米"],
        "三星": ["三星", "samsung", "galaxy"],
        "vivo": ["vivo", "iqoo"],
        "OPPO": ["oppo", "一加", "oneplus", "realme"],
        "联想": ["联想", "lenovo", "thinkpad", "拯救者"],
        "索尼": ["索尼", "sony", "playstation", "ps"],
    }

    def extract(self, user_input: str) -> Dict[str, Any]:
        """提取槽位信息"""
        slots = {}

        # 提取价格范围
        price_info = self._extract_price(user_input)
        if price_info:
            slots["price"] = price_info

        # 提取类别
        category = self._extract_category(user_input)
        if category:
            slots["category"] = category

        # 提取品牌
        brands = self._extract_brands(user_input)
        if brands:
            slots["brand"] = brands

        # 提取颜色
        colors = self._extract_colors(user_input)
        if colors:
            slots["color"] = colors

        # 提取功能需求
        features = self._extract_features(user_input)
        if features:
            slots["features"] = features

        return slots

    def _extract_price(self, text: str) -> Optional[Dict[str, Any]]:
        """提取价格信息"""
        text = text.lower()

        # 查找价格上限
        max_price = None
        min_price = None

        for pattern in self.PRICE_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                try:
                    value = float(match)
                    # 处理k/千单位
                    if 'k' in text or '千' in text:
                        value *= 1000

                    if '以下' in text or '以内' in text:
                        max_price = value
                    elif '以上' in text or '以外' in text:
                        min_price = value
                    elif max_price is None:
                        max_price = value
                except ValueError:
                    continue

        if min_price is not None or max_price is not None:
            return {
                "min": min_price,
                "max": max_price,
                "target": max_price if max_price else min_price
            }

        return None

    def _extract_category(self, text: str) -> Optional[str]:
        """提取商品类别"""
        text_lower = text.lower()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category

        return None

    def _extract_brands(self, text: str) -> List[str]:
        """提取品牌"""
        text_lower = text.lower()
        brands = []

        for brand, keywords in self.BRAND_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower and brand not in brands:
                    brands.append(brand)

        return brands

    def _extract_colors(self, text: str) -> List[str]:
        """提取颜色偏好"""
        color_keywords = {
            "黑色": ["黑", "black"],
            "白色": ["白", "white"],
            "红色": ["红", "red"],
            "蓝色": ["蓝", "blue"],
            "绿色": ["绿", "green"],
            "金色": ["金", "gold", "土豪金"],
            "银色": ["银", "silver", "sliver"],
            "粉色": ["粉", "pink"],
            "紫色": ["紫", "purple"],
            "灰色": ["灰", "grey", "gray"],
        }

        text_lower = text.lower()
        colors = []

        # 检查是否指定了"不要"某种颜色
        excluded_colors = []
        for color_name, keywords in color_keywords.items():
            for keyword in keywords:
                if f"不要{keyword}" in text or f"别{keyword}" in text or f"非{keyword}" in text:
                    excluded_colors.append(color_name)
                    break

        # 提取颜色偏好
        for color_name, keywords in color_keywords.items():
            if color_name in excluded_colors:
                continue

            for keyword in keywords:
                if keyword in text_lower and color_name not in colors:
                    colors.append(color_name)
                    break

        return colors

    def _extract_features(self, text: str) -> List[str]:
        """提取功能需求"""
        feature_keywords = {
            "拍照好": ["拍照", "摄像", "摄影", "相机", "像素", "镜头"],
            "续航长": ["续航", "电池", "电量", "充电", "待机", "耐用"],
            "高性能": ["性能", "速度", "流畅", "快", "处理器", "芯片", "CPU"],
            "轻薄": ["轻薄", "便携", "轻", "薄", "小巧", "迷你"],
            "大屏": ["大屏", "屏幕大", "显示器", "尺寸", "视野"],
            "音质好": ["音质", "音效", "声音", "听歌", "音响"],
            "性价比高": ["性价比", "划算", "实惠", "便宜", "优惠"],
            "游戏性能": ["游戏", "打游戏", "电竞", "GPU", "显卡", "帧率"],
        }

        text_lower = text.lower()
        features = []

        for feature_name, keywords in feature_keywords.items():
            for keyword in keywords:
                if keyword in text_lower and feature_name not in features:
                    features.append(feature_name)
                    break

        return features


class NLPUnderstanding:
    """自然语言理解主类"""

    def __init__(self):
        self.intent_recognizer = IntentRecognizer()
        self.slot_extractor = SlotExtractor()

    def understand(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> SemanticUnderstandingResult:
        """
        理解用户输入

        Args:
            user_input: 用户输入文本
            context: 上下文信息

        Returns:
            SemanticUnderstandingResult: 语义理解结果
        """
        # 1. 意图识别
        intent_type, confidence, intent_info = self.intent_recognizer.recognize(user_input)

        # 2. 槽位提取
        slots = self.slot_extractor.extract(user_input)

        # 3. 构建意图分类结果
        intent_classification = IntentClassification(
            primary_intent=intent_type,
            confidence=confidence,
            slots=slots,
            needs_clarification=intent_info.get("ambiguity", False) or confidence < 0.5,
            clarification_question=self._generate_clarification_question(intent_type, slots) if confidence < 0.5 else ""
        )

        # 4. 构建完整理解结果
        result = SemanticUnderstandingResult(
            intent=intent_classification,
            slots=slots,
            raw_input=user_input,
            urgency=intent_info.get("urgency", UrgencyLevel.LOW),
            confidence=confidence
        )

        return result

    def _generate_clarification_question(self, intent: IntentType, slots: Dict[str, Any]) -> str:
        """生成澄清问题"""
        if intent == IntentType.PRODUCT_SEARCH:
            if "category" not in slots:
                return "您想找什么类型的商品呢？比如手机、笔记本、耳机等。"
            return "我没有完全理解您的需求，您能再详细描述一下吗？"
        elif intent == IntentType.PRICE_INQUIRY:
            return "您想了解哪款商品的价格呢？"
        else:
            return "我没有完全理解您的意思，您能换个方式描述吗？"

    def quick_understand(self, user_input: str) -> Dict[str, Any]:
        """快速理解（简化接口）"""
        result = self.understand(user_input)
        return {
            "intent": result.intent.primary_intent.value,
            "confidence": result.confidence,
            "slots": result.slots,
            "urgency": result.urgency.value
        }
