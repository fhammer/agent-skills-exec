---
name: intent_classification
version: 1.0.0
description: 识别用户意图（查询订单、申请退货、咨询政策等）
triggers:
  - 查订单
  - 退货
  - 换货
  - 退款
  - 物流
  - 问题
  - 投诉
tags:
  - support
  - nlu
  - intent
---

# 意图分类 Skill

## 功能说明

识别用户的客服咨询意图，包括：
- 订单查询：查询订单状态、详情
- 退货申请：申请退货
- 换货申请：申请换货
- 退款咨询：询问退款进度
- 政策咨询：询问退换货政策
- 物流查询：查询物流信息
- 投诉：产品质量、服务投诉

## 输入格式

```json
{
  "user_input": "我想退货",
  "conversation_history": []
}
```

## 输出格式

```json
{
  "structured": {
    "primary_intent": "return_request",
    "confidence": 0.95,
    "extracted_entities": {
      "action": "return"
    },
    "required_info": ["order_id", "reason"],
    "dialogue_state": "awaiting_order_id"
  },
  "text": "收到，我来帮您处理退货申请。"
}
```

## 使用规则

1. 优先识别主要意图
2. 提取关键实体（订单号、原因等）
3. 确定所需的额外信息
4. 设置适当的对话状态
