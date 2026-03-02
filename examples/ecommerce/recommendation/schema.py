"""
智能导购 Agent - 数据模型定义

定义需求分析、用户画像、商品搜索、推荐排序等数据模型。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class IntentType(Enum):
    """意图类型"""
    PRODUCT_INQUIRY = "product_inquiry"  # 商品咨询
    PRICE_INQUIRY = "price_inquiry"  # 价格咨询
    COMPARISON = "comparison"  # 商品对比
    RECOMMENDATION = "recommendation"  # 推荐
    CLARIFICATION = "clarification"  # 澄清需求


@dataclass
class PriceRange:
    """价格范围"""
    min: Optional[int] = None
    max: Optional[int] = None

    def is_valid(self) -> bool:
        """是否有效"""
        return self.min is not None or self.max is not None

    def contains(self, price: int) -> bool:
        """是否包含指定价格"""
        if self.min is not None and price < self.min:
            return False
        if self.max is not None and price > self.max:
            return False
        return True


@dataclass
class DemandConstraints:
    """需求约束"""
    category: Optional[str] = None  # 商品类别
    price_range: Optional[PriceRange] = None  # 价格范围
    brands: List[str] = field(default_factory=list)  # 品牌偏好
    use_case: Optional[str] = None  # 使用场景 (gaming, office, photography等)
    priority_features: List[str] = field(default_factory=list)  # 优先关注的特性
    exclude_brands: List[str] = field(default_factory=list)  # 排除的品牌

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "category": self.category,
            "price_range": {
                "min": self.price_range.min if self.price_range else None,
                "max": self.price_range.max if self.price_range else None,
            } if self.price_range else None,
            "brands": self.brands,
            "use_case": self.use_case,
            "priority_features": self.priority_features,
            "exclude_brands": self.exclude_brands,
        }


@dataclass
class DemandAnalysisResult:
    """需求分析结果"""
    intent: IntentType
    constraints: DemandConstraints
    missing_info: List[str] = field(default_factory=list)
    confidence: float = 0.0
    raw_text: str = ""

    def is_complete(self) -> bool:
        """信息是否完整"""
        return (
            self.constraints.category is not None
            and len(self.missing_info) == 0
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "intent": self.intent.value,
            "constraints": self.constraints.to_dict(),
            "missing_info": self.missing_info,
            "confidence": self.confidence,
            "raw_text": self.raw_text,
        }


@dataclass
class UserProfile:
    """用户画像"""
    user_id: str
    preferred_brands: List[str] = field(default_factory=list)
    price_preference: str = "中端"  # 低端、中端、高端
    recent_views: List[str] = field(default_factory=list)
    purchase_history: List[Dict[str, Any]] = field(default_factory=list)
    browse_categories: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "preferred_brands": self.preferred_brands,
            "price_preference": self.price_preference,
            "recent_views": self.recent_views,
            "purchase_history": self.purchase_history,
            "browse_categories": self.browse_categories,
        }


@dataclass
class RecommendationHints:
    """推荐提示"""
    focus_on: List[str] = field(default_factory=list)
    avoid: List[str] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "focus_on": self.focus_on,
            "avoid": self.avoid,
            "explanation": self.explanation,
        }


@dataclass
class UserProfilingResult:
    """用户画像结果"""
    user_id: str
    profile: UserProfile
    recommendation_hints: RecommendationHints
    text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "profile": self.profile.to_dict(),
            "recommendation_hints": self.recommendation_hints.to_dict(),
            "text": self.text,
        }


@dataclass
class Product:
    """商品"""
    product_id: str
    name: str
    brand: str
    price: float
    category: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    rating: float = 5.0
    sales: int = 0
    stock: int = 0
    image_url: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "brand": self.brand,
            "price": self.price,
            "category": self.category,
            "attributes": self.attributes,
            "rating": self.rating,
            "sales": self.sales,
            "stock": self.stock,
            "image_url": self.image_url,
        }


@dataclass
class ProductSearchResult:
    """商品搜索结果"""
    total_found: int
    returned: int
    products: List[Product]
    text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_found": self.total_found,
            "returned": self.returned,
            "products": [p.to_dict() for p in self.products],
            "text": self.text,
        }


@dataclass
class MatchFactors:
    """匹配因素"""
    price_match: float = 0.0  # 价格匹配度
    brand_preference: float = 0.0  # 品牌偏好匹配度
    performance: float = 0.0  # 性能匹配度
    user_history: float = 0.0  # 用户历史匹配度

    def overall_score(self) -> float:
        """综合得分"""
        return (
            self.price_match * 0.3 +
            self.brand_preference * 0.25 +
            self.performance * 0.25 +
            self.user_history * 0.2
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "price_match": self.price_match,
            "brand_preference": self.brand_preference,
            "performance": self.performance,
            "user_history": self.user_history,
            "overall_score": self.overall_score(),
        }


@dataclass
class RankedProduct:
    """排序后的商品"""
    rank: int
    product_id: str
    score: float
    match_factors: MatchFactors
    recommendation_reasons: List[str] = field(default_factory=list)
    product: Optional[Product] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rank": self.rank,
            "product_id": self.product_id,
            "score": self.score,
            "match_factors": self.match_factors.to_dict(),
            "recommendation_reasons": self.recommendation_reasons,
            "product": self.product.to_dict() if self.product else None,
        }


@dataclass
class RecommendationRankingResult:
    """推荐排序结果"""
    ranked_products: List[RankedProduct]
    excluded_products: List[Dict[str, Any]] = field(default_factory=list)
    text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "ranked_products": [rp.to_dict() for rp in self.ranked_products],
            "excluded_products": self.excluded_products,
            "text": self.text,
        }


@dataclass
class RecommendationExplanation:
    """推荐说明"""
    response_type: str = "recommendation"
    products_count: int = 0
    highlighted_features: List[str] = field(default_factory=list)
    text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "response_type": self.response_type,
            "products_count": self.products_count,
            "highlighted_features": self.highlighted_features,
            "text": self.text,
        }
