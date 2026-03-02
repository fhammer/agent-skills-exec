# 电商场景 Skills 设计文档

**版本**: 1.0.0
**日期**: 2026-02-28
**状态**: 设计阶段

---

## 概述

本文档详细描述电商场景下的三个核心 Skills 设计：
1. 订单查询智能体 (order_query)
2. 商品推荐智能体 (product_recommendation)
3. 售后服务智能体 (after_sales_service)

---

## 1. 订单查询智能体 (order_query)

### 功能概述

帮助用户查询订单状态、订单详情、物流信息等。

### Skill 定义

```yaml
---
name: order_query
version: 1.0.0
description: 电商订单查询智能体，支持订单状态、详情、物流查询
triggers:
  - 查询订单
  - 订单状态
  - 我的订单
  - 订单详情
  - 物流信息
  - 发货了吗
tags:
  - 电商
  - 订单
  - 查询
input_schema:
  type: object
  properties:
    order_id:
      type: string
      description: 订单ID
    user_id:
      type: string
      description: 用户ID
    query_type:
      type: string
      enum: [status, detail, logistics, list]
      description: 查询类型
output_schema: OrderQueryOutput
tools:
  - query_order_by_id
  - query_orders_by_user
  - query_order_status
  - query_logistics
  - format_order_info
data_sources:
  - order_database
  - logistics_api
---

# order_query Skill

## 功能说明

### 支持的查询类型

1. **订单状态查询** - 查询订单当前状态（待支付、已发货、已完成等）
2. **订单详情查询** - 查询订单完整信息（商品、金额、收货地址等）
3. **物流信息查询** - 查询订单物流轨迹
4. **订单列表查询** - 查询用户所有订单

### 查询方式

- 按 **订单ID** 精确查询
- 按 **用户ID** 查询订单列表
- 按 **时间范围** 筛选
- 按 **状态** 筛选

## 使用示例

### 示例 1: 查询订单状态

**用户输入**:
```
帮我查一下订单 2024022812345 的状态
```

**执行结果**:
```json
{
  "structured": {
    "order_id": "2024022812345",
    "status": "shipped",
    "status_text": "已发货",
    "estimated_delivery": "2024-03-01",
    "update_time": "2024-02-28 10:30:00"
  },
  "text": "您的订单 2024022812345 已于 2月28日 发货，预计 3月1日 送达。物流公司：顺丰速运，运单号：SF1234567890。"
}
```

### 示例 2: 查询订单详情

**用户输入**:
```
订单 2024022812345 的详细信息是什么？
```

**执行结果**:
```json
{
  "structured": {
    "order_id": "2024022812345",
    "user_id": "user_123",
    "status": "shipped",
    "total_amount": 299.00,
    "items": [
      {
        "product_id": "p_001",
        "name": "无线蓝牙耳机",
        "quantity": 1,
        "price": 299.00
      }
    ],
    "shipping_address": {
      "name": "张三",
      "phone": "138****1234",
      "address": "北京市朝阳区xxx"
    },
    "create_time": "2024-02-27 14:20:00"
  },
  "text": "订单 2024022812345 详情：\n商品：无线蓝牙耳机 x1\n金额：¥299.00\n收货人：张三\n地址：北京市朝阳区xxx\n状态：已发货"
}
```

### 示例 3: 查询物流信息

**用户输入**:
```
这个订单到哪了？
```

**执行结果**:
```json
{
  "structured": {
    "order_id": "2024022812345",
    "logistics": [
      {"time": "2024-02-28 10:30", "status": "已发货", "location": "北京仓"},
      {"time": "2024-02-28 18:20", "status": "运输中", "location": "北京转运中心"},
      {"time": "2024-02-29 02:15", "status": "运输中", "location": "上海转运中心"}
    ],
    "estimated_delivery": "2024-03-01"
  },
  "text": "订单当前运输进度：\n2月28日 10:30 - 北京仓已发货\n2月28日 18:20 - 到达北京转运中心\n2月29日 02:15 - 到达上海转运中心\n预计 3月1日 派送"
}
```
```

### 实现架构

```
┌─────────────────────────────────────────────────────────┐
│                   order_query Skill                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐    │
│  │              executor.py (混合执行)               │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │  1. 参数提取 (规则引擎)                   │    │    │
│  │  │     - 提取订单ID/用户ID                   │    │    │
│  │  │     - 识别查询类型                        │    │    │
│  │  └─────────────────────────────────────────┘    │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │  2. 数据查询 (Tool 调用)                 │    │    │
│  │  │     - query_order_by_id                 │    │    │
│  │  │     - query_order_status                │    │    │
│  │  │     - query_logistics                   │    │    │
│  │  └─────────────────────────────────────────┘    │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │  3. 结果格式化 (规则引擎)                │    │    │
│  │  │     - 状态映射                          │    │    │
│  │  │     - 时间格式化                        │    │    │
│  │  └─────────────────────────────────────────┘    │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │  4. 文本生成 (LLM)                       │    │    │
│  │  │     - 生成友好的回复文本                 │    │    │
│  │  └─────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 依赖的 Tools

```python
# tools/query_order.py
class QueryOrderTool(Tool):
    """订单查询工具"""

    def execute(self, order_id: str, user_id: str = None):
        """
        从订单数据库查询订单信息

        Args:
            order_id: 订单ID
            user_id: 用户ID（用于权限验证）

        Returns:
            订单信息字典
        """
        pass

# tools/query_logistics.py
class QueryLogisticsTool(Tool):
    """物流查询工具"""

    def execute(self, order_id: str):
        """
        从物流API查询物流信息

        Args:
            order_id: 订单ID

        Returns:
            物流轨迹列表
        """
        pass

# tools/format_order.py
class FormatOrderInfoTool(Tool):
    """订单信息格式化工具"""

    def execute(self, order: dict, format_type: str = "default"):
        """
        格式化订单信息

        Args:
            order: 原始订单数据
            format_type: 格式类型

        Returns:
            格式化后的数据
        """
        pass
```

---

## 2. 商品推荐智能体 (product_recommendation)

### 功能概述

根据用户需求和画像，智能推荐合适的商品。

### Skill 定义

```yaml
---
name: product_recommendation
version: 1.0.0
description: 智能商品推荐，支持基于需求、偏好、历史的推荐
triggers:
  - 推荐
  - 有什么好
  - 想买
  - 建议
  - 哪个好
tags:
  - 电商
  - 推荐
  - 商品
input_schema:
  type: object
  properties:
    query:
      type: string
      description: 用户查询/需求描述
    category:
      type: string
      description: 商品类别
    price_range:
      type: array
      items: [number, number]
      description: 价格区间
    preferences:
      type: object
      description: 用户偏好
output_schema: ProductRecommendationOutput
tools:
  - query_user_profile
  - search_products
  - calculate_similarity
  - rank_products
  - generate_recommendation_reason
data_sources:
  - product_database
  - user_profile_database
  - recommendation_engine
---

# product_recommendation Skill

## 功能说明

### 推荐策略

1. **基于需求推荐** - 根据用户明确需求推荐
2. **基于偏好推荐** - 根据用户历史偏好推荐
3. **基于相似用户推荐** - 协同过滤
4. **热门商品推荐** - 热销、新品

### 推荐维度

- 价格区间
- 品牌偏好
- 功能需求
- 用户评价
- 销量/热度

## 使用示例

### 示例 1: 明确需求推荐

**用户输入**:
```
我想买一个2000元左右的手机，性价比高的
```

**执行结果**:
```json
{
  "structured": {
    "query_type": "explicit_need",
    "constraints": {
      "category": "手机",
      "price_range": [1500, 2500],
      "priority": "性价比"
    },
    "recommendations": [
      {
        "product_id": "p_001",
        "name": "Xiaomi 14",
        "brand": "小米",
        "price": 1999,
        "score": 0.92,
        "reasons": ["旗舰处理器", "高刷新率屏幕", "长续航"],
        "stats": {"sales": 10000, "rating": 4.8}
      },
      {
        "product_id": "p_002",
        "name": "Redmi K70",
        "brand": "红米",
        "price": 2199,
        "score": 0.88,
        "reasons": ["优秀拍照", "快充技术"],
        "stats": {"sales": 8000, "rating": 4.7}
      }
    ]
  },
  "text": "根据您的需求，我为您推荐以下两款手机：\n\n1. Xiaomi 14 (¥1999)\n   - 旗舰级处理器，性能强劲\n   - 120Hz 高刷新率屏幕\n   - 5000mAh 大电池\n   销量：1万+ | 评分：4.8\n\n2. Redmi K70 (¥2199)\n   - 优秀拍照能力\n   - 120W 快充\n   - 性价比出色\n   销量：8000+ | 评分：4.7"
}
```

### 示例 2: 浏览记录推荐

**用户输入**:
```
有什么好的耳机推荐吗？
```

**执行结果**:
```json
{
  "structured": {
    "query_type": "preference_based",
    "user_profile": {
      "recent_views": ["蓝牙耳机", "运动耳机"],
      "price_preference": "中端",
      "brand_preference": ["Sony", "Bose"]
    },
    "recommendations": [
      {
        "product_id": "p_101",
        "name": "Sony WF-1000XM5",
        "price": 1899,
        "match_reason": "符合您的品牌偏好，降噪效果出色"
      }
    ]
  },
  "text": "基于您近期的浏览记录，我为您推荐：\n\nSony WF-1000XM5 (¥1899)\n- 业界领先的降噪技术\n- 符合您对 Sony 品牌的偏好\n- 30小时总续航"
}
```

### 实现架构

```
┌─────────────────────────────────────────────────────────┐
│              product_recommendation Skill                │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐    │
│  │              executor.py (混合执行)               │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │  1. 需求分析 (LLM)                       │    │    │
│  │  │     - 提取类别                           │    │    │
│  │  │     - 提取价格区间                       │    │    │
│  │  │     - 识别核心需求                       │    │    │
│  │  └─────────────────────────────────────────┘    │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │  2. 用户画像获取 (Tool)                  │    │    │
│  │  │     - query_user_profile                │    │    │
│  │  │     - 获取历史偏好                       │    │    │
│  │  └─────────────────────────────────────────┘    │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │  3. 商品搜索 (Tool)                     │    │    │
│  │  │     - search_products                   │    │    │
│  │  │     - 按条件筛选                         │    │    │
│  │  └─────────────────────────────────────────┘    │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │  4. 相似度计算 (规则引擎)                │    │    │
│  │  │     - calculate_similarity              │    │    │
│  │  │     - 多维度打分                         │    │    │
│  │  └─────────────────────────────────────────┘    │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │  5. 排序和筛选 (规则引擎)                │    │    │
│  │  │     - rank_products                     │    │    │
│  │  │     - Top-N 选择                         │    │    │
│  │  └─────────────────────────────────────────┘    │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │  6. 推荐理由生成 (LLM)                   │    │    │
│  │  │     - generate_recommendation_reason    │    │    │
│  │  └─────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 售后服务智能体 (after_sales_service)

### 功能概述

处理用户的售后问题，包括退货、换货、投诉、咨询等。

### Skill 定义

```yaml
---
name: after_sales_service
version: 1.0.0
description: 电商售后服务智能体，处理退换货、投诉、咨询等
triggers:
  - 退货
  - 换货
  - 投诉
  - 售后
  - 问题
  - 有问题
tags:
  - 电商
  - 售后
  - 客服
input_schema:
  type: object
  properties:
    intent:
      type: string
      enum: [return, exchange, complain, consult]
      description: 用户意图
    order_id:
      type: string
      description: 关联订单ID
    reason:
      type: string
      description: 原因描述
    conversation_history:
      type: array
      description: 对话历史（用于多轮交互）
output_schema: AfterSalesServiceOutput
tools:
  - validate_return_policy
  - validate_exchange_policy
  - check_order_eligibility
  - create_return_request
  - create_exchange_request
  - create_complain_ticket
  - query_knowledge_base
  - update_conversation_state
data_sources:
  - order_database
  - policy_database
  - knowledge_base
  - crm_system
---

# after_sales_service Skill

## 功能说明

### 支持的服务类型

1. **退货服务** - 创建退货单，审核退货申请
2. **换货服务** - 创建换货单，处理换货流程
3. **投诉服务** - 创建投诉工单，跟进处理
4. **咨询服务** - 查询知识库，解答常见问题

### 服务流程

```
用户发起请求
    ↓
意图识别
    ↓
┌─────────┬─────────┬─────────┬─────────┐
│  退货   │  换货   │  投诉   │  咨询   │
└────┬────┴────┬────┴────┬────┴────┬────┘
     │         │         │         │
     ↓         ↓         ↓         ↓
  政策检查   政策检查   创建工单   知识库
     │         │                   查询
     ↓         ↓
  资格审核   资格审核
     │         │
     ↓         ↓
  创建退货单 创建换货单
     │         │
     └────┬────┘
          ↓
     生成回复
```

## 使用示例

### 示例 1: 退货服务（多轮对话）

**第一轮**:
```
用户: 我想退货
Agent: 好的，请问您要退哪个订单？
```

**第二轮**:
```
用户: 订单 2024022812345
Agent: 收到，该订单购买于 7 天内，符合退货条件。请问退货原因是什么？
```

**第三轮**:
```
用户: 质量有问题，耳机有杂音
Agent: 已为您创建退货申请：
- 退货单号：RT202402280001
- 订单：2024022812345
- 退货原因：质量问题（有杂音）
- 退货地址：上海市浦东新区xxx路xxx号
- 请在 3 天内寄回商品

退货审核通过后，款项将原路返回，预计 3-5 个工作日到账。
```

### 示例 2: 换货服务

**用户输入**:
```
我的订单 2024022812345 想换个颜色
```

**执行结果**:
```json
{
  "structured": {
    "service_type": "exchange",
    "order_id": "2024022812345",
    "eligibility": {
      "eligible": true,
      "reason": "购买15天内，可换货"
    },
    "exchange_request": {
      "request_id": "EX202402280001",
      "status": "pending",
      "current_item": {"product_id": "p_001", "color": "黑色"},
      "exchange_options": ["白色", "蓝色"]
    }
  },
  "text": "您的订单可以换货。当前商品：无线蓝牙耳机（黑色）。可换颜色：白色、蓝色。\n\n请回复您想换的颜色，我将为您创建换货单。"
}
```

### 示例 3: 投诉服务

**用户输入**:
```
我要投诉！配送太慢了！
```

**执行结果**:
```json
{
  "structured": {
    "service_type": "complain",
    "ticket_id": "TK202402280001",
    "status": "created",
    "category": "配送问题",
    "priority": "高"
  },
  "text": "已为您创建投诉工单：TK202402280001\n\n问题类型：配送问题\n处理优先级：高\n\n我们的客服专员将在 2 小时内联系您，请您保持电话畅通。"
}
```

### 示例 4: 咨询服务

**用户输入**:
```
退货需要运费吗？
```

**执行结果**:
```json
{
  "structured": {
    "service_type": "consult",
    "answer": {
      "general_rule": "质量问题卖家承担运费，非质量问题买家承担",
      "exceptions": ["VIP会员", "7天无理由退货"]
    }
  },
  "text": "关于退货运费：\n\n1. 质量问题：由卖家承担运费\n2. 非质量问题：由买家承担运费\n3. 特殊情况：VIP会员享受免费退货\n\n如有疑问，可联系客服详细咨询。"
}
```

### 多轮对话实现

```python
# 对话状态管理
class ConversationState:
    def __init__(self):
        self.state = "initial"
        self.collected_info = {}

    def update(self, user_input, intent):
        if self.state == "initial":
            if intent == "return":
                self.state = "awaiting_order_id"
                return "请问您要退哪个订单？"
        elif self.state == "awaiting_order_id":
            order_id = extract_order_id(user_input)
            self.collected_info["order_id"] = order_id
            self.state = "awaiting_reason"
            return "请告知退货原因"
        # ... 更多状态
```

### 实现架构

```
┌─────────────────────────────────────────────────────────┐
│            after_sales_service Skill                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐    │
│  │              executor.py (混合执行)               │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │  1. 意图识别 (LLM)                       │    │    │
│  │  │     - 分类：退货/换货/投诉/咨询           │    │    │
│  │  │     - 提取关键信息                        │    │    │
│  │  └─────────────────────────────────────────┘    │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │  2. 对话状态管理 (规则引擎)              │    │    │
│  │  │     - 检查是否需要更多信息               │    │    │
│  │  │     - 更新对话状态                       │    │    │
│  │  └─────────────────────────────────────────┘    │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │  3. 政策验证 (规则引擎)                  │    │    │
│  │  │     - validate_return_policy            │    │    │
│  │  │     - check_order_eligibility           │    │    │
│  │  └─────────────────────────────────────────┘    │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │  4. 业务处理 (Tool)                     │    │    │
│  │  │     - create_return_request             │    │    │
│  │  │     - create_exchange_request           │    │    │
│  │  │     - create_complain_ticket            │    │    │
│  │  └─────────────────────────────────────────┘    │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │  5. 知识库查询 (Tool)                   │    │    │
│  │  │     - query_knowledge_base              │    │    │
│  │  └─────────────────────────────────────────┘    │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │  6. 回复生成 (LLM)                      │    │    │
│  │  │     - 根据处理结果生成友好回复           │    │    │
│  │  └─────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 数据源设计

### 1. order_database (订单数据库)

```sql
-- 订单表
CREATE TABLE orders (
    order_id VARCHAR(32) PRIMARY KEY,
    user_id VARCHAR(32) NOT NULL,
    status VARCHAR(20) NOT NULL,
    total_amount DECIMAL(10,2),
    shipping_address JSON,
    create_time TIMESTAMP,
    update_time TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);

-- 订单商品表
CREATE TABLE order_items (
    id BIGINT PRIMARY KEY,
    order_id VARCHAR(32),
    product_id VARCHAR(32),
    quantity INT,
    price DECIMAL(10,2),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
```

### 2. product_database (商品数据库)

```sql
-- 商品表
CREATE TABLE products (
    product_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(200),
    category VARCHAR(50),
    brand VARCHAR(50),
    price DECIMAL(10,2),
    description TEXT,
    attributes JSON,
    stock INT,
    sales INT DEFAULT 0,
    rating DECIMAL(3,2),
    create_time TIMESTAMP
);
```

### 3. user_profile_database (用户画像数据库)

```sql
-- 用户画像表
CREATE TABLE user_profiles (
    user_id VARCHAR(32) PRIMARY KEY,
    preferences JSON,
    browsing_history JSON,
    purchase_history JSON,
    tags JSON,
    update_time TIMESTAMP
);
```

### 4. knowledge_base (知识库)

```sql
-- FAQ 表
CREATE TABLE faqs (
    id BIGINT PRIMARY KEY,
    category VARCHAR(50),
    question TEXT,
    answer TEXT,
    keywords JSON,
    priority INT,
    create_time TIMESTAMP
);
```

---

## API 集成示例

### 物流 API 集成

```python
class LogisticsAPIConnector(Tool):
    """物流 API 连接器"""

    def execute(self, order_id: str) -> dict:
        """查询物流信息"""
        url = f"{self.base_url}/logistics/{order_id}"
        response = requests.get(url, headers=self.auth_headers)
        return response.json()

# 注册为 Tool
coordinator.tools.register(LogisticsAPIConnector(
    base_url="https://api.logistics.com",
    auth_headers={"Authorization": "Bearer xxx"}
))
```

### 支付 API 集成

```python
class PaymentAPIConnector(Tool):
    """支付 API 连接器"""

    def execute(self, action: str, **kwargs) -> dict:
        """执行支付相关操作"""
        url = f"{self.base_url}/payment/{action}"
        response = requests.post(url, json=kwargs, headers=self.auth_headers)
        return response.json()
```

---

## 部署配置

### 数据源配置

```yaml
# config.yaml
data_sources:
  order_database:
    type: postgresql
    connection_string: "${DB_URL}"
    pool_size: 10

  product_database:
    type: postgresql
    connection_string: "${DB_URL}"
    pool_size: 10

  logistics_api:
    type: http
    base_url: "https://api.logistics.com"
    auth:
      type: bearer
      token: "${LOGISTICS_API_KEY}"

  knowledge_base:
    type: elasticsearch
    hosts: ["${ES_HOST}"]
    index: "faqs"
```

### Skill 配置

```yaml
# agent 配置
agent:
  name: "ecommerce_assistant"
  description: "电商智能客服"
  skills:
    - order_query
    - product_recommendation
    - after_sales_service

  # 多轮对话配置
  conversation:
    enabled: true
    max_turns: 10
    timeout: 300
```

---

**文档版本**: 1.0.0
**最后更新**: 2026-02-28
