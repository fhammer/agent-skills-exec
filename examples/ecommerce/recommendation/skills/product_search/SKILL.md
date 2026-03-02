---
name: product_search
version: 1.0.0
description: 根据需求约束条件搜索商品数据库，获取候选商品列表
triggers:
  - 搜索
  - 查找
  - 商品
  - 产品
tags:
  - recommendation
  - search
  - products
---

# 商品搜索 Skill

## 功能说明

根据用户需求约束条件（类别、价格区间、品牌等）从商品数据库中搜索候选商品。

## 输入格式

```json
{
  "category": "手机",
  "constraints": {
    "price_range": {"min": 2000, "max": 3000},
    "brands": ["小米", "华为"],
    "use_case": "gaming"
  },
  "limit": 20
}
```

## 输出格式

```json
{
  "structured": {
    "total_found": 45,
    "returned": 20,
    "products": [
      {
        "product_id": "p_001",
        "name": "Redmi K70",
        "brand": "小米",
        "price": 2499,
        "category": "手机",
        "attributes": {
          "screen": "6.67英寸 2K 120Hz",
          "processor": "骁龙8 Gen2"
        },
        "rating": 4.7,
        "sales": 50000
      }
    ]
  },
  "text": "找到45款符合条件的手机，返回前20款。"
}
```

## 配置要求

需要配置商品数据库连接器，名为 `product_db`。
