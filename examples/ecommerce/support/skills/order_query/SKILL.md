---
name: order_query
version: 1.0.0
description: 查询订单状态、详情、物流信息
triggers:
  - 订单号
  - 查询
  - 最近订单
tags:
  - support
  - order
---

# 订单查询 Skill

## 功能说明

查询订单的详细信息，包括：
- 订单基本信息（订单号、状态、金额）
- 商品信息
- 收货地址
- 物流信息

## 输入格式

```json
{
  "user_id": "user_123",
  "query_type": "by_recent",
  "order_id": "20240228123456",
  "limit": 1
}
```

## 输出格式

```json
{
  "structured": {
    "query_type": "recent_orders",
    "total_orders": 1,
    "orders": [{
      "order_id": "20240228123456",
      "status": "shipped",
      "status_text": "已发货",
      "items": [...],
      "logistics": {...}
    }]
  },
  "text": "您最近一笔订单信息如下..."
}
```
