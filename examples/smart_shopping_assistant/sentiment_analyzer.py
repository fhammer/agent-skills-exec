"""
情感分析模块 - Sentiment Analyzer

分析用户情感状态，识别情绪、紧急程度和满意度。
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .types import (
    Sentiment, SentimentResult, UrgencyLevel, ResponseTone
)


@dataclass
class EmotionIndicators:
    """情绪指示词"""
    positive: List[str] = field(default_factory=lambda: [
        "好", "棒", "赞", "喜欢", "满意", "开心", "感谢", "不错", "优秀", "完美",
        "good", "great", "excellent", "perfect", "love", "like", "happy", "thanks", "thank you"
    ])
    negative: List[str] = field(default_factory=lambda: [
        "差", "糟", "烂", "讨厌", "失望", "生气", "愤怒", "不满", "垃圾", "恶心",
        "bad", "terrible", "awful", "hate", "disappointed", "angry", "annoying", "worst", "suck"
    ])
    urgency: List[str] = field(default_factory=lambda: [
        "急", "马上", "立即", "快点", "赶紧", "尽快", "现在就要", "等不及",
        "urgent", "asap", "immediately", "quickly", "hurry", "rush", "now"
    ])
    frustration: List[str] = field(default_factory=lambda: [
        "受不了", "崩溃", "无语", "头疼", "麻烦", "复杂", "难用",
        "frustrated", "confused", "complicated", "difficult", "annoying", "headache"
    ])
    satisfaction: List[str] = field(default_factory=lambda: [
        "满意", "舒服", "顺手", "方便", "简单", "清晰", "顺畅",
        "satisfied", "comfortable", "convenient", "easy", "simple", "smooth"
    ])


class SentimentAnalyzer:
    """情感分析器"""

    def __init__(self):
        self.indicators = EmotionIndicators()

    def analyze(self, text: str, context: Optional[Dict[str, Any]] = None) -> SentimentResult:
        """
        分析文本情感

        Args:
            text: 用户输入文本
            context: 上下文信息

        Returns:
            SentimentResult: 情感分析结果
        """
        text_lower = text.lower()

        # 1. 分析情感倾向
        positive_score = self._count_matches(text_lower, self.indicators.positive)
        negative_score = self._count_matches(text_lower, self.indicators.negative)

        # 2. 确定情感标签
        if positive_score > 0 and negative_score == 0:
            label = Sentiment.POSITIVE
            confidence = min(0.5 + positive_score * 0.1, 0.95)
        elif negative_score > 0 and positive_score == 0:
            label = Sentiment.NEGATIVE
            confidence = min(0.5 + negative_score * 0.1, 0.95)
        elif positive_score > 0 and negative_score > 0:
            label = Sentiment.MIXED
            confidence = 0.6
        else:
            label = Sentiment.NEUTRAL
            confidence = 0.5

        # 3. 检测紧急程度
        urgency = self._detect_urgency(text_lower)

        # 4. 提取关键情绪词
        key_emotions = self._extract_emotions(text_lower)

        # 5. 检测挫败感指标
        frustration_indicators = self._detect_frustration(text_lower, context)

        return SentimentResult(
            label=label,
            confidence=confidence,
            urgency=urgency,
            key_emotions=key_emotions,
            aspect_sentiments={"frustration_indicators": frustration_indicators}
        )

    def _count_matches(self, text: str, keywords: List[str]) -> int:
        """统计匹配关键词数量"""
        count = 0
        for keyword in keywords:
            count += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
        return count

    def _detect_urgency(self, text: str) -> UrgencyLevel:
        """检测紧急程度"""
        urgency_count = self._count_matches(text, self.indicators.urgency)

        if urgency_count >= 2:
            return UrgencyLevel.HIGH
        elif urgency_count == 1:
            return UrgencyLevel.MEDIUM
        return UrgencyLevel.LOW

    def _extract_emotions(self, text: str) -> List[str]:
        """提取关键情绪词"""
        emotions = []

        for word in self.indicators.positive:
            if word in text:
                emotions.append(f"positive:{word}")

        for word in self.indicators.negative:
            if word in text:
                emotions.append(f"negative:{word}")

        return emotions

    def _detect_frustration(self, text: str, context: Optional[Dict[str, Any]]) -> List[str]:
        """检测挫败感指标"""
        indicators = []

        # 检查挫败感关键词
        for word in self.indicators.frustration:
            if word in text:
                indicators.append(f"keyword:{word}")

        # 检查多次重复（从上下文）
        if context and "history" in context:
            history = context["history"]
            if len(history) > 3:
                # 检查是否多次询问同一问题
                recent_queries = [h.get("user_input", "") for h in history[-3:]]
                if len(set(recent_queries)) < len(recent_queries):
                    indicators.append("repeated_queries")

        # 检查感叹号和问号数量（表达强烈情绪）
        exclamation_count = text.count('!') + text.count('！')
        question_count = text.count('?') + text.count('？')

        if exclamation_count >= 2:
            indicators.append(f"excessive_exclamations:{exclamation_count}")
        if question_count >= 3:
            indicators.append(f"excessive_questions:{question_count}")

        return indicators

    def get_recommended_tone(self, sentiment_result: SentimentResult) -> ResponseTone:
        """根据情感分析结果推荐响应语气"""
        if sentiment_result.label == Sentiment.NEGATIVE:
            if sentiment_result.urgency == UrgencyLevel.HIGH:
                return ResponseTone.EMPATHETIC_URGENT
            return ResponseTone.EMPATHETIC

        elif sentiment_result.label == Sentiment.POSITIVE:
            return ResponseTone.ENTHUSIASTIC

        else:
            if sentiment_result.urgency == UrgencyLevel.HIGH:
                return ResponseTone.PROFESSIONAL
            return ResponseTone.FRIENDLY
