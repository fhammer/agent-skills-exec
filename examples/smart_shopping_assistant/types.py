"""
类型定义 - Type Definitions

智能购物助手的核心类型定义。
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Any


@dataclass
class SemanticUnderstandingResult:
    """语义理解结果类型（在 shopping assistant 中使用）"""
    intent: str
    entities: dict
    confidence: float
    metadata: dict = field(default_factory=dict)

    def is_clear(self) -> bool:
        return self.confidence > 0.7

    def get_execution_plan_input(self) -> dict:
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "parameters": self.entities
        }


@dataclass
class IntentClassification:
    """Intent classification result"""
    intent: str
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    alternatives: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class IntentClassification:
    """意图分类结果"""
    intent: str
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    alternatives: List[Dict[str, Any]] = field(default_factory=list)


class IntentType(Enum):
    """意图类型"""
    SEARCH = "search"           # 搜索商品
    PRODUCT_SEARCH = "product_search"  # 搜索产品
    RECOMMEND = "recommend"     # 请求推荐
    COMPARE = "compare"         # 对比商品
    INQUIRE = "inquire"         # 咨询详情
    FILTER = "filter"           # 筛选条件
    CLARIFY = "clarify"         # 需要澄清
    PURCHASE = "purchase"       # 购买意向
    CHAT = "chat"               # 闲聊


class Sentiment(Enum):
    """情感类型"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class UrgencyLevel(Enum):
    """紧急程度"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ResponseTone(Enum):
    """响应语气"""
    ENTHUSIASTIC = "enthusiastic"  # 热情
    EMPATHETIC = "empathetic"      # 共情
    CALM = "calm"                  # 平静
    PROFESSIONAL = "professional" # 专业
    FRIENDLY = "friendly"         # 友好
    NEUTRAL = "neutral"           # 中性


@dataclass
class ParsedIntent:
    """解析后的意图"""
    intent: IntentType
    entities: Dict[str, Any]
    ambiguities: List[str]
    urgency: UrgencyLevel
    raw_input: str
    confidence: float = 0.8


@dataclass
class SentimentResult:
    """情感分析结果"""
    label: Sentiment
    confidence: float
    urgency: UrgencyLevel
    key_emotions: List[str]
    frustration_indicators: List[str]
    recommended_tone: ResponseTone


@dataclass
class SearchCriteria:
    """搜索条件"""
    keywords: Optional[str] = None
    category: Optional[str] = None
    brands: List[str] = field(default_factory=list)
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    required_features: List[str] = field(default_factory=list)
    min_rating: Optional[float] = None
    color: Optional[str] = None


@dataclass
class Product:
    """商品数据类"""
    id: str
    name: str
    brand: str
    category: str
    price: float
    original_price: Optional[float] = None
    colors: List[str] = field(default_factory=list)
    specs: Dict[str, Any] = field(default_factory=dict)
    features: List[str] = field(default_factory=list)
    rating: float = 4.5
    review_count: int = 0
    stock: int = 100
    images: List[str] = field(default_factory=list)
    description: str = ""

    def get_discount(self) -> Optional[float]:
        """获取折扣率"""
        if self.original_price and self.original_price > self.price:
            return round((1 - self.price / self.original_price) * 100, 1)
        return None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "brand": self.brand,
            "category": self.category,
            "price": self.price,
            "original_price": self.original_price,
            "colors": self.colors,
            "rating": self.rating,
            "review_count": self.review_count,
            "features": self.features,
        }


@dataclass
class UserPreference:
    """用户偏好"""
    favorite_categories: List[str] = field(default_factory=list)
    preferred_brands: List[str] = field(default_factory=list)
    typical_price_range: Optional[tuple] = None
    preferred_features: List[str] = field(default_factory=list)
    color_preferences: List[str] = field(default_factory=list)


@dataclass
class UserProfile:
    """用户画像"""
    user_id: str
    preferences: UserPreference = field(default_factory=UserPreference)
    browse_history: List[str] = field(default_factory=list)
    purchase_history: List[str] = field(default_factory=list)
    interaction_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)


@dataclass
class ConversationTurn:
    """对话轮次"""
    user_input: str
    assistant_response: str
    timestamp: datetime = field(default_factory=datetime.now)
    intent: Optional[IntentType] = None
    products_shown: List[str] = field(default_factory=list)


@dataclass
class ConversationSession:
    """对话会话"""
    session_id: str
    user_id: Optional[str] = None
    turns: List[ConversationTurn] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)

    def add_turn(self, user_input: str, assistant_response: str, **kwargs):
        """添加对话轮次"""
        turn = ConversationTurn(
            user_input=user_input,
            assistant_response=assistant_response,
            **kwargs
        )
        self.turns.append(turn)
        self.last_active = datetime.now()

    def get_recent_turns(self, n: int = 5) -> List[ConversationTurn]:
        """获取最近的对话轮次"""
        return self.turns[-n:] if len(self.turns) > n else self.turns


@dataclass
class SuggestedAction:
    """建议操作"""
    action_id: str
    label: str
    description: str
    handler: Optional[Callable] = None


@dataclass
class AssistantResponse:
    """助手响应"""
    text: str
    products: List[Product] = field(default_factory=list)
    suggested_actions: List[SuggestedAction] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.8


# 导出所有类型
__all__ = [
    "IntentType",
    "Sentiment",
    "UrgencyLevel",
    "ResponseTone",
    "ParsedIntent",
    "SentimentResult",
    "SearchCriteria",
    "Product",
    "UserPreference",
    "UserProfile",
    "ConversationTurn",
    "ConversationSession",
    "SuggestedAction",
    "AssistantResponse",
]
