---
name: recommendation_explanation
version: 1.0.0
description: 生成自然语言的推荐理由说明，为用户解释为什么推荐这些商品
triggers:
  - 为什么
  - 理由
  - 推荐
  - 解释
tags:
  - recommendation
  - explanation
  - llm
---

# 推荐解释 Skill

## 功能说明

基于推荐结果生成自然语言的推荐理由说明，帮助用户理解推荐逻辑。

## 输入格式

```json
{
  "recommendations": [
    {
      "rank": 1,
      "product_id": "p_001",
      "name": "Redmi K70",
      "price": 2499,
      "score": 0.92,
      "recommendation_reasons": [
        "符合您的预算范围",
        "游戏性能出色"
      ]
    }
  ],
  "user_input": "我想买个2000-3000元的手机，平时玩游戏"
}
```

## 输出格式

```json
{
  "structured": {
    "response_type": "recommendation",
    "products_count": 3
  },
  "text": "根据您的需求，我为您推荐以下几款手机：\n\n**首选推荐：Redmi K70 (¥2499)**\n\n推荐理由：\n- 性能强劲..."
}
```
