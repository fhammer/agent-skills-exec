---
name: case_creation
version: 1.0.0
description: 创建退货单、换货单、投诉工单
triggers:
  - 创建退货单
  - 提交申请
  - 确认退货
tags:
  - support
  - case
---

# 工单创建 Skill

## 功能说明

创建售后工单：
- 退货单
- 换货单
- 退款单
- 投诉工单

## 输入格式

```json
{
  "order_id": "20240228123456",
  "service_type": "return",
  "reason": "quality_issue",
  "reason_detail": "屏幕有坏点"
}
```

## 输出格式

```json
{
  "structured": {
    "case_id": "RT202402280001",
    "status": "created",
    "return_info": {...}
  },
  "text": "已为您创建退货申请..."
}
```
