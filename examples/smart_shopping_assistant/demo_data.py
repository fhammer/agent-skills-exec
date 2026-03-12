"""
演示商品数据 - Demo Product Data

包含各种类别的示例商品数据，用于智能购物助手演示。
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ProductCategory(Enum):
    """商品类别"""
    PHONE = "手机"
    LAPTOP = "笔记本"
    TABLET = "平板"
    HEADPHONE = "耳机"
    CAMERA = "相机"
    WATCH = "手表"
    TV = "电视"
    ACCESSORY = "配件"


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
    review_count: int = 100
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


# ============== 演示商品数据 ==============

DEMO_PRODUCTS: List[Product] = [
    # ===== 手机 =====
    Product(
        id="phone_001",
        name="小米14",
        brand="小米",
        category="手机",
        price=2999,
        original_price=3299,
        colors=["雅灰", "白色", "绿色", "粉色"],
        specs={
            "屏幕": "6.36英寸 OLED",
            "处理器": "骁龙8 Gen3",
            "电池": "4610mAh",
            "充电": "90W有线+50W无线",
            "相机": "5000万徕卡主摄",
        },
        features=["徕卡光学镜头", "骁龙8 Gen3", "90W快充", "IP68防水"],
        rating=4.8,
        review_count=12580,
        stock=500,
        description="小米14搭载徕卡光学镜头，骁龙8 Gen3旗舰处理器，小屏旗舰之选。",
    ),
    Product(
        id="phone_002",
        name="vivo X100",
        brand="vivo",
        category="手机",
        price=3199,
        original_price=3499,
        colors=["星际蓝", "落日橙", "辰夜黑"],
        specs={
            "屏幕": "6.78英寸 AMOLED",
            "处理器": "天玑9300",
            "电池": "5000mAh",
            "充电": "120W快充",
            "相机": "5000万蔡司主摄",
        },
        features=["蔡司影像系统", "天玑9300", "120W快充", "V2影像芯片"],
        rating=4.7,
        review_count=8930,
        stock=350,
        description="vivo X100搭载蔡司影像系统，天玑9300旗舰芯片，专业影像旗舰。",
    ),
    Product(
        id="phone_003",
        name="iPhone 15",
        brand="苹果",
        category="手机",
        price=5999,
        colors=["粉色", "黄色", "绿色", "蓝色", "黑色"],
        specs={
            "屏幕": "6.1英寸 Super Retina XDR",
            "处理器": "A16仿生芯片",
            "电池": "3349mAh",
            "充电": "20W快充",
            "相机": "4800万主摄",
        },
        features=["灵动岛", "4800万像素", "A16芯片", "USB-C接口"],
        rating=4.8,
        review_count=25600,
        stock=800,
        description="iPhone 15配备灵动岛，4800万像素主摄，A16仿生芯片。",
    ),
    Product(
        id="phone_004",
        name="华为Mate 60 Pro",
        brand="华为",
        category="手机",
        price=6999,
        colors=["雅川青", "白沙银", "南糯紫", "雅丹黑"],
        specs={
            "屏幕": "6.82英寸 OLED",
            "处理器": "麒麟9000S",
            "电池": "5000mAh",
            "充电": "88W有线+50W无线",
            "相机": "5000万可变光圈",
        },
        features=["卫星通话", "玄武架构", "可变光圈", "鸿蒙4.0"],
        rating=4.9,
        review_count=18900,
        stock=200,
        description="华为Mate 60 Pro支持卫星通话，玄武钢化昆仑玻璃，全焦段超清影像。",
    ),
    # ===== 笔记本 =====
    Product(
        id="laptop_001",
        name="MacBook Air M3",
        brand="苹果",
        category="笔记本",
        price=8999,
        colors=["午夜色", "星光色", "深空灰", "银色"],
        specs={
            "屏幕": "13.6英寸 Liquid Retina",
            "处理器": "Apple M3",
            "内存": "8GB",
            "存储": "256GB SSD",
            "续航": "18小时",
        },
        features=["M3芯片", "18小时续航", "轻薄设计", "无风扇静音"],
        rating=4.8,
        review_count=8900,
        stock=300,
        description="MacBook Air M3，超轻薄设计，18小时续航，M3芯片强劲性能。",
    ),
    Product(
        id="laptop_002",
        name="联想拯救者Y9000P",
        brand="联想",
        category="笔记本",
        price=10999,
        original_price=11999,
        colors=["碳晶灰", "冰魄白"],
        specs={
            "屏幕": "16英寸 2.5K 165Hz",
            "处理器": "i9-14900HX",
            "显卡": "RTX 4060",
            "内存": "32GB",
            "存储": "1TB SSD",
        },
        features=["i9旗舰处理器", "RTX 4060", "165Hz高刷屏", "霜刃Pro散热"],
        rating=4.7,
        review_count=5600,
        stock=150,
        description="联想拯救者Y9000P，i9-14900HX+RTX 4060，专业电竞游戏本。",
    ),
    Product(
        id="laptop_003",
        name="华为MateBook X Pro",
        brand="华为",
        category="笔记本",
        price=9999,
        colors=["墨蓝", "锦白", "深空灰"],
        specs={
            "屏幕": "14.2英寸 3.1K OLED",
            "处理器": "Ultra 7 155H",
            "内存": "16GB",
            "存储": "1TB SSD",
            "重量": "980g",
        },
        features=["980g超轻", "3.1K OLED屏", "微绒机身", "华为生态"],
        rating=4.6,
        review_count=3200,
        stock=200,
        description="华为MateBook X Pro，980g超轻薄，3.1K OLED原色屏，微绒金属机身。",
    ),
    # ===== 耳机 =====
    Product(
        id="earphone_001",
        name="AirPods Pro 2",
        brand="苹果",
        category="耳机",
        price=1899,
        colors=["白色"],
        specs={
            "类型": "入耳式",
            "降噪": "主动降噪",
            "续航": "6小时(单次)",
            "充电": "MagSafe充电盒",
            "连接": "蓝牙5.3",
        },
        features=["H2芯片", "主动降噪", "通透模式", "空间音频"],
        rating=4.8,
        review_count=15200,
        stock=600,
        description="AirPods Pro 2，H2芯片，两倍主动降噪，个性化空间音频。",
    ),
    Product(
        id="earphone_002",
        name="索尼WH-1000XM5",
        brand="索尼",
        category="耳机",
        price=2499,
        original_price=2999,
        colors=["黑色", "银色", "蓝色"],
        specs={
            "类型": "头戴式",
            "降噪": "主动降噪",
            "续航": "30小时",
            "充电": "USB-C快充",
            "重量": "250g",
        },
        features=["8麦克风降噪", "30小时续航", "LDAC高清传输", "智能免摘"],
        rating=4.7,
        review_count=8900,
        stock=400,
        description="索尼WH-1000XM5，8麦克风系统，行业领先降噪，30小时续航。",
    ),
    Product(
        id="earphone_003",
        name="华为FreeBuds Pro 3",
        brand="华为",
        category="耳机",
        price=1299,
        colors=["冰霜银", "陶瓷白", "星河蓝"],
        specs={
            "类型": "入耳式",
            "降噪": "智慧动态降噪",
            "续航": "7小时(单次)",
            "连接": "蓝牙5.2",
            "芯片": "麒麟A2",
        },
        features=["麒麟A2芯片", "星闪连接", "智慧降噪", "空间音频"],
        rating=4.6,
        review_count=5600,
        stock=500,
        description="华为FreeBuds Pro 3，麒麟A2芯片，星闪连接技术，1.5Mbps无损传输。",
    ),
]


def get_demo_products() -> List[Product]:
    """获取演示商品列表"""
    return DEMO_PRODUCTS


def get_products_by_category(category: str) -> List[Product]:
    """按类别获取商品"""
    return [p for p in DEMO_PRODUCTS if p.category == category]


def get_product_by_id(product_id: str) -> Optional[Product]:
    """按ID获取商品"""
    for p in DEMO_PRODUCTS:
        if p.id == product_id:
            return p
    return None


def get_product_by_name(name: str) -> Optional[Product]:
    """按名称获取商品（模糊匹配）"""
    name_lower = name.lower()

    # 精确匹配
    for p in DEMO_PRODUCTS:
        if p.name.lower() == name_lower:
            return p

    # 包含匹配
    for p in DEMO_PRODUCTS:
        if name_lower in p.name.lower():
            return p

    return None


def search_products(
    query: str = "",
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    features: Optional[List[str]] = None,
) -> List[Product]:
    """搜索商品"""
    results = DEMO_PRODUCTS.copy()

    if query:
        query_lower = query.lower()
        results = [
            p for p in results
            if query_lower in p.name.lower()
            or query_lower in p.brand.lower()
            or query_lower in p.description.lower()
            or any(query_lower in f.lower() for f in p.features)
        ]

    if category:
        results = [p for p in results if p.category == category]

    if brand:
        results = [p for p in results if brand.lower() in p.brand.lower()]

    if min_price is not None:
        results = [p for p in results if p.price >= min_price]

    if max_price is not None:
        results = [p for p in results if p.price <= max_price]

    if features:
        results = [
            p for p in results
            if any(f.lower() in " ".join(p.features).lower() for f in features)
        ]

    return results


def format_product_card(product: Product, show_details: bool = False) -> str:
    """格式化商品卡片"""
    discount = product.get_discount()
    discount_str = f" (省{discount}%)" if discount else ""

    card = f"""
{'='*50}
📱 {product.name}
{'='*50}
💰 价格: ¥{product.price:,}{discount_str}"""

    if product.original_price:
        card += f" (原价 ¥{product.original_price:,})"

    card += f"""
🏷️ 品牌: {product.brand}
⭐ 评分: {product.rating}/5.0 ({product.review_count}条评价)
🎨 颜色: {', '.join(product.colors)}"""

    if show_details:
        card += """
📋 主要规格:
"""
        for key, value in product.specs.items():
            card += f"   • {key}: {value}\n"

        card += """
✨ 产品亮点:
"""
        for feature in product.features:
            card += f"   • {feature}\n"

        card += f"""
📝 产品简介:
{product.description}
"""

    card += "="*50 + "\n"
    return card


def get_category_stats() -> Dict[str, int]:
    """获取类别统计"""
    stats = {}
    for p in DEMO_PRODUCTS:
        cat = p.category
        stats[cat] = stats.get(cat, 0) + 1
    return stats


if __name__ == "__main__":
    # 测试数据
    print("=== 演示商品数据 ===\n")

    # 统计
    stats = get_category_stats()
    print("商品类别统计:")
    for cat, count in stats.items():
        print(f"  {cat}: {count}款")

    print(f"\n总计: {len(DEMO_PRODUCTS)} 款商品\n")

    # 显示几款商品
    print("=== 热门商品 ===\n")
    for product in DEMO_PRODUCTS[:3]:
        print(format_product_card(product, show_details=True))
        print()

    # 测试搜索
    print("=== 搜索测试: 手机 ===\n")
    results = search_products(query="手机", max_price=5000)
    print(f"找到 {len(results)} 款商品:\n")
    for p in results:
        print(format_product_card(p))
