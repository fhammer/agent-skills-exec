---
name: policy_validation
version: 1.0.0
description: 验证退换货政策、检查订单资格
triggers:
  - 退货
  - 换货
  - 退款
tags:
  - support
  - policy
---

# 政策验证 Skill

## 功能说明

验证订单是否符合退换货条件：
- 时间限制检查（7天无理由退货）
- 商品类别检查
- 订单状态检查
- 费用政策判断

## 输入格式

```json
{
  "order_id": "20240228123456",
  "service_type": "return",
  "reason": "quality_issue"
}
```

## 输出格式

```json
{
  "structured": {
    "eligible": true,
    "validation_results": {...},
    "fee_policy": {...}
  },
  "text": "该订单符合退货条件..."
}
```
