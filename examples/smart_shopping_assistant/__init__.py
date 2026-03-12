"""
智能电商购物助手 - Smart Shopping Assistant

一个具备自然语言理解、多轮对话、个性化推荐能力的智能购物助手。
"""

from .assistant import ShoppingAssistant, AssistantConfig
from .conversation_manager import ConversationManager
from .user_profile_manager import UserProfileManager
from .recommendation_engine import RecommendationEngine, Recommendation
from .nlp_understanding import NLPUnderstanding
from .sentiment_analyzer import SentimentAnalyzer
from .product_database import ProductDatabase
from .demo_data import get_demo_products
from .types import (
    IntentType, Sentiment, UrgencyLevel, ResponseTone,
    Product, SearchCriteria, AssistantResponse,
    UserProfile, ConversationSession
)

__all__ = [
    # 主要类
    "ShoppingAssistant",
    "AssistantConfig",
    # 管理器
    "ConversationManager",
    "UserProfileManager",
    "ProductDatabase",
    # 引擎
    "RecommendationEngine",
    "Recommendation",
    # 理解模块
    "NLPUnderstanding",
    "SentimentAnalyzer",
    # 数据
    "get_demo_products",
    # 类型
    "IntentType",
    "Sentiment",
    "UrgencyLevel",
    "ResponseTone",
    "Product",
    "SearchCriteria",
    "AssistantResponse",
    "UserProfile",
    "ConversationSession",
]

__version__ = "1.0.0"
