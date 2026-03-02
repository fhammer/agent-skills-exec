---
name: demand_analysis
version: 1.0.0
description: 分析用户需求，提取商品类别、预算、品牌偏好、使用场景等约束条件
triggers:
  - 我想买
  - 推荐
  - 有什么
  - 找
  - 买个
tags:
  - ecommerce
  - recommendation
  - analysis
input_schema:
  type: object
  properties:
    user_input:
      type: string
      description: 用户输入
    conversation_history:
      type: array
      description: 对话历史
  required:
    - user_input
output_schema: demand_analysis.schema.DemandAnalysisResult
---

# 需求分析 Skill

## 功能说明

分析用户的商品需求输入，提取结构化的需求约束条件，包括：
- 商品类别（手机、电脑、耳机等）
- 预算范围
- 品牌偏好
- 使用场景/需求（游戏、办公、拍照等）
- 缺失信息（需要进一步询问的信息）

## 使用示例

```
用户: "我想买个2000-3000元的手机，平时玩游戏比较多"

输出:
{
  "intent": "product_inquiry",
  "category": "手机",
  "constraints": {
    "price_range": {"min": 2000, "max": 3000},
    "use_case": "gaming",
    "priority_features": ["性能", "屏幕刷新率"]
  },
  "missing_info": ["品牌偏好", "存储容量"]
}
```

## 注意事项

1. 如果用户未指定类别，需要引导用户说明
2. 预算范围可能不明确，需要确认
3. 优先识别显式提到的约束条件
