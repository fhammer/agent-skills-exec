"""订单售后客服Agent主执行器

处理订单查询、退换货申请、物流查询等售后场景
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class ServiceIntent(Enum):
    """售后意图枚举"""
    ORDER_QUERY = "order_query"
    LOGISTICS_QUERY = "logistics_query"
    RETURN_REQUEST = "return_request"
    EXCHANGE_REQUEST = "exchange_request"
    POLICY_INQUIRY = "policy_inquiry"
    COMPLAINT = "complaint"
    UNKNOWN = "unknown"


class DialogueState(Enum):
    """对话状态枚举"""
    INITIAL = "initial"
    AWAITING_ORDER_ID = "awaiting_order_id"
    AWAITING_REASON = "awaiting_reason"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    READY_TO_PROCESS = "ready_to_process"
    TASK_COMPLETED = "task_completed"
    HANDOVER_TO_HUMAN = "handover_to_human"


@dataclass
class DialogueContext:
    """对话上下文"""
    user_id: str
    session_id: str
    current_state: DialogueState = DialogueState.INITIAL
    collected_info: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict] = field(default_factory=list)
    current_intent: Optional[ServiceIntent] = None
    last_update: datetime = field(default_factory=datetime.now)


@dataclass
class SupportResponse:
    """售后响应"""
    response_text: str
    dialogue_state: DialogueState
    intent: ServiceIntent
    collected_info: Dict[str, Any] = field(default_factory=dict)
    action_required: Optional[Dict[str, Any]] = None
    case_created: bool = False


class CustomerSupportExecutor:
    """售后客服Agent执行器"""

    def __init__(self):
        """初始化执行器"""
        self._sessions: Dict[str, DialogueContext] = {}

    async def execute(
        self,
        user_input: str,
        user_id: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> SupportResponse:
        """执行售后客服处理流程"""

        # 获取或创建会话
        if not session_id:
            session_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        dialogue_ctx = self._get_or_create_session(user_id, session_id)

        # 第一步：意图分类
        intent_result = await self._classify_intent(
            user_input,
            dialogue_ctx
        )

        # 在多轮对话中，如果已有意图且当前意图不明确，保持原有意图
        structured_intent = intent_result.get("structured", {})
        primary_intent = structured_intent.get("primary_intent", "unknown")

        # 如果当前有未完成的任务，且新意图是未知或订单查询，保持原有意图
        if (dialogue_ctx.current_state != DialogueState.INITIAL and
            dialogue_ctx.current_state != DialogueState.TASK_COMPLETED and
            dialogue_ctx.current_intent and
            dialogue_ctx.current_intent != ServiceIntent.UNKNOWN and
            primary_intent in ["unknown", "order_query"]):
            # 保持原有意图
            pass
        elif primary_intent != "unknown":
            # 更新为新意图
            dialogue_ctx.current_intent = ServiceIntent(primary_intent)

        # 第二步：信息收集
        info_result = await self._collect_information(
            user_input,
            dialogue_ctx,
            intent_result
        )

        # 第三步：业务处理
        process_result = await self._process_request(
            dialogue_ctx,
            intent_result,
            info_result
        )

        # 第四步：生成响应
        response = self._generate_response(
            dialogue_ctx,
            intent_result,
            process_result
        )

        # 更新对话历史
        self._update_conversation_history(dialogue_ctx, user_input, response)

        return response

    async def _classify_intent(
        self,
        user_input: str,
        dialogue_ctx: DialogueContext
    ) -> Dict[str, Any]:
        """分类用户意图"""

        from examples.ecommerce.support.skills.intent_classification.executor import execute as intent_execute

        result = intent_execute(
            llm=None,  # 规则引擎不需要LLM
            sub_task=user_input,
            context={
                "user_input": user_input,
                "conversation_history": dialogue_ctx.conversation_history
            }
        )

        # 同时保存根级别的文本和structured数据
        return {
            "structured": result["structured"],
            "text": result.get("text", "")
        }

    async def _collect_information(
        self,
        user_input: str,
        dialogue_ctx: DialogueContext,
        intent_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """收集必要信息"""

        entities = intent_result.get("structured", {}).get("extracted_entities", {})
        required_info = intent_result.get("structured", {}).get("required_info", [])

        # 更新收集到的信息
        for key, value in entities.items():
            if value:
                dialogue_ctx.collected_info[key] = value

        # 确定对话状态和意图
        state_str = intent_result.get("structured", {}).get("dialogue_state", "information_gathering")

        # 如果已经有意图且不是初始状态，保持原有意图
        if dialogue_ctx.current_intent and dialogue_ctx.current_intent != ServiceIntent.UNKNOWN:
            # 保持原有意图，只更新状态
            dialogue_ctx.current_state = DialogueState(state_str)
        else:
            # 首次设置意图
            primary_intent = intent_result.get("structured", {}).get("primary_intent", "unknown")
            dialogue_ctx.current_intent = ServiceIntent(primary_intent)
            dialogue_ctx.current_state = DialogueState(state_str)

        return {
            "collected_info": dialogue_ctx.collected_info,
            "missing_info": required_info,
            "state": state_str
        }

    async def _process_request(
        self,
        dialogue_ctx: DialogueContext,
        intent_result: Dict[str, Any],
        info_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理业务请求"""

        # 使用对话上下文中的意图，而不是新识别的意图
        intent = dialogue_ctx.current_intent or ServiceIntent.UNKNOWN
        missing_info = info_result.get("missing_info", [])

        # 如果信息不完整，返回等待状态
        if missing_info:
            return {
                "status": "awaiting_info",
                "missing_info": missing_info
            }

        # 根据意图执行相应处理
        if intent == ServiceIntent.ORDER_QUERY:
            return await self._process_order_query(dialogue_ctx)
        elif intent == ServiceIntent.LOGISTICS_QUERY:
            return await self._process_logistics_query(dialogue_ctx)
        elif intent == ServiceIntent.RETURN_REQUEST:
            return await self._process_return_request(dialogue_ctx)
        elif intent == ServiceIntent.EXCHANGE_REQUEST:
            return await self._process_exchange_request(dialogue_ctx)
        elif intent == ServiceIntent.POLICY_INQUIRY:
            return await self._process_policy_inquiry(dialogue_ctx)
        else:
            return {
                "status": "unknown_intent",
                "message": "抱歉，我暂时不理解您的需求，请换个说法或联系人工客服。"
            }

    async def _process_order_query(self, dialogue_ctx: DialogueContext) -> Dict[str, Any]:
        """处理订单查询"""

        from examples.ecommerce.support.skills.order_query.executor import execute as order_execute

        order_id = dialogue_ctx.collected_info.get("order_id")
        query_type = "by_order_id" if order_id else "by_recent"

        result = order_execute(
            llm=None,
            sub_task="查询订单",
            context={
                "user_id": dialogue_ctx.user_id,
                "query_type": query_type,
                "order_id": order_id,
                "limit": 5
            }
        )

        return {
            "status": "success",
            "data": result["structured"],
            "text": result["text"]
        }

    async def _process_logistics_query(self, dialogue_ctx: DialogueContext) -> Dict[str, Any]:
        """处理物流查询"""

        # 物流查询实际上是订单查询的一种特殊形式
        order_result = await self._process_order_query(dialogue_ctx)

        if order_result["status"] == "success":
            orders = order_result["data"].get("orders", [])
            if orders and orders[0].get("logistics"):
                logistics = orders[0]["logistics"]
                text = f"**物流信息**\n\n"
                text += f"物流公司：{logistics['company']}\n"
                text += f"运单号：{logistics['tracking_no']}\n"
                text += f"最新动态：{logistics.get('latest_update', '暂无')}\n"
                if logistics.get('estimated_delivery'):
                    text += f"预计送达：{logistics['estimated_delivery']}\n"

                order_result["text"] = text

        return order_result

    async def _process_return_request(self, dialogue_ctx: DialogueContext) -> Dict[str, Any]:
        """处理退货申请"""

        # 第一步：验证政策
        from examples.ecommerce.support.skills.policy_validation.executor import execute as policy_execute

        order_id = dialogue_ctx.collected_info.get("order_id")
        reason = dialogue_ctx.collected_info.get("return_reason", "not_like")

        validation_result = policy_execute(
            llm=None,
            sub_task="验证退货政策",
            context={
                "order_id": order_id,
                "service_type": "return",
                "reason": reason
            }
        )

        validation = validation_result["structured"]

        # 如果符合条件，创建退货单
        if validation.get("eligible"):
            case_result = await self._create_return_case(dialogue_ctx, validation)

            return {
                "status": "success",
                "case_created": True,
                "case_info": case_result,
                "validation": validation,
                "text": validation_result["text"] + "\n\n" + case_result.get("text", "")
            }
        else:
            return {
                "status": "not_eligible",
                "validation": validation,
                "text": validation_result["text"]
            }

    async def _process_exchange_request(self, dialogue_ctx: DialogueContext) -> Dict[str, Any]:
        """处理换货申请"""

        # 换货流程与退货类似
        from examples.ecommerce.support.skills.policy_validation.executor import execute as policy_execute

        order_id = dialogue_ctx.collected_info.get("order_id")
        reason = dialogue_ctx.collected_info.get("return_reason", "not_like")

        validation_result = policy_execute(
            llm=None,
            sub_task="验证换货政策",
            context={
                "order_id": order_id,
                "service_type": "exchange",
                "reason": reason
            }
        )

        validation = validation_result["structured"]

        if validation.get("eligible"):
            case_result = await self._create_exchange_case(dialogue_ctx, validation)

            return {
                "status": "success",
                "case_created": True,
                "case_info": case_result,
                "validation": validation,
                "text": validation_result["text"] + "\n\n" + case_result.get("text", "")
            }
        else:
            return {
                "status": "not_eligible",
                "validation": validation,
                "text": validation_result["text"]
            }

    async def _process_policy_inquiry(self, dialogue_ctx: DialogueContext) -> Dict[str, Any]:
        """处理政策咨询"""

        # 简化的政策咨询响应
        text = """关于售后政策：

**退货政策：**
- 普通商品支持7天无理由退货
- 质量问题支持15天退货
- 定制商品、鲜活易腐等特殊商品不支持退货

**运费政策：**
- 质量问题、发错货：卖家承担运费
- 不喜欢、尺寸不合适：买家承担运费

**退款时效：**
- 退货签收后3-5个工作日原路退款
- 具体到账时间取决于银行处理速度

还有什么具体问题需要了解吗？"""

        return {
            "status": "success",
            "text": text
        }

    async def _create_return_case(
        self,
        dialogue_ctx: DialogueContext,
        validation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建退货工单"""

        case_id = f"RT{datetime.now().strftime('%Y%m%d%H%M%S')}"

        order_id = dialogue_ctx.collected_info.get("order_id")
        reason = dialogue_ctx.collected_info.get("return_reason", "not_like")

        # 获取订单信息
        from examples.ecommerce.support.skills.order_query.executor import MOCK_ORDERS
        # MOCK_ORDERS 是字典格式
        order = MOCK_ORDERS.get(order_id)

        if not order:
            return {"error": "订单不存在"}

        # 生成退货地址
        return_address = {
            "recipient": "售后部",
            "phone": "400-xxx-xxxx",
            "address": "广东省深圳市xxx区xxx路xxx号"
        }

        # 计算截止日期
        time_limit = validation.get("validation_results", {}).get("time_limit", {})
        deadline = time_limit.get("deadline", "3天后")

        text = f"""
**退货申请已创建**

退货单号：{case_id}

请按以下步骤操作：
1. 打包商品及所有配件
2. 使用顺丰/京东寄回以下地址：
   收件人：{return_address['recipient']}
   电话：{return_address['phone']}
   地址：{return_address['address']}
3. 保留运费凭证
4. 等待退款（卖家签收后3-5个工作日）

请在 {deadline} 前寄出商品。"""

        return {
            "case_id": case_id,
            "case_type": "return",
            "status": "created",
            "return_address": return_address,
            "deadline": deadline,
            "text": text
        }

    async def _create_exchange_case(
        self,
        dialogue_ctx: DialogueContext,
        validation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建换货工单"""

        case_id = f"EX{datetime.now().strftime('%Y%m%d%H%M%S')}"

        text = f"""
**换货申请已创建**

换货单号：{case_id}

接下来请：
1. 选择您想要的换货商品（颜色、尺寸等）
2. 确认换货地址
3. 寄回原商品

我们的客服会尽快与您联系确认换货详情。"""

        return {
            "case_id": case_id,
            "case_type": "exchange",
            "status": "created",
            "text": text
        }

    def _generate_response(
        self,
        dialogue_ctx: DialogueContext,
        intent_result: Dict[str, Any],
        process_result: Dict[str, Any]
    ) -> SupportResponse:
        """生成响应"""

        # 从意图分类结果获取初始文本
        intent_text = intent_result.get("text", "")

        # 如果处理成功，使用处理结果的文本
        if process_result.get("status") == "success":
            response_text = process_result.get("text", intent_text)
        elif process_result.get("status") == "awaiting_info":
            response_text = intent_text
        else:
            response_text = process_result.get("text", intent_text)

        return SupportResponse(
            response_text=response_text,
            dialogue_state=dialogue_ctx.current_state,
            intent=dialogue_ctx.current_intent or ServiceIntent.UNKNOWN,
            collected_info=dialogue_ctx.collected_info,
            action_required=process_result.get("action_required"),
            case_created=process_result.get("case_created", False)
        )

    def _get_or_create_session(self, user_id: str, session_id: str) -> DialogueContext:
        """获取或创建对话会话"""

        key = f"{user_id}:{session_id}"

        if key not in self._sessions:
            self._sessions[key] = DialogueContext(
                user_id=user_id,
                session_id=session_id
            )

        return self._sessions[key]

    def _update_conversation_history(
        self,
        dialogue_ctx: DialogueContext,
        user_input: str,
        response: SupportResponse
    ):
        """更新对话历史"""

        dialogue_ctx.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "agent_response": response.response_text,
            "intent": response.intent.value,
            "state": response.dialogue_state.value
        })

        dialogue_ctx.last_update = datetime.now()

    def clear_session(self, user_id: str, session_id: str):
        """清除会话"""

        key = f"{user_id}:{session_id}"
        if key in self._sessions:
            del self._sessions[key]

    def get_session_info(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""

        key = f"{user_id}:{session_id}"
        if key in self._sessions:
            ctx = self._sessions[key]
            return {
                "user_id": ctx.user_id,
                "session_id": ctx.session_id,
                "current_state": ctx.current_state.value,
                "current_intent": ctx.current_intent.value if ctx.current_intent else None,
                "collected_info": ctx.collected_info,
                "conversation_count": len(ctx.conversation_history),
                "last_update": ctx.last_update.isoformat()
            }
        return None
