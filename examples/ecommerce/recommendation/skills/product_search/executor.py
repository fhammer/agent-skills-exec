"""商品搜索 Skill 执行器

根据需求约束条件搜索商品数据库
"""

from typing import Dict, Any, List, Optional

# LLMBase 类型提示（实际不依赖具体实现）
try:
    from agent.llm_base import LLMProvider as LLMBase
except ImportError:
    LLMBase = Any


# 模拟商品数据库（实际应从数据库查询）
MOCK_PRODUCTS = [
    {
        "product_id": "p_001",
        "name": "Redmi K70",
        "brand": "小米",
        "price": 2499,
        "category": "手机",
        "attributes": {
            "screen": "6.67英寸 2K 120Hz",
            "processor": "骁龙8 Gen2",
            "battery": "5000mAh",
            "charging": "120W快充",
            "camera": "5000万像素主摄"
        },
        "use_cases": ["游戏", "拍照", "日常"],
        "rating": 4.7,
        "sales": 50000,
        "stock": 1000
    },
    {
        "product_id": "p_002",
        "name": "iQOO Neo9",
        "brand": "iQOO",
        "price": 2299,
        "category": "手机",
        "attributes": {
            "screen": "6.78英寸 144Hz",
            "processor": "骁龙8 Gen2",
            "battery": "5160mAh",
            "charging": "120W快充",
            "camera": "5000万像素主摄"
        },
        "use_cases": ["游戏", "日常"],
        "rating": 4.6,
        "sales": 35000,
        "stock": 800
    },
    {
        "product_id": "p_003",
        "name": "一加 Ace 3",
        "brand": "一加",
        "price": 2599,
        "category": "手机",
        "attributes": {
            "screen": "6.78英寸 120Hz",
            "processor": "骁龙8 Gen2",
            "battery": "5500mAh",
            "charging": "100W快充",
            "camera": "5000万像素主摄"
        },
        "use_cases": ["游戏", "办公", "日常"],
        "rating": 4.8,
        "sales": 28000,
        "stock": 600
    },
    {
        "product_id": "p_004",
        "name": "荣耀90 GT",
        "brand": "荣耀",
        "price": 2399,
        "category": "手机",
        "attributes": {
            "screen": "6.7英寸 120Hz 护眼屏",
            "processor": "骁龙8 Gen2",
            "battery": "5000mAh",
            "charging": "100W快充",
            "camera": "5000万像素主摄"
        },
        "use_cases": ["游戏", "日常"],
        "rating": 4.5,
        "sales": 22000,
        "stock": 500
    },
    {
        "product_id": "p_005",
        "name": "真我 GT5",
        "brand": "真我",
        "price": 2699,
        "category": "手机",
        "attributes": {
            "screen": "6.74英寸 144Hz",
            "processor": "骁龙8 Gen2",
            "battery": "5240mAh",
            "charging": "150W快充",
            "camera": "5000万像素主摄"
        },
        "use_cases": ["游戏", "拍照"],
        "rating": 4.6,
        "sales": 18000,
        "stock": 400
    },
]


def execute(llm: LLMBase, sub_task: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """执行商品搜索"""

    # 获取约束条件
    constraints = context.get("constraints", {})
    category = context.get("category", "手机")
    limit = context.get("limit", 20)

    # 执行搜索
    matched_products = _search_products(
        category=category,
        price_range=constraints.get("price_range"),
        brands=constraints.get("brands", []),
        use_case=constraints.get("use_case"),
        special_requirements=constraints.get("special_requirements", [])
    )

    # 限制返回数量
    returned_products = matched_products[:limit]

    # 构建输出
    structured = {
        "total_found": len(matched_products),
        "returned": len(returned_products),
        "products": returned_products
    }

    text = f"找到{len(matched_products)}款符合条件的{category}，为您推荐前{len(returned_products)}款。"

    return {
        "structured": structured,
        "text": text
    }


def _search_products(
    category: str,
    price_range: Optional[Dict] = None,
    brands: Optional[List[str]] = None,
    use_case: Optional[str] = None,
    special_requirements: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """搜索商品"""

    matched = []

    for product in MOCK_PRODUCTS:
        # 类别过滤
        if product["category"] != category:
            continue

        # 价格过滤
        if price_range:
            min_price = price_range.get("min", 0)
            max_price = price_range.get("max", 99999)
            if not (min_price <= product["price"] <= max_price):
                continue

        # 品牌过滤
        if brands and product["brand"] not in brands:
            # 如果没有指定品牌，或者商品品牌不在列表中，跳过
            # 但如果用户没指定品牌，就不过滤
            if brands:  # 只在用户明确指定品牌时才过滤
                continue

        # 使用场景过滤（优先级排序用，不作为过滤条件）

        matched.append(product)

    # 按相关度排序
    matched = _sort_by_relevance(
        matched,
        use_case=use_case,
        brands=brands,
        price_range=price_range
    )

    return matched


def _sort_by_relevance(
    products: List[Dict],
    use_case: Optional[str] = None,
    brands: Optional[List[str]] = None,
    price_range: Optional[Dict] = None
) -> List[Dict]:
    """按相关度排序"""

    def calculate_score(product: Dict) -> float:
        score = 0.0

        # 使用场景匹配
        if use_case and use_case in product.get("use_cases", []):
            score += 30

        # 品牌偏好匹配
        if brands and product["brand"] in brands:
            score += 20

        # 价格适中度（越接近价格区间中点越好）
        if price_range:
            price_mid = (price_range["min"] + price_range["max"]) / 2
            price_diff = abs(product["price"] - price_mid)
            score += max(0, 10 - price_diff / 200)

        # 销量和评分
        score += product["rating"] * 2
        score += min(product["sales"] / 10000, 5)

        return score

    return sorted(products, key=calculate_score, reverse=True)
