"""
推荐引擎 - Recommendation Engine

提供个性化商品推荐、智能排序和推荐理由生成。
"""

import random
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from .types import Product, UserProfile, SearchCriteria, SearchResult
from .product_database import ProductDatabase


@dataclass
class Recommendation:
    """推荐结果"""
    product: Product
    score: float
    reasons: List[str] = field(default_factory=list)
    match_attributes: Dict[str, Any] = field(default_factory=dict)


class RecommendationEngine:
    """推荐引擎"""

    def __init__(self, product_db: Optional[ProductDatabase] = None):
        """
        初始化推荐引擎

        Args:
            product_db: 商品数据库，默认使用演示数据
        """
        self.product_db = product_db or ProductDatabase()

        # 推荐权重配置
        self.weights = {
            "user_preference_match": 0.25,
            "price_range_match": 0.20,
            "brand_preference_match": 0.15,
            "category_match": 0.15,
            "feature_match": 0.15,
            "popularity": 0.05,
            "rating": 0.05,
        }

    def recommend(
        self,
        user_profile: Optional[UserProfile] = None,
        criteria: Optional[SearchCriteria] = None,
        context: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Recommendation]:
        """
        生成个性化推荐

        Args:
            user_profile: 用户画像
            criteria: 搜索条件
            context: 上下文信息
            limit: 返回数量限制

        Returns:
            推荐结果列表
        """
        # 1. 获取候选商品
        if criteria:
            search_results = self.product_db.search(criteria, limit=50)
            candidates = [r.product for r in search_results]
        else:
            candidates = self.product_db.products[:50]

        # 2. 计算每个商品的推荐分数
        recommendations = []
        for product in candidates:
            score, reasons, attributes = self._calculate_recommendation_score(
                product, user_profile, criteria, context
            )
            recommendations.append(Recommendation(
                product=product,
                score=score,
                reasons=reasons,
                match_attributes=attributes
            ))

        # 3. 排序并限制数量
        recommendations.sort(key=lambda r: r.score, reverse=True)
        return recommendations[:limit]

    def _calculate_recommendation_score(
        self,
        product: Product,
        user_profile: Optional[UserProfile],
        criteria: Optional[SearchCriteria],
        context: Optional[Dict[str, Any]]
    ) -> Tuple[float, List[str], Dict[str, Any]]:
        """
        计算推荐分数

        Returns:
            (分数, 推荐理由, 匹配属性)
        """
        score = 0.0
        reasons = []
        attributes = {}

        # 1. 用户偏好匹配
        if user_profile:
            pref_score = self._calculate_preference_match(product, user_profile)
            score += pref_score * self.weights["user_preference_match"]
            if pref_score > 0.7:
                reasons.append("符合您的偏好")
                attributes["preference_match"] = True

        # 2. 价格范围匹配
        if criteria and (criteria.min_price or criteria.max_price):
            price_score = self._calculate_price_match(product, criteria)
            score += price_score * self.weights["price_range_match"]
            if price_score > 0.8:
                reasons.append("价格符合您的预算")
                attributes["price_match"] = True

        # 3. 品牌偏好匹配
        if user_profile:
            brand_score = self._calculate_brand_match(product, user_profile)
            score += brand_score * self.weights["brand_preference_match"]
            if brand_score > 0.8:
                reasons.append(f"您偏好的{product.brand}品牌")
                attributes["brand_match"] = True

        # 4. 类别匹配
        if criteria and criteria.category:
            if criteria.category in product.category:
                score += self.weights["category_match"]
                reasons.append(f"属于您需要的{product.category}")
                attributes["category_match"] = True

        # 5. 特性匹配
        if criteria and criteria.features:
            feature_score = self._calculate_feature_match(product, criteria.features)
            score += feature_score * self.weights["feature_match"]
            if feature_score > 0.5:
                reasons.append("具备您需要的功能特性")
                attributes["feature_match"] = True

        # 6. 流行度加分
        popularity_score = min(product.review_count / 10000, 1.0) * 0.5
        popularity_score += (product.rating - 3.0) / 2.0 * 0.5
        score += popularity_score * self.weights["popularity"]
        if product.review_count > 5000 and product.rating >= 4.5:
            reasons.append("深受用户喜爱的高分商品")
            attributes["popular"] = True

        # 7. 评分加分
        rating_score = (product.rating - 3.0) / 2.0  # 3.0-5.0 映射到 0-1
        score += rating_score * self.weights["rating"]

        # 8. 促销商品额外加分
        if product.original_price and product.original_price > product.price:
            discount = product.get_discount() or 0
            if discount >= 20:
                score += 0.15
                reasons.append(f"限时优惠{discount}%")
                attributes["on_sale"] = True
            else:
                score += 0.05

        return min(score, 1.0), reasons, attributes

    def _calculate_preference_match(self, product: Product, user_profile: UserProfile) -> float:
        """计算与用户偏好的匹配度"""
        score = 0.0

        # 检查类别偏好
        fav_categories = user_profile.preferences.get("favorite_categories", {}).get("value", [])
        if isinstance(fav_categories, list):
            if product.category in fav_categories:
                score += 0.4

        # 检查价格范围偏好
        price_range = user_profile.preferences.get("price_range", {}).get("value")
        if isinstance(price_range, (list, tuple)) and len(price_range) == 2:
            min_price, max_price = price_range
            if min_price <= product.price <= max_price:
                score += 0.3
            elif abs(product.price - max_price) < 500:  # 接近上限
                score += 0.15

        # 检查浏览历史中的相似商品
        browse_history = user_profile.browse_history[-10:]  # 最近10个
        for product_id in browse_history:
            browsed_product = self.product_db.get_by_id(product_id)
            if browsed_product:
                if browsed_product.category == product.category:
                    score += 0.1
                if browsed_product.brand == product.brand:
                    score += 0.1
                break

        return min(score, 1.0)

    def _calculate_price_match(self, product: Product, criteria: SearchCriteria) -> float:
        """计算价格匹配度"""
        if not criteria.min_price and not criteria.max_price:
            return 0.5  # 默认中等分数

        min_price = criteria.min_price or 0
        max_price = criteria.max_price or float('inf')

        if min_price <= product.price <= max_price:
            # 在范围内，计算居中程度
            range_center = (min_price + max_price) / 2
            distance = abs(product.price - range_center)
            range_size = max_price - min_price
            if range_size > 0:
                return 1.0 - (distance / range_size) * 0.3
            return 1.0
        else:
            # 超出范围
            if product.price < min_price:
                distance = min_price - product.price
                return max(0, 0.7 - distance / min_price * 0.5) if min_price > 0 else 0
            else:
                distance = product.price - max_price
                return max(0, 0.7 - distance / max_price * 0.5) if max_price > 0 else 0

    def _calculate_brand_match(self, product: Product, user_profile: UserProfile) -> float:
        """计算品牌匹配度"""
        preferred_brands = user_profile.preferences.get("preferred_brands", {}).get("value", [])

        if not isinstance(preferred_brands, list):
            return 0.0

        if product.brand in preferred_brands:
            return 1.0

        # 检查购买历史中的品牌
        purchase_history = user_profile.purchase_history[-5:]
        for product_id in purchase_history:
            purchased_product = self.product_db.get_by_id(product_id)
            if purchased_product and purchased_product.brand == product.brand:
                return 0.8

        return 0.0

    def _calculate_feature_match(self, product: Product, features: List[str]) -> float:
        """计算特性匹配度"""
        if not features:
            return 0.0

        matched_count = 0
        product_features_text = " ".join(product.features).lower()

        for feature in features:
            feature_lower = feature.lower()
            # 检查是否匹配产品特性
            if feature_lower in product_features_text:
                matched_count += 1
            # 检查是否在规格中
            for spec_key, spec_value in product.specs.items():
                if feature_lower in str(spec_key).lower() or feature_lower in str(spec_value).lower():
                    matched_count += 1
                    break

        return matched_count / len(features)
