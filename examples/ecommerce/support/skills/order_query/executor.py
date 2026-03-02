"""订单查询 Skill 执行器

查询订单状态、详情、物流信息
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

try:
    from agent.llm_base import LLMProvider as LLMBase
except ImportError:
    LLMBase = Any

from examples.ecommerce.support.schema import (
    Order, OrderItem, ShippingAddress, LogisticsInfo, OrderQueryResult
)


# 生成动态日期以适应测试
NOW = datetime.now()
RECENT_TIME = NOW - timedelta(days=2)  # 2天前
OLD_TIME = NOW - timedelta(days=20)  # 20天前

# 模拟订单数据库
MOCK_ORDERS = {
    "20240228123456": {
        "order_id": "20240228123456",
        "status": "shipped",
        "status_text": "已发货",
        "create_time": RECENT_TIME.strftime("%Y-%m-%d 10:30:00"),
        "pay_time": RECENT_TIME.strftime("%Y-%m-%d 10:35:00"),
        "ship_time": (RECENT_TIME + timedelta(hours=4)).strftime("%Y-%m-%d 14:20:00"),
        "total_amount": 2499.00,
        "items": [
            {
                "product_id": "p_001",
                "name": "Redmi K70",
                "quantity": 1,
                "price": 2499.00,
                "image_url": "https://example.com/p_001.jpg"
            }
        ],
        "shipping_address": {
            "name": "张三",
            "phone": "138****1234",
            "province": "北京市",
            "city": "北京市",
            "district": "朝阳区",
            "address": "xxx路xxx号"
        },
        "logistics": {
            "company": "顺丰速运",
            "tracking_no": "SF1234567890",
            "status": "in_transit",
            "latest_update": (RECENT_TIME + timedelta(days=1)).strftime("%Y-%m-%d 08:30:00") + " 快件到达北京转运中心",
            "estimated_delivery": (RECENT_TIME + timedelta(days=3)).strftime("%Y-%m-%d")
        }
    },
    "20240225098765": {
        "order_id": "20240225098765",
        "status": "received",
        "status_text": "已签收",
        "create_time": (NOW - timedelta(days=5)).strftime("%Y-%m-%d 15:20:00"),
        "pay_time": (NOW - timedelta(days=5)).strftime("%Y-%m-%d 15:25:00"),
        "ship_time": (NOW - timedelta(days=5)).strftime("%Y-%m-%d 18:00:00"),
        "receive_time": (NOW - timedelta(days=3)).strftime("%Y-%m-%d 10:15:00"),
        "total_amount": 499.00,
        "items": [
            {
                "product_id": "e_002",
                "name": "华为FreeBuds 4i",
                "quantity": 1,
                "price": 499.00,
                "image_url": "https://example.com/e_002.jpg"
            }
        ],
        "shipping_address": {
            "name": "张三",
            "phone": "138****1234",
            "province": "北京市",
            "city": "北京市",
            "district": "朝阳区",
            "address": "xxx路xxx号"
        },
        "logistics": {
            "company": "中通快递",
            "tracking_no": "ZT9876543210",
            "status": "delivered",
            "latest_update": (NOW - timedelta(days=3)).strftime("%Y-%m-%d 10:15:00") + " 已签收",
            "estimated_delivery": (NOW - timedelta(days=3)).strftime("%Y-%m-%d")
        }
    },
    "20240220012345": {
        "order_id": "20240220012345",
        "status": "pending_payment",
        "status_text": "待付款",
        "create_time": OLD_TIME.strftime("%Y-%m-%d 20:00:00"),
        "total_amount": 1899.00,
        "items": [
            {
                "product_id": "e_003",
                "name": "Apple AirPods Pro",
                "quantity": 1,
                "price": 1899.00,
                "image_url": "https://example.com/e_003.jpg"
            }
        ],
        "shipping_address": None,
        "logistics": None
    }
}


def execute(llm: LLMBase, sub_task: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """执行订单查询"""

    user_id = context.get("user_id", "user_123")
    order_id = context.get("order_id")
    query_type = context.get("query_type", "by_order_id")
    limit = context.get("limit", 5)

    if query_type == "by_recent" or not order_id:
        return _query_recent_orders(user_id, limit)
    else:
        return _query_by_order_id(order_id)


def _query_by_order_id(order_id: str) -> Dict[str, Any]:
    """根据订单号查询"""
    if order_id not in MOCK_ORDERS:
        return {
            "structured": {
                "query_type": "by_order_id",
                "total_orders": 0,
                "orders": []
            },
            "text": f"未找到订单号 {order_id}，请检查订单号是否正确。"
        }

    order_data = MOCK_ORDERS[order_id]
    order = _parse_order(order_data)

    return {
        "structured": {
            "query_type": "by_order_id",
            "total_orders": 1,
            "orders": [order.to_dict()]
        },
        "text": _format_order_text(order)
    }


def _query_recent_orders(user_id: str, limit: int) -> Dict[str, Any]:
    """查询最近的订单"""
    # 简化实现：返回前N个订单
    orders_data = list(MOCK_ORDERS.values())[:limit]
    orders = [_parse_order(data) for data in orders_data]

    if not orders:
        return {
            "structured": {
                "query_type": "recent_orders",
                "total_orders": 0,
                "orders": []
            },
            "text": "您暂时没有订单记录。"
        }

    return {
        "structured": {
            "query_type": "recent_orders",
            "total_orders": len(orders),
            "orders": [order.to_dict() for order in orders]
        },
        "text": _format_recent_orders_text(orders)
    }


def _parse_order(data: Dict[str, Any]) -> Order:
    """解析订单数据"""
    items = [
        OrderItem(
            product_id=item["product_id"],
            name=item["name"],
            quantity=item["quantity"],
            price=item["price"],
            image_url=item.get("image_url", "")
        )
        for item in data.get("items", [])
    ]

    shipping_address = None
    if data.get("shipping_address"):
        addr = data["shipping_address"]
        shipping_address = ShippingAddress(
            name=addr["name"],
            phone=addr["phone"],
            province=addr["province"],
            city=addr["city"],
            district=addr["district"],
            address=addr["address"]
        )

    logistics = None
    if data.get("logistics"):
        log = data["logistics"]
        logistics = LogisticsInfo(
            company=log["company"],
            tracking_no=log["tracking_no"],
            status=log["status"],
            latest_update=log.get("latest_update", ""),
            estimated_delivery=log.get("estimated_delivery", "")
        )

    return Order(
        order_id=data["order_id"],
        status=data["status"],
        status_text=data["status_text"],
        create_time=data["create_time"],
        pay_time=data.get("pay_time"),
        ship_time=data.get("ship_time"),
        receive_time=data.get("receive_time"),
        total_amount=data["total_amount"],
        items=items,
        shipping_address=shipping_address,
        logistics=logistics
    )


def _format_order_text(order: Order) -> str:
    """格式化订单文本"""
    lines = [
        f"订单号：{order.order_id}",
        f"商品：{', '.join(item.name for item in order.items)}",
        f"状态：{order.status_text}",
    ]

    if order.pay_time:
        lines.append(f"付款时间：{order.pay_time}")

    if order.ship_time:
        lines.append(f"发货时间：{order.ship_time}")

    if order.logistics:
        lines.append(f"物流：{order.logistics.company}，运单号 {order.logistics.tracking_no}")
        if order.logistics.estimated_delivery:
            lines.append(f"预计送达：{order.logistics.estimated_delivery}")

    if order.receive_time:
        lines.append(f"签收时间：{order.receive_time}")

    lines.append(f"订单金额：¥{order.total_amount:.2f}")

    return "\n".join(lines)


def _format_recent_orders_text(orders: List[Order]) -> str:
    """格式化最近订单文本"""
    if len(orders) == 1:
        return f"您最近一笔订单信息如下：\n\n{_format_order_text(orders[0])}"

    lines = ["您最近的订单如下：\n"]
    for i, order in enumerate(orders, 1):
        lines.append(f"\n{i}. 订单号：{order.order_id}")
        lines.append(f"   商品：{', '.join(item.name for item in order.items)}")
        lines.append(f"   状态：{order.status_text}")
        lines.append(f"   金额：¥{order.total_amount:.2f}")

    return "\n".join(lines)
