# 电商场景Demo设计文档

**版本**: 1.0.0
**日期**: 2026-02-28
**作者**: AI产品经理
**状态**: 设计阶段

---

## 目录

1. [概述](#概述)
2. [Demo 1: 智能导购/商品推荐Agent](#demo-1-智能导购商品推荐agent)
3. [Demo 2: 订单处理/售后客服Agent](#demo-2-订单处理售后客服agent)
4. [数据模型设计](#数据模型设计)
5. [API接口设计](#api接口设计)
6. [部署架构](#部署架构)
7. [测试用例](#测试用例)

---

## 概述

### 设计目标

本文档定义两个电商场景Demo的设计：

1. **智能导购/商品推荐Agent** - 帮助用户发现商品、提供购买建议
2. **订单处理/售后客服Agent** - 处理订单查询、售后问题

### 核心用户价值

| Demo | 用户价值 | 关键能力 |
|------|----------|----------|
| 智能导购 | 快速找到合适商品，降低决策成本 | 需求分析、个性化推荐、多轮对话 |
| 订单/售后 | 高效解决问题，提升购物体验 | 订单追踪、政策验证、工单处理 |

### 技术亮点

1. **双引擎执行** - 规则引擎处理确定性逻辑（如价格区间过滤），LLM处理复杂推理
2. **多轮对话管理** - 状态机驱动的对话流程，支持上下文保持和意图切换
3. **渐进式披露** - 仅向当前Skill传递必要的上下文，控制Token消耗
4. **全链路审计** - 每个决策和操作都有完整记录，可追溯可解释

---

## Demo 1: 智能导购/商品推荐Agent

### 1.1 场景概述

**目标用户**: 电商平台消费者

**场景描述**: 用户想要购买某类商品但不确定具体选择，Agent通过多轮对话了解用户需求，提供个性化商品推荐。

**典型对话流**:

```
用户: 我想买个手机
Agent: 好的，请问您有什么具体需求吗？比如预算、品牌偏好、主要用途？
用户: 预算2000-3000，平时玩游戏比较多
Agent: 了解了，基于您的需求，我推荐以下几款手机：
      1. Redmi K70 (¥2499) - 骁龙8 Gen2，游戏性能出色
      2. iQOO Neo9 (¥2299) - 144Hz高刷屏，游戏体验佳
      需要了解哪款详情？
```

### 1.2 Skill设计

#### Skill 1: demand_analysis (需求分析)

**功能**: 分析用户输入，提取需求约束（类别、预算、品牌、功能等）

**输入示例**:
```json
{
  "user_input": "我想买个2000-3000的手机，平时玩游戏比较多",
  "conversation_history": []
}
```

**输出示例**:
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

#### Skill 2: user_profiling (用户画像)

**功能**: 获取用户历史偏好、浏览记录，用于个性化推荐

**输入示例**:
```json
{
  "user_id": "user_123",
  "current_category": "手机"
}
```

**输出示例**:
```json
{
  "structured": {
    "user_id": "user_123",
    "profile": {
      "preferred_brands": ["小米", "华为"],
      "price_preference": "中端",
      "recent_views": ["Redmi K70", "iQOO Neo9"],
      "purchase_history": ["小米13 (2023-10)"]
    },
    "recommendation_hints": {
      "focus_on": ["性价比", "游戏体验"],
      "avoid": ["苹果生态"]
    }
  },
  "text": "根据您的浏览和购买历史，您偏好性价比高的国产品牌。"
}
```

#### Skill 3: product_search (商品搜索)

**功能**: 根据约束条件搜索候选商品

**输入示例**:
```json
{
  "category": "手机",
  "constraints": {
    "price_range": {"min": 2000, "max": 3000},
    "brands": ["小米", "iQOO", "一加"]
  },
  "limit": 20
}
```

**输出示例**:
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
          "processor": "骁龙8 Gen2",
          "battery": "5000mAh",
          "charging": "120W快充"
        },
        "rating": 4.7,
        "sales": 50000,
        "stock": 1000
      }
      // ... more products
    ]
  },
  "text": "找到45款符合条件的手机，返回前20款。"
}
```

#### Skill 4: recommendation_ranking (推荐排序)

**功能**: 对候选商品进行多维度排序和筛选

**输入示例**:
```json
{
  "user_id": "user_123",
  "candidates": [/* product_search的输出 */],
  "user_profile": {/* user_profiling的输出 */},
  "constraints": {
    "priority": "性价比",
    "use_case": "gaming"
  },
  "top_n": 5
}
```

**输出示例**:
```json
{
  "structured": {
    "ranked_products": [
      {
        "rank": 1,
        "product_id": "p_001",
        "score": 0.92,
        "match_factors": {
          "price_match": 0.95,
          "brand_preference": 0.90,
          "performance": 0.95,
          "user_history": 0.88
        },
        "recommendation_reasons": [
          "符合您的预算范围",
          "游戏性能出色（骁龙8 Gen2）",
          "品牌符合您的偏好（小米）",
          "高性价比（4.7分好评）"
        ]
      }
      // ... more ranked products
    ],
    "excluded_products": [
      {
        "product_id": "p_015",
        "reason": "超出预算范围"
      }
    ]
  },
  "text": "根据您的需求和偏好，为您推荐以下5款手机："
}
```

#### Skill 5: recommendation_explanation (推荐理由生成)

**功能**: 生成自然语言的推荐理由说明

**输入示例**:
```json
{
  "user_id": "user_123",
  "recommendations": [/* recommendation_ranking的输出 */],
  "user_input": "我想买个手机，预算2000-3000，平时玩游戏比较多"
}
```

**输出示例**:
```json
{
  "structured": {
    "response_type": "recommendation",
    "products_count": 5,
    "highlighted_features": ["游戏性能", "性价比", "快充"]
  },
  "text": "根据您的需求，我为您推荐以下几款手机：\n\n**首选推荐：Redmi K70 (¥2499)**\n\n推荐理由：\n- 性能强劲：搭载骁龙8 Gen2处理器，游戏性能出色，王者荣耀、和平精英都能高帧率流畅运行\n- 屏幕优秀：2K分辨率+120Hz高刷屏，游戏画面细腻流畅\n- 续航给力：5000mAh大电池+120W快充，充电10分钟就能玩好几局\n- 性价比高：2499元的价格在同档位非常有竞争力，京东好评率4.7分\n\n**备选方案：**\n\n2. **iQOO Neo9 (¥2299)** - 144Hz电竞屏，专为游戏优化，价格更实惠\n3. **一加Ace 3 (¥2599)** - 质感出色，系统流畅，适合追求品质的用户\n4. **真我GT5 (¥2699)** - 150W快充，充电速度更快\n5. **荣耀90 GT (¥2399)** - 护眼屏幕，长时间游戏不易疲劳\n\n根据您的浏览历史，您对小米品牌比较偏好，Redmi K70应该会比较符合您的期望。需要我详细介绍哪款手机的更多信息吗？"
}
```

### 1.3 执行流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                    智能导购/商品推荐 Agent 执行流程                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  用户输入: "我想买个手机，预算2000-3000，平时玩游戏比较多"              │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────┐           │
│  │  Skill 1: demand_analysis (需求分析)                  │           │
│  │  ────────────────────────────────────────            │           │
│  │  输入: 用户原始输入                                  │           │
│  │  处理: 提取类别(手机)、预算(2000-3000)、用途(游戏)     │           │
│  │  输出: 结构化需求约束 + 缺失信息列表                   │           │
│  └─────────────────────────────────────────────────────┘           │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────┐           │
│  │  Skill 2: user_profiling (用户画像)                   │           │
│  │  ────────────────────────────────────────            │           │
│  │  输入: user_id + current_category                    │           │
│  │  处理: 查询用户偏好、浏览历史、购买记录                 │           │
│  │  输出: 用户画像 + 推荐偏好提示                        │           │
│  └─────────────────────────────────────────────────────┘           │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────┐           │
│  │  Skill 3: product_search (商品搜索)                   │           │
│  │  ────────────────────────────────────────            │           │
│  │  输入: category + constraints (price_range等)         │           │
│  │  处理: 执行数据库查询，获取候选商品列表                 │           │
│  │  输出: 候选商品列表 (20-50个)                         │           │
│  └─────────────────────────────────────────────────────┘           │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────┐           │
│  │  Skill 4: recommendation_ranking (推荐排序)             │           │
│  │  ────────────────────────────────────────            │           │
│  │  输入: candidates + user_profile + constraints        │           │
│  │  处理: 多维度打分排序，生成推荐理由                     │           │
│  │  输出: 排序后的Top-N推荐列表 + 推荐理由                │           │
│  └─────────────────────────────────────────────────────┘           │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────┐           │
│  │  Skill 5: recommendation_explanation (推荐理由生成)      │           │
│  │  ────────────────────────────────────────            │           │
│  │  输入: recommendations + user_input                     │           │
│  │  处理: 生成自然语言推荐说明                           │           │
│  │  输出: 完整的推荐回复文本                             │           │
│  └─────────────────────────────────────────────────────┘           │
│                              │                                      │
│                              ▼                                      │
│  最终输出: 自然语言推荐回复                                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Demo 2: 订单处理/售后客服Agent

### 2.1 场景概述

**目标用户**: 电商平台消费者、客服人员

**场景描述**: 用户需要查询订单状态、申请退换货、咨询售后政策等，Agent通过多轮对话收集必要信息，调用业务系统完成操作。

**典型对话流 - 订单查询**:

```
用户: 帮我查一下订单状态
Agent: 好的，请问您要查询哪个订单？您可以提供订单号，或者我帮您查询最近的订单。
用户: 最近的订单
Agent: 好的，您最近一笔订单信息如下：
      订单号：20240228123456
      商品：Redmi K70 (¥2499)
      状态：已发货
      物流：顺丰速运，运单号 SF1234567890
      预计送达：3月1日
      需要查询物流详情吗？
```

**典型对话流 - 退货申请**:

```
用户: 我想退货
Agent: 好的，请问您要退哪个订单的商品？
用户: 订单 20240228123456
Agent: 该订单购买的是 Redmi K70，符合7天无理由退货条件。
      请问退货原因是什么？
用户: 质量问题，屏幕有坏点
Agent: 收到，质量问题属于卖家承担运费范围。
      已为您创建退货申请：
      - 退货单号：RT202402280001
      - 退货地址：广东省深圳市xxx仓库
      - 请在3天内将商品连同配件完整寄回
      - 运费将由卖家承担（请保留运费凭证）
      有任何问题可以随时联系我。
```

### 2.2 Skill设计

#### Skill 1: intent_classification (意图分类)

**功能**: 识别用户意图（查询订单、申请退货、咨询政策等）

**输入示例**:
```json
{
  "user_input": "我想退货",
  "conversation_history": []
}
```

**输出示例**:
```json
{
  "structured": {
    "primary_intent": "return_request",
    "confidence": 0.95,
    "secondary_intents": [
      {"intent": "exchange_request", "confidence": 0.15}
    ],
    "extracted_entities": {
      "action": "return"
    },
    "required_info": ["order_id", "reason"],
    "dialogue_state": "awaiting_order_id"
  },
  "text": "收到，我来帮您处理退货申请。"
}
```

#### Skill 2: order_query (订单查询)

**功能**: 查询订单状态、详情、物流信息

**输入示例**:
```json
{
  "user_id": "user_123",
  "query_type": "by_recent",
  "limit": 1
}
```

**输出示例**:
```json
{
  "structured": {
    "query_type": "recent_orders",
    "total_orders": 5,
    "orders": [
      {
        "order_id": "20240228123456",
        "status": "shipped",
        "status_text": "已发货",
        "create_time": "2024-02-28 10:30:00",
        "pay_time": "2024-02-28 10:35:00",
        "ship_time": "2024-02-28 14:20:00",
        "total_amount": 2499.00,
        "items": [
          {
            "product_id": "p_001",
            "name": "Redmi K70",
            "quantity": 1,
            "price": 2499.00,
            "image_url": "https://..."
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
          "latest_update": "2024-02-29 08:30:00 快件到达北京转运中心",
          "estimated_delivery": "2024-03-01"
        }
      }
    ]
  },
  "text": "您最近一笔订单信息如下：\n订单号：20240228123456\n商品：Redmi K70\n状态：已发货\n物流：顺丰速运 SF1234567890\n预计送达：3月1日"
}
```

#### Skill 3: policy_validation (政策验证)

**功能**: 验证退换货政策、检查订单资格

**输入示例**:
```json
{
  "order_id": "20240228123456",
  "service_type": "return",
  "reason": "quality_issue"
}
```

**输出示例**:
```json
{
  "structured": {
    "eligible": true,
    "order_id": "20240228123456",
    "service_type": "return",
    "validation_results": {
      "time_limit": {
        "policy": "7天无理由退货",
        "order_date": "2024-02-28",
        "deadline": "2024-03-06",
        "remaining_days": 5,
        "passed": true
      },
      "product_category": {
        "category": "手机",
        "returnable": true,
        "passed": true
      },
      "order_status": {
        "current_status": "shipped",
        "returnable": true,
        "passed": true
      }
    },
    "fee_policy": {
      "responsible_party": "seller",
      "reason": "质量问题",
      "buyer_cost": 0,
      "compensation": "运费卖家承担，需提供运费凭证"
    },
    "next_steps": [
      "填写退货原因",
      "选择退货方式（上门取件/自行寄回）",
      "寄回商品并保留运费凭证"
    ]
  },
  "text": "该订单符合退货条件。由于退货原因是质量问题，运费将由卖家承担。请在3月6日前完成退货。"
}
```

#### Skill 4: case_creation (工单创建)

**功能**: 创建退货单、换货单、投诉工单

**输入示例**:
```json
{
  "order_id": "20240228123456",
  "service_type": "return",
  "reason": "quality_issue",
  "reason_detail": "屏幕有坏点",
  "evidence": [
    "https://cdn.example.com/photos/1.jpg",
    "https://cdn.example.com/photos/2.jpg"
  ],
  "return_method": "self_ship",
  "refund_method": "original"
}
```

**输出示例**:
```json
{
  "structured": {
    "case_id": "RT202402280001",
    "case_type": "return",
    "status": "created",
    "created_at": "2024-02-28 16:30:00",
    "order_info": {
      "order_id": "20240228123456",
      "product_name": "Redmi K70",
      "product_id": "p_001"
    },
    "return_info": {
      "reason": "quality_issue",
      "reason_detail": "屏幕有坏点",
      "return_address": {
        "recipient": "xxx售后部",
        "phone": "400-xxx-xxxx",
        "address": "广东省深圳市xxx区xxx路xxx号"
      },
      "deadline": "2024-03-03 23:59:59",
      "return_method": "self_ship",
      "shipping_fee_policy": "seller_paid"
    },
    "refund_info": {
      "refund_amount": 2499.00,
      "refund_method": "original",
      "estimated_refund_time": "退货签收后3-5个工作日"
    },
    "next_steps": [
      {
        "step": 1,
        "action": "打包商品",
        "detail": "将商品及所有配件、发票完整打包"
      },
      {
        "step": 2,
        "action": "寄回商品",
        "detail": "使用顺丰/京东寄到退货地址，保留运费凭证"
      },
      {
        "step": 3,
        "action": "等待退款",
        "detail": "卖家签收后3-5个工作日原路退款"
      }
    ]
  },
  "text": "已为您创建退货申请，退货单号：RT202402280001\n\n请在3月3日前将商品寄回以下地址：\n收件人：xxx售后部\n地址：广东省深圳市xxx区xxx路xxx号\n电话：400-xxx-xxxx\n\n由于退货原因是质量问题，运费将由卖家承担，请您保留运费凭证。\n\n退款将在卖家签收后3-5个工作日原路退回。"
}
```

#### Skill 5: knowledge_base_query (知识库查询)

**功能**: 查询FAQ、售后政策、常见问题

**输入示例**:
```json
{
  "query": "退货需要运费吗",
  "context": {
    "service_type": "return",
    "reason": "quality_issue"
  }
}
```

**输出示例**:
```json
{
  "structured": {
    "query_type": "policy_inquiry",
    "matched_faqs": [
      {
        "faq_id": "faq_001",
        "question": "退货需要运费吗",
        "answer": "退货运费根据退货原因确定：质量问题由卖家承担，非质量问题由买家承担。",
        "relevance": 0.98
      },
      {
        "faq_id": "faq_002",
        "question": "质量问题如何认定",
        "answer": "商品存在功能故障、外观损坏、与描述不符等问题可认定为质量问题。",
        "relevance": 0.85
      }
    ],
    "policy_summary": {
      "general_rule": "质量问题卖家承担，非质量问题买家承担",
      "exceptions": ["VIP会员免运费", "7天无理由退货首单免运费"],
      "evidence_requirement": "质量问题需提供照片/视频证明"
    }
  },
  "text": "关于退货运费：\n\n**一般规则：**\n- 质量问题：由卖家承担运费\n- 非质量问题（如不喜欢、拍错）：由买家承担运费\n\n**您的当前情况：**\n由于退货原因是质量问题，运费将由卖家承担。建议您：\n1. 拍摄清晰的问题照片/视频作为凭证\n2. 使用顺丰/京东寄回，保留运费凭证\n3. 运费将与货款一并退回\n\n**特殊情况：**\n- VIP会员享受所有退货免运费\n- 首次7天无理由退货免运费\n\n还有其他问题吗？"
}
```

### 1.4 对话状态管理

```python
# 对话状态机设计
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

class DialogueState(Enum):
    """对话状态枚举"""
    INITIAL = "initial"                    # 初始状态
    AWAITING_CLARIFICATION = "awaiting_clarification"  # 等待澄清
    INFORMATION_GATHERING = "information_gathering"    # 信息收集中
    RECOMMENDATION_READY = "recommendation_ready"      # 推荐就绪
    EXPLAINING_DETAILS = "explaining_details"          # 解释详情中
    CONFIRMATION_PENDING = "confirmation_pending"      # 等待确认
    TASK_COMPLETED = "task_completed"                    # 任务完成
    HANDOVER_TO_HUMAN = "handover_to_human"            # 转人工

@dataclass
class Slot:
    """对话槽位"""
    name: str
    value: Optional[Any] = None
    required: bool = True
    confirmed: bool = False
    alternatives: list = field(default_factory=list)

@dataclass
class DialogueContext:
    """对话上下文"""
    session_id: str
    user_id: str
    tenant_id: str
    current_state: DialogueState = DialogueState.INITIAL
    slots: Dict[str, Slot] = field(default_factory=dict)
    history: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_state(self, new_state: DialogueState):
        """更新对话状态"""
        self.history.append({
            "from": self.current_state.value,
            "to": new_state.value,
            "timestamp": datetime.now().isoformat()
        })
        self.current_state = new_state

    def fill_slot(self, slot_name: str, value: Any, confirmed: bool = False):
        """填充槽位"""
        if slot_name in self.slots:
            self.slots[slot_name].value = value
            self.slots[slot_name].confirmed = confirmed

    def get_missing_required_slots(self) -> List[str]:
        """获取缺失的必填槽位"""
        return [
            name for name, slot in self.slots.items()
            if slot.required and slot.value is None
        ]
```

---

由于文档内容较长，我将继续创建第二部分，包含Demo 2的详细设计和数据模型。我需要：

1. 继续编写Demo 2 (订单处理/售后客服Agent)的设计
2. 添加数据模型设计
3. 添加API接口设计
4. 添加部署架构
5. 添加测试用例

让我继续编写文档。这将是一个较长的文档，我需要确保包含所有必要的细节。## Demo 2: 订单处理/售后客服Agent

### 2.1 场景概述

**目标用户**: 电商平台消费者、售后客服人员

**场景描述**: 用户需要查询订单状态、追踪物流、申请退换货或咨询售后政策。Agent通过多轮对话收集信息，调用业务系统完成查询或创建售后工单。

**典型对话流 - 退货申请**:

```
用户: 我想退货
Agent: 好的，请问您要退哪个订单的商品？
用户: 订单 20240228123456
Agent: 该订单购买的是 Redmi K70，符合7天无理由退货条件。
      请问退货原因是什么？
用户: 质量问题，屏幕有坏点
Agent: 收到，质量问题属于卖家承担运费范围。
      已为您创建退货申请：
      - 退货单号：RT202402280001
      - 退货地址：深圳市xxx仓库
      - 请在3天内寄回商品
      有任何问题可以随时联系我。
```

### 2.2 Skill设计

#### Skill 1: intent_classification (意图分类)

**功能**: 识别用户意图（查询订单、申请退货、咨询政策等）

**输出示例**:
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
  }
}
```

#### Skill 2: order_query (订单查询)

**功能**: 查询订单状态、详情、物流信息

**输出示例**:
```json
{
  "structured": {
    "orders": [{
      "order_id": "20240228123456",
      "status": "shipped",
      "items": [{"name": "Redmi K70", "price": 2499}],
      "logistics": {
        "company": "顺丰速运",
        "tracking_no": "SF1234567890"
      }
    }]
  }
}
```

#### Skill 3: policy_validation (政策验证)

**功能**: 验证退换货政策、检查订单资格

**输出示例**:
```json
{
  "structured": {
    "eligible": true,
    "validation_results": {
      "time_limit": {"passed": true, "remaining_days": 5},
      "product_category": {"returnable": true}
    },
    "fee_policy": {
      "responsible_party": "seller",
      "reason": "质量问题"
    }
  }
}
```

#### Skill 4: case_creation (工单创建)

**功能**: 创建退货单、换货单、投诉工单

**输出示例**:
```json
{
  "structured": {
    "case_id": "RT202402280001",
    "status": "created",
    "return_info": {
      "deadline": "2024-03-03",
      "return_address": {...}
    }
  }
}
```

#### Skill 5: knowledge_base_query (知识库查询)

**功能**: 查询FAQ、售后政策、常见问题

**输出示例**:
```json
{
  "structured": {
    "matched_faqs": [...],
    "policy_summary": {
      "general_rule": "质量问题卖家承担，非质量问题买家承担"
    }
  }
}
```

---

## 数据模型设计

### 电商业务数据模型

```sql
-- 商品表
CREATE TABLE products (
    product_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    brand VARCHAR(50),
    price DECIMAL(10,2) NOT NULL,
    description TEXT,
    attributes JSONB,
    stock INT DEFAULT 0,
    sales INT DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 5.0,
    images JSONB,
    status VARCHAR(20) DEFAULT 'active',
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW(),
    INDEX idx_category (category),
    INDEX idx_brand (brand),
    INDEX idx_price (price),
    INDEX idx_status (status)
);

-- 订单表
CREATE TABLE orders (
    order_id VARCHAR(32) PRIMARY KEY,
    user_id VARCHAR(32) NOT NULL,
    status VARCHAR(20) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    pay_amount DECIMAL(10,2) NOT NULL,
    shipping_fee DECIMAL(10,2) DEFAULT 0,
    shipping_address JSONB NOT NULL,
    invoice_info JSONB,
    remark TEXT,
    pay_time TIMESTAMP,
    ship_time TIMESTAMP,
    receive_time TIMESTAMP,
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW(),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_create_time (create_time)
);

-- 订单商品表
CREATE TABLE order_items (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id VARCHAR(32) NOT NULL,
    product_id VARCHAR(32) NOT NULL,
    sku_id VARCHAR(32),
    product_name VARCHAR(200) NOT NULL,
    product_image VARCHAR(500),
    price DECIMAL(10,2) NOT NULL,
    quantity INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    attributes JSONB,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    INDEX idx_order_id (order_id)
);

-- 物流表
CREATE TABLE logistics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id VARCHAR(32) NOT NULL,
    company VARCHAR(50) NOT NULL,
    tracking_no VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    tracks JSONB,
    estimated_delivery DATE,
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    INDEX idx_order_id (order_id),
    INDEX idx_tracking_no (tracking_no)
);

-- 售后工单表
CREATE TABLE service_cases (
    case_id VARCHAR(32) PRIMARY KEY,
    order_id VARCHAR(32) NOT NULL,
    user_id VARCHAR(32) NOT NULL,
    case_type VARCHAR(20) NOT NULL,  -- return, exchange, refund, complain
    status VARCHAR(20) NOT NULL,
    reason VARCHAR(50) NOT NULL,
    reason_detail TEXT,
    evidence JSONB,
    shipping_info JSONB,
    refund_info JSONB,
    timeline JSONB,
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW(),
    close_time TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    INDEX idx_order_id (order_id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_create_time (create_time)
);

-- 用户画像表
CREATE TABLE user_profiles (
    user_id VARCHAR(32) PRIMARY KEY,
    preferences JSONB,
    browsing_history JSONB,
    purchase_history JSONB,
    tags JSONB,
    rfmm JSONB,  -- RFM模型数据
    update_time TIMESTAMP DEFAULT NOW()
);

-- FAQ知识库表
CREATE TABLE knowledge_base (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    category VARCHAR(50) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    keywords JSONB,
    related_questions JSONB,
    priority INT DEFAULT 0,
    hit_count INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW(),
    INDEX idx_category (category),
    INDEX idx_status (status),
    FULLTEXT idx_question (question)
);
```

---

## API接口设计

### 智能导购API

```yaml
paths:
  /api/v1/recommendation/chat:
    post:
      summary: 智能导购对话
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                session_id:
                  type: string
                  description: 会话ID，首次为空
                user_id:
                  type: string
                message:
                  type: string
                  description: 用户消息
                context:
                  type: object
                  description: 额外上下文
      responses:
        200:
          description: 成功响应
          content:
            application/json:
              schema:
                type: object
                properties:
                  session_id:
                    type: string
                  response:
                    type: string
                    description: Agent回复
                  recommendations:
                    type: array
                    items:
                      type: object
                      properties:
                        product_id:
                          type: string
                        name:
                          type: string
                        price:
                          type: number
                        image:
                          type: string
                        reasons:
                          type: array
                          items:
                            type: string
                  dialogue_state:
                    type: string
                    description: 对话状态
                  extracted_constraints:
                    type: object
                    description: 提取的约束条件

  /api/v1/recommendation/products:
    post:
      summary: 获取商品推荐
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                user_id:
                  type: string
                category:
                  type: string
                constraints:
                  type: object
                  properties:
                    price_min:
                      type: number
                    price_max:
                      type: number
                    brands:
                      type: array
                      items:
                        type: string
                limit:
                  type: integer
                  default: 5
      responses:
        200:
          description: 推荐结果
          content:
            application/json:
              schema:
                type: object
                properties:
                  recommendations:
                    type: array
                    items:
                      type: object
                      properties:
                        rank:
                          type: integer
                        product_id:
                          type: string
                        name:
                          type: string
                        price:
                          type: number
                        match_score:
                          type: number
                        reasons:
                          type: array
                          items:
                            type: string
```

### 订单/售后API

```yaml
paths:
  /api/v1/support/chat:
    post:
      summary: 售后客服对话
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                session_id:
                  type: string
                user_id:
                  type: string
                message:
                  type: string
      responses:
        200:
          description: 客服回复
          content:
            application/json:
              schema:
                type: object
                properties:
                  session_id:
                    type: string
                  response:
                    type: string
                  intent:
                    type: string
                  dialogue_state:
                    type: string
                  action_required:
                    type: object

  /api/v1/orders/{order_id}:
    get:
      summary: 查询订单详情
      parameters:
        - name: order_id
          in: path
          required: true
          schema:
            type: string
      responses:
        200:
          description: 订单详情
          content:
            application/json:
              schema:
                type: object
                properties:
                  order_id:
                    type: string
                  status:
                    type: string
                  items:
                    type: array
                  logistics:
                    type: object

  /api/v1/cases:
    post:
      summary: 创建售后工单
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                order_id:
                  type: string
                case_type:
                  type: string
                  enum: [return, exchange, refund, complain]
                reason:
                  type: string
                reason_detail:
                  type: string
                evidence:
                  type: array
      responses:
        201:
          description: 工单创建成功
          content:
            application/json:
              schema:
                type: object
                properties:
                  case_id:
                    type: string
                  status:
                    type: string
                  next_steps:
                    type: array
```

---

## 部署架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              负载均衡层                                        │
│                          (Nginx / AWS ALB)                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
┌───────▼────────┐         ┌───────────▼──────────┐      ┌──────────▼──────┐
│   API服务实例1  │         │    API服务实例2       │      │  API服务实例N  │
│  (FastAPI)     │         │    (FastAPI)         │      │   (FastAPI)   │
├────────────────┤         ├──────────────────────┤      ├───────────────┤
│ • 认证鉴权      │         │ • 认证鉴权            │      │ • 认证鉴权    │
│ • 请求路由      │         │ • 请求路由            │      │ • 请求路由    │
│ • 限流熔断      │         │ • 限流熔断            │      │ • 限流熔断    │
└───────┬────────┘         └───────────┬──────────┘      └───────┬───────┘
        │                              │                              │
        └──────────────────────────────┼──────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────┐
│                           业务服务层                                       │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐         │
│  │   订单服务        │  │   商品服务        │  │   用户服务        │         │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘         │
│           │                     │                     │                  │
│  ┌────────▼─────────┐  ┌─────────▼────────┐  ┌─────────▼────────┐         │
│  │   售后工单服务    │  │   物流服务       │  │   知识库服务      │         │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘         │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
┌───────▼────────┐         ┌───────────▼──────────┐      ┌──────────▼──────┐
│   主数据库      │         │    缓存层           │      │   消息队列      │
│  (PostgreSQL)  │         │   (Redis)           │      │  (RabbitMQ)    │
├────────────────┤         ├──────────────────────┤      ├───────────────┤
│ • 订单数据      │         │ • 会话缓存          │      │ • 异步任务    │
│ • 用户数据      │         │ • 热点数据          │      │ • 事件通知    │
│ • 商品数据      │         │ • 限流计数          │      │ • 日志收集    │
└────────────────┘         └──────────────────────┘      └───────────────┘
```

---

## 测试用例

### Demo 1: 智能导购测试用例

| 用例ID | 场景 | 用户输入 | 期望输出 |
|--------|------|----------|----------|
| REC-001 | 明确需求推荐 | "我想买个2000元左右的手机，主要拍照用" | 推荐拍照手机Top5，包含推荐理由 |
| REC-002 | 模糊需求引导 | "我想买个好东西" | 询问具体类别、预算、用途 |
| REC-003 | 多轮对话 | 第一轮:"推荐手机" → 第二轮:"2000左右，玩游戏" | 第二轮返回游戏手机推荐 |
| REC-004 | 商品对比 | "Redmi K70和iQOO Neo9哪个好" | 对比两款手机的优缺点 |
| REC-005 | 价格筛选 | "1000元以下的耳机推荐" | 返回符合预算的耳机列表 |
| REC-006 | 品牌偏好 | "华为的手机有什么好推荐" | 推荐华为手机，体现品牌偏好 |

### Demo 2: 订单/售后测试用例

| 用例ID | 场景 | 用户输入 | 期望输出 |
|--------|------|----------|----------|
| ORD-001 | 查询最近订单 | "查一下我的订单" | 返回最近一笔订单详情 |
| ORD-002 | 按订单号查询 | "订单 20240228123456" | 返回指定订单详情 |
| ORD-003 | 查询物流 | "我的快递到哪了" | 返回物流轨迹和预计送达时间 |
| RET-001 | 退货申请-质量问题 | "这个手机有问题，屏幕有坏点" | 创建退货单，告知退货运费政策 |
| RET-002 | 退货申请-无理由 | "我不喜欢这个颜色" | 告知7天无理由政策，创建退货单 |
| RET-003 | 换货申请 | "想换个颜色" | 检查库存，创建换货单 |
| FAQ-001 | 运费咨询 | "退货要运费吗" | 解释退货运费政策 |
| FAQ-002 | 时效咨询 | "多久能退款" | 说明退款时效 |

---

## 附录

### A. 术语表

| 术语 | 定义 |
|------|------|
| SKU | 库存保有单位，商品的最小库存单位 |
| SPU | 标准产品单位，商品信息聚合的最小单位 |
| 7天无理由退货 | 消费者收到商品后7天内可无理由退货 |
| RFM模型 | 通过最近购买时间(Recency)、购买频率(Frequency)、购买金额(Monetary)分析客户价值 |
| 工单 | 记录和跟踪客户服务请求的票据 |

### B. 参考资料

- 核心能力设计文档: `docs/design/core-capabilities-design.md`
- 现有PRD: `docs/PRD_Agent_Skills_Framework.md`
- 电商场景设计: `docs/ecommerce_skills_design.md`
- 框架设计文档: `docs/plans/2025-02-28-agent-skills-framework-design.md`
