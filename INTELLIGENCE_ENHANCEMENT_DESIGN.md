# 智能增强详细设计文档

## 1. 语义理解层

### 1.1 当前问题

**意图识别使用简单关键词匹配**：
```python
# 当前实现 - 关键词匹配
def _detect_intent(text: str) -> tuple[SupportIntent, float]:
    text_lower = text.lower()

    for intent in priority_order:
        keywords = INTENT_KEYWORDS[intent]
        for keyword in keywords:
            if keyword in text:
                return intent, 0.8  # 固定置信度
```

**问题**：
1. 无法理解语义相似性："我想退掉这个东西" vs "我不要了"
2. 无法处理歧义："我要退货"可能指退款或换货
3. 缺乏常识推理：无法理解"屏幕碎了"暗示质量问题

### 1.2 工业级设计方案

**核心架构**：

```python
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from abc import ABC, abstractmethod

class IntentConfidence(Enum):
    HIGH = "high"      # > 0.8
    MEDIUM = "medium"  # 0.5 - 0.8
    LOW = "low"        # < 0.5

@dataclass
class IntentClassificationResult:
    """意图分类结果"""
    primary_intent: str
    confidence: float
    confidence_level: IntentConfidence
    alternative_intents: List[Tuple[str, float]]
    reasoning: str  # LLM的推理过程
    slots: Dict[str, Any]  # 提取的槽位

@dataclass
class SemanticUnderstandingResult:
    """语义理解结果"""
    intent_result: IntentClassificationResult
    entities: List[Dict[str, Any]]  # 命名实体
    sentiment: Dict[str, Any]  # 情感分析
    topic: Optional[str]  # 主题
    urgency: float  # 紧急程度 0-1
    context_references: List[str]  # 对上下文的引用

class EmbeddingProvider(ABC):
    """嵌入向量提供者基类"""

    @abstractmethod
    async def get_embedding(self, text: str) -> np.ndarray:
        """获取文本的嵌入向量"""
        pass

    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """批量获取嵌入向量"""
        pass

class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI嵌入向量提供者"""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        self._client = None

    async def get_embedding(self, text: str) -> np.ndarray:
        """获取文本的嵌入向量"""
        if not self._client:
            import openai
            self._client = openai.AsyncOpenAI(api_key=self.api_key)

        response = await self._client.embeddings.create(
            model=self.model,
            input=text
        )

        return np.array(response.data[0].embedding)

    async def get_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """批量获取嵌入向量"""
        if not self._client:
            import openai
            self._client = openai.AsyncOpenAI(api_key=self.api_key)

        response = await self._client.embeddings.create(
            model=self.model,
            input=texts
        )

        return [np.array(item.embedding) for item in response.data]

class IntentClassifier:
    """意图分类器 - 基于LLM + 向量检索"""

    def __init__(
        self,
        llm_client: Any,
        embedding_provider: EmbeddingProvider,
        vector_store: Optional[Any] = None
    ):
        self.llm_client = llm_client
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self._intent_definitions: Dict[str, Dict] = {}
        self._few_shot_examples: List[Dict] = []

    def register_intent(
        self,
        intent_name: str,
        description: str,
        examples: List[str],
        slots: Optional[List[Dict]] = None
    ) -> None:
        """注册意图定义

        Args:
            intent_name: 意图名称
            description: 意图描述
            examples: 示例语句
            slots: 槽位定义（可选）
        """
        self._intent_definitions[intent_name] = {
            "name": intent_name,
            "description": description,
            "examples": examples,
            "slots": slots or []
        }

        # 如果配置了向量存储，索引这些示例
        if self.vector_store:
            for example in examples:
                # 异步索引（这里简化处理）
                pass

    def add_few_shot_examples(self, examples: List[Dict]) -> None:
        """添加Few-shot示例

        Args:
            examples: 示例列表，每个示例包含input、intent、slots
        """
        self._few_shot_examples.extend(examples)

    async def classify(
        self,
        user_input: str,
        context: Optional[Dict] = None,
        top_k: int = 3
    ) -> IntentClassificationResult:
        """意图分类

        Args:
            user_input: 用户输入
            context: 上下文信息
            top_k: 返回前k个候选意图

        Returns:
            意图分类结果
        """
        # 1. 构建Prompt
        prompt = self._build_classification_prompt(user_input, context)

        # 2. 调用LLM进行分类
        llm_response = await self.llm_client.invoke(
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        # 3. 解析LLM响应
        classification = self._parse_llm_response(llm_response)

        # 4. 计算置信度
        confidence = self._calculate_confidence(classification, user_input)
        confidence_level = self._get_confidence_level(confidence)

        # 5. 提取槽位
        slots = await self._extract_slots(user_input, classification["primary_intent"])

        return IntentClassificationResult(
            primary_intent=classification["primary_intent"],
            confidence=confidence,
            confidence_level=confidence_level,
            alternative_intents=classification.get("alternatives", []),
            reasoning=classification.get("reasoning", ""),
            slots=slots
        )

    def _build_classification_prompt(
        self,
        user_input: str,
        context: Optional[Dict]
    ) -> str:
        """构建分类Prompt"""
        prompt_parts = []

        # 用户输入
        prompt_parts.append(f"用户输入: {user_input}")

        # 上下文（如果有）
        if context:
            prompt_parts.append(f"上下文: {json.dumps(context, ensure_ascii=False)}")

        # 可用意图
        prompt_parts.append("\n可用意图:")
        for intent_name, intent_def in self._intent_definitions.items():
            prompt_parts.append(f"- {intent_name}: {intent_def['description']}")
            prompt_parts.append(f"  示例: {', '.join(intent_def['examples'][:2])}")

        # Few-shot示例
        if self._few_shot_examples:
            prompt_parts.append("\n示例:")
            for example in self._few_shot_examples[:3]:
                prompt_parts.append(f"输入: {example['input']}")
                prompt_parts.append(f"意图: {example['intent']}")
                prompt_parts.append("")

        # 输出格式说明
        prompt_parts.append("\n请分析用户输入，输出JSON格式:")
        prompt_parts.append(json.dumps({
            "primary_intent": "主要意图",
            "confidence": 0.95,
            "reasoning": "推理过程",
            "alternatives": [
                {"intent": "备选意图1", "confidence": 0.3},
                {"intent": "备选意图2", "confidence": 0.2}
            ]
        }, ensure_ascii=False, indent=2))

        return "\n".join(prompt_parts)

    def _get_system_prompt(self) -> str:
        """获取系统Prompt"""
        return """你是一个意图分类专家。你的任务是分析用户的输入，识别用户的真实意图。

请遵循以下原则：
1. 深入理解用户输入的语义，不要仅仅依赖关键词匹配
2. 考虑上下文信息，理解用户的真实需求
3. 如果用户输入存在歧义，选择最可能的意图，并在alternatives中列出其他可能性
4. 提供详细的推理过程（reasoning字段）
5. confidence应该在0-1之间，表示你对分类结果的置信度

输出必须是合法的JSON格式。"""

    def _parse_llm_response(self, llm_response: str) -> Dict:
        """解析LLM响应"""
        try:
            # 尝试解析JSON
            result = json.loads(llm_response)

            # 验证必需字段
            if "primary_intent" not in result:
                raise ValueError("Missing 'primary_intent' field")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            # 尝试从文本中提取JSON
            return self._extract_json_from_text(llm_response)

    def _extract_json_from_text(self, text: str) -> Dict:
        """从文本中提取JSON"""
        import re

        # 尝试匹配JSON代码块
        json_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
        matches = re.findall(json_pattern, text, re.DOTALL)

        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue

        # 尝试匹配花括号包围的JSON
        json_pattern = r'\{[^{}]*\}'
        matches = re.findall(json_pattern, text)

        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        # 如果都无法解析，返回默认值
        logger.error("Failed to extract JSON from text")
        return {
            "primary_intent": "unknown",
            "confidence": 0.0,
            "reasoning": "Failed to parse LLM response",
            "alternatives": []
        }

    def _calculate_confidence(self, classification: Dict, user_input: str) -> float:
        """计算置信度"""
        # 1. LLM返回的置信度
        llm_confidence = classification.get("confidence", 0.5)

        # 2. 基于备选意图数量的调整
        alternatives = classification.get("alternatives", [])
        if alternatives:
            # 如果有很多备选意图，降低置信度
            alt_confidences = [alt.get("confidence", 0) for alt in alternatives]
            max_alt_confidence = max(alt_confidences) if alt_confidences else 0

            # 如果最佳备选意图的置信度接近主意图，降低置信度
            if max_alt_confidence > llm_confidence * 0.8:
                llm_confidence *= 0.8

        # 3. 基于输入长度的调整
        if len(user_input) < 5:
            # 输入太短，置信度降低
            llm_confidence *= 0.9

        return min(1.0, max(0.0, llm_confidence))

    def _get_confidence_level(self, confidence: float) -> IntentConfidence:
        """获取置信度级别"""
        if confidence > 0.8:
            return IntentConfidence.HIGH
        elif confidence > 0.5:
            return IntentConfidence.MEDIUM
        else:
            return IntentConfidence.LOW

    async def _extract_slots(self, user_input: str, intent: str) -> Dict[str, Any]:
        """提取槽位"""
        # 获取意图定义
        intent_def = self._intent_definitions.get(intent)
        if not intent_def or not intent_def.get("slots"):
            return {}

        slots = {}

        # 方法1：使用LLM提取槽位
        try:
            slot_prompt = self._build_slot_extraction_prompt(
                user_input, intent, intent_def["slots"]
            )

            llm_response = await self.llm_client.invoke(
                messages=[
                    {"role": "system", "content": "你是一个槽位提取专家。请从用户输入中提取指定类型的信息。"},
                    {"role": "user", "content": slot_prompt}
                ],
                response_format={"type": "json_object"}
            )

            extracted_slots = json.loads(llm_response)
            slots.update(extracted_slots)

        except Exception as e:
            logger.error(f"LLM slot extraction failed: {e}")

        # 方法2：使用规则提取（作为备选）
        for slot_def in intent_def.get("slots", []):
            slot_name = slot_def["name"]
            if slot_name not in slots:
                # 尝试规则提取
                extracted = self._extract_slot_by_rule(
                    user_input, slot_def
                )
                if extracted:
                    slots[slot_name] = extracted

        return slots

    def _build_slot_extraction_prompt(
        self,
        user_input: str,
        intent: str,
        slot_definitions: List[Dict]
    ) -> str:
        """构建槽位提取Prompt"""
        prompt_parts = [
            f"用户输入: {user_input}",
            f"意图: {intent}",
            "\n需要从用户输入中提取以下信息："
        ]

        slot_schema = {}
        for slot_def in slot_definitions:
            slot_name = slot_def["name"]
            slot_type = slot_def.get("type", "string")
            slot_desc = slot_def.get("description", "")

            prompt_parts.append(f"- {slot_name} ({slot_type}): {slot_desc}")

            # 构建JSON schema
            if slot_type == "string":
                slot_schema[slot_name] = {"type": "string"}
            elif slot_type == "number":
                slot_schema[slot_name] = {"type": "number"}
            elif slot_type == "boolean":
                slot_schema[slot_name] = {"type": "boolean"}
            else:
                slot_schema[slot_name] = {"type": "string"}

        prompt_parts.append("\n请输出JSON格式，包含提取的槽位信息：")
        prompt_parts.append(json.dumps(slot_schema, indent=2, ensure_ascii=False))

        prompt_parts.append("\n注意：")
        prompt_parts.append("- 如果某个槽位在用户输入中没有提到，不要包含该字段")
        prompt_parts.append("- 确保提取的值符合要求的类型")
        prompt_parts.append("- 对于日期时间，使用ISO 8601格式")

        return "\n".join(prompt_parts)

    def _extract_slot_by_rule(self, user_input: str, slot_def: Dict) -> Optional[Any]:
        """使用规则提取槽位"""
        import re

        slot_type = slot_def.get("type", "string")
        patterns = slot_def.get("patterns", [])

        if slot_type == "number":
            # 提取数字
            number_patterns = [
                r'(\d+(?:\.\d+)?)',  # 整数或小数
                r'(\d{1,3}(?:,\d{3})+(?:\.\d+)?)',  # 千分位数字
            ]
            for pattern in number_patterns:
                match = re.search(pattern, user_input)
                if match:
                    number_str = match.group(1).replace(',', '')
                    try:
                        if '.' in number_str:
                            return float(number_str)
                        else:
                            return int(number_str)
                    except ValueError:
                        continue

        elif slot_type == "date":
            # 提取日期
            date_patterns = [
                r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # 2024-01-15
                r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',  # 15/01/2024
                r'(明天|后天|大后天|今天|昨天)',  # 相对日期
            ]
            for pattern in date_patterns:
                match = re.search(pattern, user_input)
                if match:
                    return match.group(1)

        elif slot_type == "email":
            # 提取邮箱
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            match = re.search(email_pattern, user_input)
            if match:
                return match.group(0)

        elif slot_type == "phone":
            # 提取手机号
            phone_patterns = [
                r'1[3-9]\d{9}',  # 中国手机号
                r'\d{3,4}-?\d{7,8}',  # 固话
            ]
            for pattern in phone_patterns:
                match = re.search(pattern, user_input)
                if match:
                    return match.group(0)

        # 使用自定义正则表达式
        for pattern in patterns:
            match = re.search(pattern, user_input)
            if match:
                return match.group(1) if match.groups() else match.group(0)

        return None

    def _extract_slot_by_rule(self, user_input: str, slot_def: Dict) -> Optional[Any]:
        """使用规则提取槽位"""
        import re

        slot_type = slot_def.get("type", "string")
        patterns = slot_def.get("patterns", [])

        if slot_type == "number":
            # 提取数字
            number_patterns = [
                r'(\d+(?:\.\d+)?)',  # 整数或小数
                r'(\d{1,3}(?:,\d{3})+(?:\.\d+)?)',  # 千分位数字
            ]
            for pattern in number_patterns:
                match = re.search(pattern, user_input)
                if match:
                    number_str = match.group(1).replace(',', '')
                    try:
                        if '.' in number_str:
                            return float(number_str)
                        else:
                            return int(number_str)
                    except ValueError:
                        continue

        elif slot_type == "date":
            # 提取日期
            date_patterns = [
                r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # 2024-01-15
                r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',  # 15/01/2024
                r'(明天|后天|大后天|今天|昨天)',  # 相对日期
            ]
            for pattern in date_patterns:
                match = re.search(pattern, user_input)
                if match:
                    return match.group(1)

        elif slot_type == "email":
            # 提取邮箱
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            match = re.search(email_pattern, user_input)
            if match:
                return match.group(0)

        elif slot_type == "phone":
            # 提取手机号
            phone_patterns = [
                r'1[3-9]\d{9}',  # 中国手机号
                r'\d{3,4}-?\d{7,8}',  # 固话
            ]
            for pattern in phone_patterns:
                match = re.search(pattern, user_input)
                if match:
                    return match.group(0)

        # 使用自定义正则表达式
        for pattern in patterns:
            match = re.search(pattern, user_input)
            if match:
                return match.group(1) if match.groups() else match.group(0)

        return None
