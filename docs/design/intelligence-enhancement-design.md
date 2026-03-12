

## 3. 记忆系统设计

### 3.1 架构概述

记忆系统采用三层架构：

```
┌─────────────────────────────────────────────────────────────────┐
│                      记忆系统架构                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │   短期工作记忆   │  │   长期用户画像   │  │   向量记忆库     │   │
│  │  (Session级)   │  │  (User级)       │  │  (Global级)    │   │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤   │
│  │ • 当前对话状态   │  │ • 人口统计学    │  │ • 商品向量      │   │
│  │ • 已填槽位     │  │ • 行为模式     │  │ • 用户偏好向量  │   │
│  │ • 候选商品     │  │ • 偏好演化     │  │ • 对话历史向量  │   │
│  │ • 澄清问题     │  │ • 购买力模型   │  │ • 意图模式向量  │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    记忆管理器 (Memory Manager)              │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │    │
│  │  │ 记忆写入     │  │ 记忆检索     │  │ 记忆融合     │      │    │
│  │  │ • 实时更新   │  │ • 语义搜索   │  │ • 冲突解决   │      │    │
│  │  │ • 定期合并   │  │ • 相似度排序 │  │ • 权重调整   │      │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 核心实现代码

```python
# memory_system/core.py

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
import numpy as np
from abc import ABC, abstractmethod

class MemoryType(Enum):
    """记忆类型"""
    SHORT_TERM = "short_term"      # 短期工作记忆
    LONG_TERM = "long_term"        # 长期用户画像
    EPISODIC = "episodic"          #  episodic记忆（具体对话片段）
    SEMANTIC = "semantic"          # 语义记忆（抽象知识）

class MemoryPriority(Enum):
    """记忆优先级"""
    CRITICAL = 5    # 关键信息（如用户明确偏好）
    HIGH = 4        # 重要信息（如购买历史）
    MEDIUM = 3      # 普通信息（如浏览记录）
    LOW = 2         # 次要信息
    EPHEMERAL = 1   # 临时信息

@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str
    type: MemoryType
    content: Dict[str, Any]
    timestamp: datetime
    priority: MemoryPriority
    tags: List[str] = field(default_factory=list)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    source: Optional[str] = None  # 来源对话ID
    confidence: float = 1.0  # 置信度

    def to_vector(self) -> np.ndarray:
        """转换为向量表示（用于语义搜索）"""
        # 实际实现中应该使用embedding模型
        # 这里简化处理
        content_str = json.dumps(self.content, ensure_ascii=False)
        # 使用简单的hash作为placeholder
        hash_val = int(hashlib.md5(content_str.encode()).hexdigest(), 16)
        return np.array([hash_val % 10000 / 10000.0])

    def touch(self):
        """更新访问记录"""
        self.access_count += 1
        self.last_accessed = datetime.now()

class ShortTermMemory:
    """
    短期工作记忆（Session级别）

    特点：
    - 当前对话会话内有效
    - 容量有限（7±2原则）
    - 快速读写
    - 会话结束即清空（或归档到长期记忆）
    """

    CAPACITY = 9  # 工作记忆容量

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.entries: Dict[str, MemoryEntry] = {}
        self.focus_stack: List[str] = []  # 焦点栈，用于追踪当前关注主题
        self.slots_filled: Dict[str, Any] = {}  # 已填槽位
        self.clarification_questions: List[str] = []  # 待澄清问题

    def add(self, content: Dict[str, Any], priority: MemoryPriority = MemoryPriority.MEDIUM) -> str:
        """添加记忆条目"""
        # 检查容量，如果满了则移除最低优先级的
        if len(self.entries) >= self.CAPACITY:
            self._evict_lowest_priority()

        entry_id = f"stm_{self.session_id}_{datetime.now().timestamp()}"
        entry = MemoryEntry(
            id=entry_id,
            type=MemoryType.SHORT_TERM,
            content=content,
            timestamp=datetime.now(),
            priority=priority,
            source=self.session_id
        )
        self.entries[entry_id] = entry
        self.focus_stack.append(entry_id)
        return entry_id

    def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """获取记忆条目"""
        entry = self.entries.get(entry_id)
        if entry:
            entry.touch()
        return entry

    def get_current_focus(self) -> Optional[MemoryEntry]:
        """获取当前焦点"""
        if self.focus_stack:
            return self.get(self.focus_stack[-1])
        return None

    def update_slot(self, slot_name: str, value: Any):
        """更新槽位值"""
        self.slots_filled[slot_name] = value

    def get_missing_slots(self, required_slots: List[str]) -> List[str]:
        """获取缺失的槽位"""
        return [slot for slot in required_slots if slot not in self.slots_filled]

    def _evict_lowest_priority(self):
        """移除最低优先级的条目"""
        if not self.entries:
            return
        lowest = min(self.entries.values(), key=lambda e: (e.priority.value, e.timestamp))
        del self.entries[lowest.id]
        if lowest.id in self.focus_stack:
            self.focus_stack.remove(lowest.id)

    def to_context_string(self) -> str:
        """转换为上下文字符串"""
        lines = ["=== 当前工作记忆 ==="]

        # 焦点信息
        focus = self.get_current_focus()
        if focus:
            lines.append(f"当前焦点: {focus.content.get('topic', '未知')}")

        # 已填槽位
        if self.slots_filled:
            lines.append("已收集信息:")
            for slot, value in self.slots_filled.items():
                lines.append(f"  - {slot}: {value}")

        # 待澄清问题
        if self.clarification_questions:
            lines.append("待澄清:")
            for q in self.clarification_questions:
                lines.append(f"  - {q}")

        return "\n".join(lines)


class LongTermMemory:
    """
    长期用户画像（User级别）

    特点：
    - 跨会话持久化
    - 结构化用户画像
    - 支持复杂查询
    - 增量更新
    """

    def __init__(self, user_id: str, vector_store=None):
        self.user_id = user_id
        self.vector_store = vector_store  # 向量存储，用于语义检索
        self.profile: Dict[str, Any] = self._load_or_create_profile()
        self.memories: List[MemoryEntry] = []

    def _load_or_create_profile(self) -> Dict[str, Any]:
        """加载或创建用户画像"""
        # 实际应从数据库加载
        return {
            "user_id": self.user_id,
            "created_at": datetime.now().isoformat(),
            "demographics": {},
            "preferences": {
                "brands": [],
                "price_range": {},
                "categories": [],
                "features": []
            },
            "behavior_patterns": {
                "purchase_history": [],
                "browsing_patterns": [],
                "decision_factors": []
            },
            "interaction_history": {
                "total_sessions": 0,
                "last_session": None,
                "avg_session_duration": 0
            }
        }

    async def add_memory(self, content: Dict[str, Any], memory_type: MemoryType,
                        priority: MemoryPriority = MemoryPriority.MEDIUM) -> str:
        """添加记忆"""
        entry_id = f"ltm_{self.user_id}_{datetime.now().timestamp()}"
        entry = MemoryEntry(
            id=entry_id,
            type=memory_type,
            content=content,
            timestamp=datetime.now(),
            priority=priority,
            source=self.user_id
        )

        # 存储到向量库（如果可用）
        if self.vector_store:
            vector = entry.to_vector()
            await self.vector_store.add(entry_id, vector, {
                "type": memory_type.value,
                "timestamp": entry.timestamp.isoformat(),
                "content_preview": str(content)[:200]
            })

        self.memories.append(entry)
        return entry_id

    async def search_memories(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """语义搜索记忆"""
        if self.vector_store:
            # 使用向量检索
            results = await self.vector_store.search(query, limit=limit)
            # 过滤类型
            if memory_types:
                results = [r for r in results if r.type in memory_types]
            return results
        else:
            # 退化为时间排序
            filtered = self.memories
            if memory_types:
                filtered = [m for m in filtered if m.type in memory_types]
            return sorted(filtered, key=lambda x: x.timestamp, reverse=True)[:limit]

    def update_profile(self, updates: Dict[str, Any]):
        """更新用户画像"""
        self._deep_update(self.profile, updates)

    def _deep_update(self, base: Dict, updates: Dict):
        """深度更新字典"""
        for key, value in updates.items():
            if isinstance(value, dict) and key in base:
                self._deep_update(base[key], value)
            else:
                base[key] = value

    def get_profile_summary(self) -> str:
        """获取画像摘要"""
        p = self.profile
        lines = [f"用户ID: {self.user_id}"]

        prefs = p.get("preferences", {})
        if prefs.get("brands"):
            lines.append(f"偏好品牌: {', '.join(prefs['brands'])}")
        if prefs.get("categories"):
            lines.append(f"关注类别: {', '.join(prefs['categories'])}")

        behavior = p.get("behavior_patterns", {})
        history = behavior.get("purchase_history", [])
        if history:
            lines.append(f"购买历史: {len(history)}笔")

        return "\n".join(lines)


# 使用示例
async def demo_memory_system():
    """演示记忆系统使用"""

    # 创建短期记忆（会话级别）
    stm = ShortTermMemory(session_id="session_001")

    # 添加记忆条目
    stm.add({
        "topic": "手机推荐",
        "user_need": "3000元左右，拍照好"
    }, priority=MemoryPriority.HIGH)

    # 更新槽位
    stm.update_slot("product_category", "手机")
    stm.update_slot("price_range", {"min": 2500, "max": 3500})

    # 查看工作记忆状态
    print(stm.to_context_string())

    # 创建长期记忆（用户级别）
    ltm = LongTermMemory(user_id="user_123")

    # 添加长期记忆
    await ltm.add_memory({
        "event": "purchase",
        "product": "小米13",
        "price": 3999,
        "satisfaction": 4.5
    }, memory_type=MemoryType.EPISODIC, priority=MemoryPriority.HIGH)

    # 更新用户画像
    ltm.update_profile({
        "preferences": {
            "brands": ["小米", "华为"],
            "price_range": {"min": 2000, "max": 4000}
        }
    })

    # 搜索记忆
    memories = await ltm.search_memories("购买历史")
    for m in memories:
        print(f"找到记忆: {m.content}")

    # 获取画像摘要
    print(ltm.get_profile_summary())


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_memory_system())


## 4. 情感识别和回应策略模块

### 4.1 情感识别架构

```python
# emotion_recognition/emotion_analyzer.py

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re

class EmotionType(Enum):
    """情感类型"""
    HAPPY = "happy"                 # 开心/满意
    EXCITED = "excited"             # 兴奋/期待
    NEUTRAL = "neutral"             # 中性
    CONFUSED = "confused"           # 困惑
    FRUSTRATED = "frustrated"       # 沮丧/挫败
    ANGRY = "angry"                 # 愤怒
    ANXIOUS = "anxious"             # 焦虑
    HESITANT = "hesitant"           # 犹豫
    SATISFIED = "satisfied"         # 满意
    DISAPPOINTED = "disappointed"   # 失望

class UrgencyLevel(Enum):
    """紧急程度"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class EmotionState:
    """情感状态"""
    primary_emotion: EmotionType
    secondary_emotion: Optional[EmotionType]
    confidence: float  # 置信度 0-1
    intensity: float   # 强度 0-1
    urgency: UrgencyLevel
    triggers: List[str]  # 触发关键词
    context: Dict[str, Any]  # 上下文信息

@dataclass
class ResponseStrategy:
    """回应策略"""
    style: str                     # 回应风格
    tone: str                      # 语气
    pace: str                      # 节奏（快速/适中/缓慢）
    approach: str                  # 处理方式
    content_focus: List[str]       # 内容重点
    avoid_topics: List[str]        # 避免话题
    suggested_actions: List[str]   # 建议行动

class EmotionAnalyzer:
    """
    情感分析器

    多维度情感识别，结合规则引擎和LLM
    """

    # 情感关键词词典
    EMOTION_KEYWORDS = {
        EmotionType.HAPPY: ["不错", "很好", "喜欢", "满意", "开心", "棒", "赞", "完美", "太好了"],
        EmotionType.EXCITED: ["期待", "兴奋", "迫不及待", "好想", "超想", "赶紧", "马上"],
        EmotionType.CONFUSED: ["不懂", "不明白", " confused", "困惑", "迷茫", "不清楚", "什么意思"],
        EmotionType.FRUSTRATED: ["烦", "郁闷", "无语", "头疼", "麻烦", "难用", "失望", "不爽"],
        EmotionType.ANGRY: ["生气", "愤怒", "火大", "气愤", "忍无可忍", "投诉", "退钱", "骗子"],
        EmotionType.ANXIOUS: ["着急", "焦虑", "担心", "怕", "赶时间", "急用", "快点"],
        EmotionType.HESITANT: ["犹豫", "纠结", "拿不定", "考虑", "想想", "再看看", "比较"],
        EmotionType.SATISFIED: ["满意", "符合", "正好", "合适", "就它了", "定了", "下单"],
        EmotionType.DISAPPOINTED: ["失望", "不如", "没达到", "不值", "差", "垃圾", "踩坑"]
    }

    # 紧急程度关键词
    URGENCY_KEYWORDS = {
        UrgencyLevel.CRITICAL: ["马上", "立刻", "现在就", "等不了", "救命"],
        UrgencyLevel.HIGH: ["快点", "着急", "赶时间", "急用", "尽快"],
        UrgencyLevel.MEDIUM: ["今天", "这次", "近期"],
        UrgencyLevel.LOW: ["随便", "看看", "以后再说", "不急"]
    }

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self._compile_patterns()

    def _compile_patterns(self):
        """编译正则模式"""
        self.emotion_patterns = {}
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            pattern = "|".join(re.escape(kw) for kw in keywords)
            self.emotion_patterns[emotion] = re.compile(pattern)

    def analyze(self, text: str, context: Optional[Dict] = None) -> EmotionState:
        """
        分析情感状态

        结合规则引擎和LLM进行多维度分析
        """
        # 1. 规则引擎快速分析
        rule_result = self._rule_based_analysis(text)

        # 2. 如果有LLM，进行深度分析
        if self.llm_client:
            llm_result = self._llm_based_analysis(text, context)
            # 融合结果
            return self._merge_results(rule_result, llm_result)

        return rule_result

    def _rule_based_analysis(self, text: str) -> EmotionState:
        """基于规则的情感分析"""
        text_lower = text.lower()

        # 检测情感
        emotion_scores = {}
        triggers = {}

        for emotion, pattern in self.emotion_patterns.items():
            matches = pattern.findall(text_lower)
            if matches:
                emotion_scores[emotion] = len(matches)
                triggers[emotion] = matches

        # 确定主要和次要情感
        if emotion_scores:
            sorted_emotions = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)
            primary_emotion = sorted_emotions[0][0]
            secondary_emotion = sorted_emotions[1][0] if len(sorted_emotions) > 1 else None
            confidence = min(0.5 + sorted_emotions[0][1] * 0.1, 0.95)
        else:
            primary_emotion = EmotionType.NEUTRAL
            secondary_emotion = None
            confidence = 0.5

        # 计算强度
        intensity = self._calculate_intensity(text, emotion_scores)

        # 检测紧急程度
        urgency = self._detect_urgency(text)

        return EmotionState(
            primary_emotion=primary_emotion,
            secondary_emotion=secondary_emotion,
            confidence=confidence,
            intensity=intensity,
            urgency=urgency,
            triggers=[t for ts in triggers.values() for t in ts],
            context={"source": "rule_based"}
        )

    def _calculate_intensity(self, text: str, emotion_scores: Dict[EmotionType, int]) -> float:
        """计算情感强度"""
        # 基于标点、大写、重复词等计算
        intensity = 0.5  # 基础强度

        # 感叹号增加强度
        exclamation_count = text.count('！') + text.count('!')
        intensity += min(exclamation_count * 0.1, 0.2)

        # 重复字符增加强度
        import re
        repeats = len(re.findall(r'(.)\1{2,}', text))
        intensity += min(repeats * 0.1, 0.2)

        # 情感词数量
        if emotion_scores:
            total_emotion_words = sum(emotion_scores.values())
            intensity += min(total_emotion_words * 0.05, 0.2)

        return min(intensity, 1.0)

    def _detect_urgency(self, text: str) -> UrgencyLevel:
        """检测紧急程度"""
        text_lower = text.lower()

        for level, keywords in self.URGENCY_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    return level

        return UrgencyLevel.LOW

    def _llm_based_analysis(self, text: str, context: Optional[Dict]) -> EmotionState:
        """基于LLM的情感分析"""
        prompt = f"""请分析以下用户语句的情感状态。

用户语句："{text}"

请从以下维度进行分析，并以JSON格式输出：
{{
    "primary_emotion": "主要情感（happy/excited/neutral/confused/frustrated/angry/anxious/hesitant/satisfied/disappointed）",
    "secondary_emotion": "次要情感，没有则为null",
    "confidence": 0.85,
    "intensity": 0.7,
    "urgency": "low/medium/high/critical",
    "triggers": ["触发情感的关键词"],
    "reasoning": "分析推理过程"
}}
"""

        try:
            response = self.llm_client.invoke([{"role": "user", "content": prompt}])
            result = json.loads(response)

            emotion_map = {
                "happy": EmotionType.HAPPY,
                "excited": EmotionType.EXCITED,
                "neutral": EmotionType.NEUTRAL,
                "confused": EmotionType.CONFUSED,
                "frustrated": EmotionType.FRUSTRATED,
                "angry": EmotionType.ANGRY,
                "anxious": EmotionType.ANXIOUS,
                "hesitant": EmotionType.HESITANT,
                "satisfied": EmotionType.SATISFIED,
                "disappointed": EmotionType.DISAPPOINTED
            }

            urgency_map = {
                "low": UrgencyLevel.LOW,
                "medium": UrgencyLevel.MEDIUM,
                "high": UrgencyLevel.HIGH,
                "critical": UrgencyLevel.CRITICAL
            }

            return EmotionState(
                primary_emotion=emotion_map.get(result["primary_emotion"], EmotionType.NEUTRAL),
                secondary_emotion=emotion_map.get(result["secondary_emotion"]) if result.get("secondary_emotion") else None,
                confidence=result.get("confidence", 0.7),
                intensity=result.get("intensity", 0.5),
                urgency=urgency_map.get(result.get("urgency", "low"), UrgencyLevel.LOW),
                triggers=result.get("triggers", []),
                context={"source": "llm", "reasoning": result.get("reasoning", "")}
            )

        except Exception as e:
            # 降级到规则分析
            return self._rule_based_analysis(text)

    def _merge_results(self, rule_result: EmotionState, llm_result: EmotionState) -> EmotionState:
        """融合规则分析和LLM分析结果"""
        # 如果LLM置信度更高，优先使用LLM结果
        if llm_result.confidence > rule_result.confidence + 0.2:
            return llm_result

        # 否则融合两者
        # 主要情感：选择置信度更高的
        primary_emotion = llm_result.primary_emotion if llm_result.confidence > rule_result.confidence else rule_result.primary_emotion

        # 融合强度（加权平均）
        rule_weight = rule_result.confidence
        llm_weight = llm_result.confidence
        total_weight = rule_weight + llm_weight

        intensity = (rule_result.intensity * rule_weight + llm_result.intensity * llm_weight) / total_weight
        confidence = max(rule_result.confidence, llm_result.confidence)

        # 合并触发词
        triggers = list(set(rule_result.triggers + llm_result.triggers))

        # 紧急程度取最高
        urgency = max(rule_result.urgency, llm_result.urgency, key=lambda x: x.value)

        return EmotionState(
            primary_emotion=primary_emotion,
            secondary_emotion=llm_result.secondary_emotion or rule_result.secondary_emotion,
            confidence=confidence,
            intensity=intensity,
            urgency=urgency,
            triggers=triggers,
            context={"source": "merged", "rule_confidence": rule_result.confidence, "llm_confidence": llm_result.confidence}
        )


class ResponseStrategyGenerator:
    """
    回应策略生成器

    根据情感状态生成最优回应策略
    """

    # 情感 -> 策略映射
    EMOTION_STRATEGIES = {
        EmotionType.HAPPY: ResponseStrategy(
            style="enthusiastic",
            tone="friendly",
            pace="normal",
            approach="reinforce_positive",
            content_focus=["features", "benefits", "social_proof"],
            avoid_topics=["problems", "limitations"],
            suggested_actions=["show_recommendations", "offer_comparison"]
        ),
        EmotionType.FRUSTRATED: ResponseStrategy(
            style="empathetic",
            tone="calm",
            pace="slow",
            approach="acknowledge_and_redirect",
            content_focus=["solutions", "alternatives", "support"],
            avoid_topics=["pressure", "urgency", "complicated_features"],
            suggested_actions=["offer_help", "simplify_options", "escalate_if_needed"]
        ),
        EmotionType.ANGRY: ResponseStrategy(
            style="empathetic",
            tone="sincere",
            pace="slow",
            approach="acknowledge_apologize_solve",
            content_focus=["immediate_solution", "compensation", "escalation_path"],
            avoid_topics=["excuses", "blame", "delay"],
            suggested_actions=["immediate_acknowledgment", "offer_solution", "escalate_to_human"]
        ),
        EmotionType.CONFUSED: ResponseStrategy(
            style="professional",
            tone="patient",
            pace="slow",
            approach="clarify_simplify_educate",
            content_focus=["explanation", "examples", "comparison"],
            avoid_topics=["jargon", "assumptions", "rushing"],
            suggested_actions=["ask_clarifying_questions", "provide_examples", "offer_step_by_step_guide"]
        ),
        EmotionType.HESITANT: ResponseStrategy(
            style="friendly",
            tone="encouraging",
            pace="normal",
            approach="build_confidence_address_concerns",
            content_focus=["social_proof", "risk_mitigation", "flexibility"],
            avoid_topics=["pressure", "urgency", "complicated_commitments"],
            suggested_actions=["provide_testimonials", "offer_guarantee", "suggest_low_risk_options"]
        ),
        EmotionType.ANXIOUS: ResponseStrategy(
            style="empathetic",
            tone="reassuring",
            pace="calm",
            approach="acknowledge_reassure_provide_certainty",
            content_focus=["timeline", "support_availability", "contingency_plans"],
            avoid_topics=["uncertainty", "delays", "complexity"],
            suggested_actions=["provide_clear_timeline", "offer_direct_contact", "set_expectations"]
        ),
        EmotionType.EXCITED: ResponseStrategy(
            style="enthusiastic",
            tone="energetic",
            pace="fast",
            approach="match_energy_amplify_provide_options",
            content_focus=["premium_features", "exclusivity", "early_access"],
            avoid_topics=["limitations", "delays", "boring_details"],
            suggested_actions=["show_premium_options", "offer_exclusive_deals", "provide_immediate_next_steps"]
        ),
    }

    # 紧急程度调整
    URGENCY_ADJUSTMENTS = {
        UrgencyLevel.CRITICAL: {
            "pace": "fast",
            "tone": "direct",
            "approach_override": "immediate_action_required"
        },
        UrgencyLevel.HIGH: {
            "pace": "fast",
            "tone": "urgent_but_calm"
        }
    }

    def generate_strategy(self, emotion_state: EmotionState) -> ResponseStrategy:
        """生成回应策略"""
        # 获取基础策略
        base_strategy = self.EMOTION_STRATEGIES.get(
            emotion_state.primary_emotion,
            self._default_strategy()
        )

        # 根据紧急程度调整
        if emotion_state.urgency in self.URGENCY_ADJUSTMENTS:
            base_strategy = self._apply_urgency_adjustment(
                base_strategy,
                self.URGENCY_ADJUSTMENTS[emotion_state.urgency]
            )

        # 根据强度微调
        if emotion_state.intensity > 0.8:
            base_strategy = self._intensify_strategy(base_strategy)

        return base_strategy

    def _default_strategy(self) -> ResponseStrategy:
        """默认策略"""
        return ResponseStrategy(
            style="friendly",
            tone="neutral",
            pace="normal",
            approach="standard_assistance",
            content_focus=["features", "benefits"],
            avoid_topics=[],
            suggested_actions=["provide_information", "ask_questions"]
        )

    def _apply_urgency_adjustment(
        self,
        strategy: ResponseStrategy,
        adjustment: Dict[str, str]
    ) -> ResponseStrategy:
        """应用紧急程度调整"""
        # 创建新的策略，应用调整
        new_strategy = ResponseStrategy(
            style=strategy.style,
            tone=adjustment.get("tone", strategy.tone),
            pace=adjustment.get("pace", strategy.pace),
            approach=adjustment.get("approach_override", strategy.approach),
            content_focus=strategy.content_focus,
            avoid_topics=strategy.avoid_topics,
            suggested_actions=strategy.suggested_actions
        )
        return new_strategy

    def _intensify_strategy(self, strategy: ResponseStrategy) -> ResponseStrategy:
        """强化策略（当情感强度高时）"""
        # 根据风格强化
        if strategy.style == "empathetic":
            strategy = ResponseStrategy(
                **{**strategy.__dict__, "tone": "deeply_empathetic"}
            )
        elif strategy.style == "enthusiastic":
            strategy = ResponseStrategy(
                **{**strategy.__dict__, "tone": "highly_enthusiastic"}
            )

        return strategy


# 使用示例
async def demo_emotion_system():
    """演示情感识别系统"""

    # 创建情感分析器
    analyzer = EmotionAnalyzer(llm_client=None)  # 这里可以传入LLM客户端

    # 测试不同情感类型的用户输入
    test_cases = [
        "这款手机太好了，我特别喜欢！",
        "什么破东西，根本不能用，我要退货！",
        "我不太确定选哪个，能帮我分析一下吗？",
        "这个和那个有什么区别？我没看懂",
        "赶紧给我推荐，我赶时间",
        "我再考虑考虑，不急"
    ]

    # 创建策略生成器
    strategy_gen = ResponseStrategyGenerator()

    for text in test_cases:
        print(f"\n用户输入: {text}")

        # 分析情感
        emotion_state = analyzer.analyze(text)

        print(f"主要情感: {emotion_state.primary_emotion.value} "
              f"(置信度: {emotion_state.confidence:.2f})")
        if emotion_state.secondary_emotion:
            print(f"次要情感: {emotion_state.secondary_emotion.value}")
        print(f"强度: {emotion_state.intensity:.2f}, 紧急度: {emotion_state.urgency.name}")
        print(f"触发词: {emotion_state.triggers}")

        # 生成回应策略
        strategy = strategy_gen.generate_strategy(emotion_state)
        print(f"\n建议策略:")
        print(f"  风格: {strategy.style}, 语气: {strategy.tone}, 节奏: {strategy.pace}")
        print(f"  方法: {strategy.approach}")
        print(f"  内容重点: {strategy.content_focus}")
        print(f"  建议行动: {strategy.suggested_actions}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_emotion_system())


## 5. 推荐解释生成系统

### 5.1 架构设计

```python
# explanation_generation/recommendation_explainer.py

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class ExplanationType(Enum):
    """解释类型"""
    ATTRIBUTE_BASED = "attribute_based"         # 基于属性匹配
    PREFERENCE_BASED = "preference_based"       # 基于偏好匹配
    SOCIAL_PROOF = "social_proof"               # 社交证明
    CONTRASTIVE = "contrastive"                 # 对比解释
    STORY_BASED = "story_based"                 # 故事化解释

@dataclass
class ExplanationFragment:
    """解释片段"""
    type: ExplanationType
    content: str
    evidence: List[str]
    confidence: float
    relevance_score: float

@dataclass
class PersonalizedExplanation:
    """个性化解释"""
    user_id: str
    product_id: str
    fragments: List[ExplanationFragment]
    overall_confidence: float
    generated_at: datetime

class RecommendationExplainer:
    """
    推荐解释生成器

    生成个性化、有说服力的推荐解释
    """

    def __init__(self, llm_client, user_profiler):
        self.llm_client = llm_client
        self.user_profiler = user_profiler

    async def generate_explanation(
        self,
        user_id: str,
        product: Dict[str, Any],
        recommendation_context: Dict[str, Any],
        explanation_types: Optional[List[ExplanationType]] = None
    ) -> PersonalizedExplanation:
        """生成个性化解释"""

        # 获取用户画像
        user_profile = await self.user_profiler.get_profile(user_id)

        # 确定解释类型
        if not explanation_types:
            explanation_types = self._select_explanation_types(user_profile, product)

        # 生成各类型解释片段
        fragments = []
        for exp_type in explanation_types:
            fragment = await self._generate_fragment(
                exp_type, user_profile, product, recommendation_context
            )
            if fragment:
                fragments.append(fragment)

        # 排序并选择最相关的片段
        fragments.sort(key=lambda f: f.relevance_score, reverse=True)
        selected_fragments = fragments[:3]  # 最多3个片段

        # 计算整体置信度
        overall_confidence = sum(f.confidence for f in selected_fragments) / len(selected_fragments) if selected_fragments else 0

        return PersonalizedExplanation(
            user_id=user_id,
            product_id=product.get("id", ""),
            fragments=selected_fragments,
            overall_confidence=overall_confidence,
            generated_at=datetime.now()
        )

    def _select_explanation_types(
        self,
        user_profile: Dict[str, Any],
        product: Dict[str, Any]
    ) -> List[ExplanationType]:
        """根据用户画像和商品选择解释类型"""
        types = []

        # 根据用户决策风格选择
        decision_style = user_profile.get("decision_style", "balanced")

        if decision_style == "analytical":
            types = [ExplanationType.ATTRIBUTE_BASED, ExplanationType.CONTRASTIVE]
        elif decision_style == "social":
            types = [ExplanationType.SOCIAL_PROOF, ExplanationType.STORY_BASED]
        elif decision_style == "emotional":
            types = [ExplanationType.STORY_BASED, ExplanationType.PREFERENCE_BASED]
        else:
            types = [ExplanationType.ATTRIBUTE_BASED, ExplanationType.PREFERENCE_BASED]

        # 根据商品特性调整
        if product.get("has_strong_social_proof"):
            if ExplanationType.SOCIAL_PROOF not in types:
                types.append(ExplanationType.SOCIAL_PROOF)

        return types[:3]  # 最多3种

    async def _generate_fragment(
        self,
        exp_type: ExplanationType,
        user_profile: Dict[str, Any],
        product: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[ExplanationFragment]:
        """生成单个解释片段"""

        generators = {
            ExplanationType.ATTRIBUTE_BASED: self._generate_attribute_fragment,
            ExplanationType.PREFERENCE_BASED: self._generate_preference_fragment,
            ExplanationType.SOCIAL_PROOF: self._generate_social_proof_fragment,
            ExplanationType.CONTRASTIVE: self._generate_contrastive_fragment,
            ExplanationType.STORY_BASED: self._generate_story_fragment
        }

        generator = generators.get(exp_type)
        if generator:
            return await generator(user_profile, product, context)

        return None

    async def _generate_attribute_fragment(
        self,
        user_profile: Dict[str, Any],
        product: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ExplanationFragment:
        """生成基于属性的解释片段"""

        # 找出与用户最相关的属性
        user_needs = context.get("user_needs", [])
        product_attributes = product.get("attributes", {})

        matched_attributes = []
        for need in user_needs:
            for attr_name, attr_value in product_attributes.items():
                if need.lower() in attr_name.lower() or need.lower() in str(attr_value).lower():
                    matched_attributes.append((attr_name, attr_value, need))

        if matched_attributes:
            attr_name, attr_value, need = matched_attributes[0]
            content = f"这款{product.get('name')}特别契合您的需求——它的{attr_name}为{attr_value}，正好满足您对{need}的要求。"
        else:
            # 默认展示核心卖点
            key_attr = list(product_attributes.keys())[0] if product_attributes else "配置"
            content = f"这款{product.get('name')}在{key_attr}方面表现出色，是同类产品的佼佼者。"

        return ExplanationFragment(
            type=ExplanationType.ATTRIBUTE_BASED,
            content=content,
            evidence=[f"匹配属性: {attr[0]}" for attr in matched_attributes[:3]],
            confidence=0.8 if matched_attributes else 0.6,
            relevance_score=0.85 if matched_attributes else 0.6
        )

    async def _generate_preference_fragment(
        self,
        user_profile: Dict[str, Any],
        product: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ExplanationFragment:
        """生成基于偏好的解释片段"""

        preferred_brands = user_profile.get("preferences", {}).get("brands", [])
        product_brand = product.get("brand", "")

        if product_brand in preferred_brands:
            content = f"知道您一直偏爱{product_brand}的产品，这款{product.get('name')}延续了品牌一贯的高品质和优秀体验，相信不会让您失望。"
            confidence = 0.9
            relevance = 0.95
        else:
            # 尝试找其他偏好匹配
            preferred_categories = user_profile.get("preferences", {}).get("categories", [])
            product_category = product.get("category", "")

            if product_category in preferred_categories:
                content = f"看到您对{product_category}很感兴趣，这款{product.get('name')}在这个品类中口碑很好，值得您关注。"
                confidence = 0.75
                relevance = 0.8
            else:
                content = f"根据您过往的选择偏好，这款{product.get('name')}的风格和定位与您比较契合。"
                confidence = 0.6
                relevance = 0.5

        return ExplanationFragment(
            type=ExplanationType.PREFERENCE_BASED,
            content=content,
            evidence=[f"偏好品牌: {preferred_brands}", f"产品品牌: {product_brand}"],
            confidence=confidence,
            relevance_score=relevance
        )

    async def _generate_social_proof_fragment(
        self,
        user_profile: Dict[str, Any],
        product: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ExplanationFragment:
        """生成社交证明解释片段"""

        rating = product.get("rating", 0)
        sales = product.get("sales", 0)
        reviews = product.get("reviews", [])

        # 选择最相关的社交证明
        if sales > 100000:
            content = f"这款{product.get('name')}非常受欢迎，已经有超过{sales//10000}万人购买，评分高达{rating}分，是众多用户的选择。"
            confidence = 0.9
        elif rating >= 4.8:
            content = f"这款{product.get('name')}的用户评价非常高，平均评分{rating}分，很多用户都说它超出预期。"
            confidence = 0.85
        elif reviews:
            # 提取一个正面评价
            positive_review = next((r for r in reviews if r.get("rating", 0) >= 4), None)
            if positive_review:
                content = f"不少用户都喜欢这款{product.get('name')}，有用户评价说：\"{positive_review.get('content', '很不错')[:30]}...\""
                confidence = 0.75
            else:
                content = f"这款{product.get('name')}在市场上的口碑不错，值得您考虑。"
                confidence = 0.6
        else:
            content = f"这款{product.get('name')}是我们精选的优质商品。"
            confidence = 0.5

        return ExplanationFragment(
            type=ExplanationType.SOCIAL_PROOF,
            content=content,
            evidence=[f"评分: {rating}", f"销量: {sales}"],
            confidence=confidence,
            relevance_score=confidence
        )

    async def _generate_contrastive_fragment(
        self,
        user_profile: Dict[str, Any],
        product: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ExplanationFragment:
        """生成对比解释片段"""

        # 获取对比商品
        alternatives = context.get("alternatives", [])

        if not alternatives:
            return None

        # 选择最有对比价值的竞品
        alternative = alternatives[0]

        # 找出核心差异点
        this_attrs = product.get("attributes", {})
        alt_attrs = alternative.get("attributes", {})

        differences = []
        for key in set(this_attrs.keys()) & set(alt_attrs.keys()):
            if this_attrs[key] != alt_attrs[key]:
                differences.append((key, this_attrs[key], alt_attrs[key]))

        if differences:
            # 选择最显著的差异
            attr_name, this_val, alt_val = differences[0]
            content = f"相比于{alternative.get('name')}，这款{product.get('name')}在{attr_name}方面更胜一筹（{this_val} vs {alt_val}），如果您更看重这点，它是更好的选择。"
            confidence = 0.8
        else:
            # 基于价格对比
            this_price = product.get("price", 0)
            alt_price = alternative.get("price", 0)
            if this_price < alt_price:
                content = f"这款{product.get('name')}比{alternative.get('name')}便宜¥{alt_price - this_price}，但配置相近，性价比更高。"
            else:
                content = f"虽然这款{product.get('name')}比{alternative.get('name')}贵一些，但它在品质和性能上更有优势。"
            confidence = 0.75

        return ExplanationFragment(
            type=ExplanationType.CONTRASTIVE,
            content=content,
            evidence=[f"对比商品: {alternative.get('name')}"],
            confidence=confidence,
            relevance_score=0.8 if alternatives else 0.4
        )

    async def _generate_story_fragment(
        self,
        user_profile: Dict[str, Any],
        product: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ExplanationFragment:
        """生成故事化解释片段"""

        # 构建用户使用场景故事
        use_case = context.get("use_case", "日常使用")
        product_name = product.get("name", "这款产品")

        # 基于使用场景生成故事
        stories = {
            "游戏": f"想象一下，周末晚上你正准备和朋友们开黑，打开{product_name}，高帧率模式让每一帧画面都丝滑流畅，团战时也不会卡顿，让你轻松carry全场。",
            "办公": f"工作日的早晨，你打开{product_name}开始一天的工作。它快速响应每一个操作，多任务切换流畅自如，让你专注在重要的工作内容上，效率倍增。",
            "拍照": f"周末出游，看到美丽的风景，你拿出{product_name}，轻轻一按，清晰细腻的画面瞬间定格。无论是风景还是人像，都能拍出专业级的效果。",
            "学习": f"晚自习时间，你用{product_name}查阅资料、做笔记。清晰的屏幕显示让长时间阅读也不疲劳，帮助你更专注地投入学习。",
            "日常": f"在日常生活中，{product_name}是你可靠的伙伴。无论是通讯、娱乐还是处理事务，它都能轻松应对，让生活更加便捷。"
        }

        story = stories.get(use_case, stories["日常"])

        return ExplanationFragment(
            type=ExplanationType.STORY_BASED,
            content=story,
            evidence=[f"使用场景: {use_case}"],
            confidence=0.75,
            relevance_score=0.8 if use_case != "日常" else 0.6
        )

    def assemble_explanation(
        self,
        fragments: List[ExplanationFragment],
        user_context: Dict[str, Any],
        max_length: int = 500
    ) -> str:
        """组装最终解释文本"""

        if not fragments:
            return "这是一款不错的商品，值得考虑。"

        # 按相关性排序
        fragments.sort(key=lambda f: f.relevance_score, reverse=True)

        # 选择片段组装
        selected_fragments = []
        current_length = 0

        for fragment in fragments:
            if current_length + len(fragment.content) <= max_length:
                selected_fragments.append(fragment)
                current_length += len(fragment.content)
            else:
                break

        # 组装文本
        parts = []
        for i, fragment in enumerate(selected_fragments):
            if i == 0:
                # 第一段作为开场
                parts.append(fragment.content)
            else:
                # 后续段落添加过渡
                transition = self._select_transition(fragment.type)
                parts.append(transition + fragment.content)

        return "\n\n".join(parts)

    def _select_transition(self, fragment_type: ExplanationType) -> str:
        """选择过渡语"""
        transitions = {
            ExplanationType.ATTRIBUTE_BASED: "从配置来看，",
            ExplanationType.PREFERENCE_BASED: "考虑到您的偏好，",
            ExplanationType.SOCIAL_PROOF: "另外值得一提的是，",
            ExplanationType.CONTRASTIVE: "相比之下，",
            ExplanationType.STORY_BASED: "想象一下，"
        }
        return transitions.get(fragment_type, "此外，")


# 使用示例
async def demo_explanation_generation():
    """演示解释生成"""

    # 创建解释器
    explainer = RecommendationExplainer(llm_client=None, user_profiler=None)

    # 模拟用户画像和商品信息
    user_profile = {
        "preferences": {
            "brands": ["小米", "华为"],
            "price_range": {"min": 2000, "max": 4000}
        }
    }

    product = {
        "id": "p_001",
        "name": "小米13",
        "price": 3999,
        "brand": "小米",
        "rating": 4.7,
        "sales": 50000,
        "attributes": {
            "camera": "徕卡三摄",
            "processor": "骁龙8 Gen2",
            "screen": "6.36英寸 OLED"
        }
    }

    context = {
        "user_needs": ["拍照", "性能"],
        "use_case": "拍照",
        "alternatives": [
            {"name": "华为nova 11", "price": 2799}
        ]
    }

    # 生成各类解释片段
    fragments = []

    # 属性匹配解释
    attr_fragment = await explainer._generate_attribute_fragment(
        user_profile, product, context
    )
    if attr_fragment:
        fragments.append(attr_fragment)

    # 偏好匹配解释
    pref_fragment = await explainer._generate_preference_fragment(
        user_profile, product, context
    )
    if pref_fragment:
        fragments.append(pref_fragment)

    # 社交证明解释
    social_fragment = await explainer._generate_social_proof_fragment(
        user_profile, product, context
    )
    if social_fragment:
        fragments.append(social_fragment)

    # 对比解释
    contrast_fragment = await explainer._generate_contrastive_fragment(
        user_profile, product, context
    )
    if contrast_fragment:
        fragments.append(contrast_fragment)

    # 故事化解释
    story_fragment = await explainer._generate_story_fragment(
        user_profile, product, context
    )
    if story_fragment:
        fragments.append(story_fragment)

    # 组装最终解释
    final_explanation = explainer.assemble_explanation(
        fragments,
        {"user_profile": user_profile},
        max_length=600
    )

    print("=== 生成的推荐解释 ===")
    print(final_explanation)

    print("\n=== 各片段详情 ===")
    for i, frag in enumerate(fragments, 1):
        print(f"\n片段{i}: {frag.type.value}")
        print(f"  内容: {frag.content[:100]}...")
        print(f"  置信度: {frag.confidence:.2f}")
        print(f"  相关度: {frag.relevance_score:.2f}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_explanation_generation())
