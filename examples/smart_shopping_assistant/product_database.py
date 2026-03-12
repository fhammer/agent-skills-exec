"""
商品数据库 - Product Database

管理商品数据的检索、筛选和排序。
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from .types import Product, SearchCriteria
from .demo_data import get_demo_products


@dataclass
class SearchResult:
    """搜索结果"""
    product: Product
    relevance_score: float
    match_reasons: List[str] = field(default_factory=list)


class ProductDatabase:
    """商品数据库"""

    def __init__(self, products: Optional[List[Product]] = None):
        """
        初始化商品数据库

        Args:
            products: 商品列表，默认为演示数据
        """
        self.products = products if products else get_demo_products()
        self._build_index()

    def _build_index(self):
        """构建商品索引"""
        self.category_index: Dict[str, List[Product]] = {}
        self.brand_index: Dict[str, List[Product]] = {}
        self.feature_index: Dict[str, List[Product]] = {}

        for product in self.products:
            # 按类别索引
            category = product.category
            if category not in self.category_index:
                self.category_index[category] = []
            self.category_index[category].append(product)

            # 按品牌索引
            brand = product.brand
            if brand not in self.brand_index:
                self.brand_index[brand] = []
            self.brand_index[brand].append(product)

            # 按特性索引
            for feature in product.features:
                if feature not in self.feature_index:
                    self.feature_index[feature] = []
                self.feature_index[feature].append(product)

    def search(self, criteria: SearchCriteria, limit: int = 20) -> List[SearchResult]:
        """
        搜索商品

        Args:
            criteria: 搜索条件
            limit: 返回结果数量限制

        Returns:
            搜索结果列表
        """
        candidates = self.products.copy()

        # 按类别筛选
        if criteria.category:
            candidates = [p for p in candidates if criteria.category in p.category]

        # 按品牌筛选
        if criteria.brands:
            candidates = [p for p in candidates if p.brand in criteria.brands]

        # 按价格范围筛选
        if criteria.min_price is not None:
            candidates = [p for p in candidates if p.price >= criteria.min_price]
        if criteria.max_price is not None:
            candidates = [p for p in candidates if p.price <= criteria.max_price]

        # 按评分筛选
        if criteria.min_rating is not None:
            candidates = [p for p in candidates if p.rating >= criteria.min_rating]

        # 计算相关性分数
        results = []
        for product in candidates:
            score, reasons = self._calculate_relevance(product, criteria)
            results.append(SearchResult(
                product=product,
                relevance_score=score,
                match_reasons=reasons
            ))

        # 排序并限制结果数量
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:limit]

    def _calculate_relevance(self, product: Product, criteria: SearchCriteria) -> tuple:
        """
        计算商品与搜索条件的相关性分数

        Returns:
            (分数, 匹配原因列表)
        """
        score = 0.0
        reasons = []

        # 关键词匹配
        if criteria.keywords:
            keyword_score = self._match_keywords(product, criteria.keywords)
            score += keyword_score * 30
            if keyword_score > 0:
                reasons.append(f"匹配关键词 '{criteria.keywords}'")

        # 类别匹配
        if criteria.category and criteria.category in product.category:
            score += 25
            reasons.append(f"类别匹配: {product.category}")

        # 品牌匹配
        if criteria.brands and product.brand in criteria.brands:
            score += 15
            reasons.append(f"品牌匹配: {product.brand}")

        # 价格匹配度（越接近目标越好）
        if criteria.min_price is not None and criteria.max_price is not None:
            target_price = (criteria.min_price + criteria.max_price) / 2
            price_diff = abs(product.price - target_price)
            price_score = max(0, 20 - price_diff / 100)
            score += price_score
            if price_score > 10:
                reasons.append(f"价格适中: ¥{product.price}")

        # 评分加分
        if product.rating >= 4.5:
            score += 10
            reasons.append(f"高评分: {product.rating}")
        elif product.rating >= 4.0:
            score += 5

        # 促销商品加分
        if product.original_price and product.original_price > product.price:
            discount = product.get_discount()
            if discount and discount >= 10:
                score += 8
                reasons.append(f"优惠{discount}%")

        return score, reasons

    def _match_keywords(self, product: Product, keywords: str) -> float:
        """匹配关键词并返回匹配分数"""
        keywords_lower = keywords.lower()
        score = 0.0

        # 名称匹配（权重最高）
        if keywords_lower in product.name.lower():
            score += 1.0

        # 品牌匹配
        if keywords_lower in product.brand.lower():
            score += 0.8

        # 描述匹配
        if product.description and keywords_lower in product.description.lower():
            score += 0.6

        # 特性匹配
        for feature in product.features:
            if keywords_lower in feature.lower():
                score += 0.5
                break

        return min(score, 1.0)

    def get_by_id(self, product_id: str) -> Optional[Product]:
        """通过ID获取商品"""
        for product in self.products:
            if product.id == product_id:
                return product
        return None

    def get_by_name(self, name: str, fuzzy: bool = True) -> Optional[Product]:
        """通过名称获取商品"""
        name_lower = name.lower()

        for product in self.products:
            if name_lower in product.name.lower():
                return product

        if fuzzy:
            # 模糊匹配
            best_match = None
            best_score = 0.0
            for product in self.products:
                score = SequenceMatcher(None, name_lower, product.name.lower()).ratio()
                if score > best_score and score > 0.6:
                    best_score = score
                    best_match = product
            return best_match

        return None

    def get_by_category(self, category: str) -> List[Product]:
        """通过类别获取商品"""
        return [p for p in self.products if category in p.category]

    def get_by_brand(self, brand: str) -> List[Product]:
        """通过品牌获取商品"""
        return [p for p in self.products if brand in p.brand]

    def get_similar_products(self, product: Product, limit: int = 5) -> List[Product]:
        """获取相似商品"""
        candidates = [p for p in self.products if p.id != product.id]

        # 优先推荐同类别商品
        candidates.sort(key=lambda p: (
            p.category == product.category,
            p.brand == product.brand,
            abs(p.price - product.price) < 500
        ), reverse=True)

        return candidates[:limit]

    def get_popular_products(self, limit: int = 10) -> List[Product]:
        """获取热门商品（按评分和评论数排序）"""
        sorted_products = sorted(
            self.products,
            key=lambda p: (p.rating * 0.7 + min(p.review_count / 1000, 5) * 0.3),
            reverse=True
        )
        return sorted_products[:limit]

    def get_products_on_sale(self, limit: int = 10) -> List[Product]:
        """获取促销商品"""
        sale_products = [p for p in self.products if p.original_price and p.original_price > p.price]
        sale_products.sort(key=lambda p: p.get_discount() or 0, reverse=True)
        return sale_products[:limit]

    def get_price_range(self, category: Optional[str] = None) -> Tuple[float, float]:
        """获取价格范围"""
        products = self.get_by_category(category) if category else self.products
        if not products:
            return (0, 0)
        prices = [p.price for p in products]
        return (min(prices), max(prices))

    def get_all_categories(self) -> List[str]:
        """获取所有类别"""
        categories = set()
        for product in self.products:
            categories.add(product.category)
        return sorted(list(categories))

    def get_all_brands(self) -> List[str]:
        """获取所有品牌"""
        brands = set()
        for product in self.products:
            brands.add(product.brand)
        return sorted(list(brands))
