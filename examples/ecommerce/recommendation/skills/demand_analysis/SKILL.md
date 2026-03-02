---
name: demand_analysis
version: 1.0.0
description: 分析用户需求，提取商品类别、预算、品牌偏好、使用场景等约束条件
triggers:
  - 我想买
  - 推荐
  - 有什么好
  - 想要
  - 需要
tags:
  - recommendation
  - nlu
  - demand
---

# 需求分析 Skill

## 功能说明

分析用户的商品需求输入，提取结构化的约束条件，包括：
- 商品类别（如：手机、耳机、电脑）
- 价格区间（预算范围）
- 品牌偏好
- 使用场景（如：游戏、办公、拍照）
- 其他特殊要求

## 输入格式

```json
{
  "user_input": "我想买个2000-3000元的手机，平时玩游戏比较多",
  "conversation_history": []
}
```

## 输出格式

```json
{
  "structured": {
    "intent": "product_inquiry",
    "category": "手机",
    "constraints": {
      "price_range": {"min": 2000, "max": 3000},
      "use_case": "gaming",
      "priority_features": ["性能", "屏幕刷新率"]
    },
    "missing_info": ["品牌偏好", "存储容量"]
  },
  "text": "已记录您的需求：预算2000-3000元的手机，主要用于游戏。"
}
```

## 使用规则

1. 如果用户未指定类别，主动询问
2. 如果用户未指定预算，提供价格区间选项
3. 理解模糊表达（如"便宜点"、"性价比高"）
4. 记录用户的品牌偏好
