"""意图分类 Skill 执行器

识别用户意图（查询订单、申请退货、咨询政策等）
"""

import re
from typing import Dict, Any, List, Optional

try:
    from agent.llm_base import LLMProvider as LLMBase
except ImportError:
    LLMBase = Any

from examples.ecommerce.support.schema import SupportIntent, DialogueState


# 意图关键词映射
INTENT_KEYWORDS = {
    SupportIntent.ORDER_QUERY: [
        "查订单", "查询订单", "订单", "我的订单", "最近订单",
        "订单状态", "订单详情"
    ],
    SupportIntent.RETURN_REQUEST: [
        "退货", "退掉", "退款退货", "申请退货",
        "不想要了", "想退"
    ],
    SupportIntent.EXCHANGE_REQUEST: [
        "换货", "换个", "换一个", "申请换货",
        "想换", "更换"
    ],
    SupportIntent.REFUND_INQUIRY: [
        "退款", "什么时候退款", "退款进度",
        "钱退了吗", "退款到账"
    ],
    SupportIntent.POLICY_INQUIRY: [
        "退货政策", "能退吗", "怎么退", "退货条件",
        "几天退货", "退货要运费吗", "退货运费"
    ],
    SupportIntent.LOGISTICS_QUERY: [
        "物流", "快递", "发货", "配送", "运单",
        "快递到哪", "物流信息", "配送进度"
    ],
    SupportIntent.COMPLAINT: [
        "投诉", "质量问题", "有问题", "坏了",
        "不满意", "差评", "客服态度"
    ]
}

# 订单号正则模式
ORDER_ID_PATTERNS = [
    r'\d{14,20}',  # 14-20位数字
    r'202\d{10,}',  # 202开头的订单号
    r'ORD\d+',  # ORD开头的订单号
]

# 原因关键词
REASON_KEYWORDS = {
    "quality_issue": ["质量问题", "坏了", "损坏", "故障", "不工作", "有问题"],
    "not_as_described": ["和描述不符", "不一样", "不是", "发错"],
    "no_longer_needed": ["不想要", "不想买了", "改变主意"],
    "preference_issue": ["不喜欢", "不合适", "颜色", "尺码", "大小"],
    "price_issue": ["贵了", "降价", "价格"],
}


def execute(llm: LLMBase, sub_task: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """执行意图分类"""

    user_input = context.get("user_input", sub_task)
    conversation_history = context.get("conversation_history", [])

    # 识别主要意图
    primary_intent, confidence = _detect_intent(user_input)

    # 识别次要意图
    secondary_intents = _detect_secondary_intents(user_input, primary_intent)

    # 提取实体
    extracted_entities = _extract_entities(user_input)

    # 确定所需信息
    required_info = _determine_required_info(primary_intent, extracted_entities)

    # 确定对话状态
    dialogue_state = _determine_dialogue_state(primary_intent, required_info)

    # 生成回复文本
    text = _generate_response(primary_intent, required_info, extracted_entities)

    return {
        "structured": {
            "primary_intent": primary_intent.value,
            "confidence": confidence,
            "secondary_intents": secondary_intents,
            "extracted_entities": extracted_entities,
            "required_info": required_info,
            "dialogue_state": dialogue_state.value
        },
        "text": text
    }


def _detect_intent(text: str) -> tuple[SupportIntent, float]:
    """检测主要意图"""
    text_lower = text.lower()

    # 按优先级检测意图
    priority_order = [
        SupportIntent.RETURN_REQUEST,
        SupportIntent.EXCHANGE_REQUEST,
        SupportIntent.REFUND_INQUIRY,
        SupportIntent.LOGISTICS_QUERY,
        SupportIntent.ORDER_QUERY,
        SupportIntent.POLICY_INQUIRY,
        SupportIntent.COMPLAINT,
    ]

    for intent in priority_order:
        keywords = INTENT_KEYWORDS[intent]
        for keyword in keywords:
            if keyword in text:
                # 计算置信度
                confidence = _calculate_intent_confidence(text, intent)
                return intent, confidence

    # 默认为一般对话
    return SupportIntent.GENERAL_CHAT, 0.3


def _calculate_intent_confidence(text: str, intent: SupportIntent) -> float:
    """计算意图置信度"""
    confidence = 0.7  # 基础置信度

    keywords = INTENT_KEYWORDS[intent]
    match_count = sum(1 for kw in keywords if kw in text)

    # 关键词匹配越多，置信度越高
    confidence += min(match_count - 1, 3) * 0.1

    # 包含具体数字（如订单号），提高置信度
    if re.search(r'\d{10,}', text):
        confidence += 0.1

    return min(confidence, 1.0)


def _detect_secondary_intents(text: str, primary_intent: SupportIntent) -> List[Dict[str, Any]]:
    """检测次要意图"""
    secondary = []

    for intent, keywords in INTENT_KEYWORDS.items():
        if intent == primary_intent:
            continue

        for keyword in keywords:
            if keyword in text:
                secondary.append({
                    "intent": intent.value,
                    "confidence": 0.5
                })
                break

    return secondary[:3]  # 最多返回3个次要意图


def _extract_entities(text: str) -> Dict[str, Any]:
    """提取实体信息"""
    entities = {}

    # 提取订单号
    order_id = _extract_order_id(text)
    if order_id:
        entities["order_id"] = order_id

    # 提取原因
    reason = _extract_reason(text)
    if reason:
        entities["reason"] = reason

    # 提取时间相关
    if "最近" in text or "latest" in text.lower():
        entities["time_range"] = "recent"

    return entities


def _extract_order_id(text: str) -> Optional[str]:
    """提取订单号"""
    for pattern in ORDER_ID_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def _extract_reason(text: str) -> Optional[str]:
    """提取原因"""
    for reason_type, keywords in REASON_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return reason_type
    return None


def _determine_required_info(intent: SupportIntent, entities: Dict[str, Any]) -> List[str]:
    """确定所需信息"""
    required = []

    match intent:
        case SupportIntent.ORDER_QUERY:
            if "order_id" not in entities:
                required.append("order_id")
        case SupportIntent.RETURN_REQUEST | SupportIntent.EXCHANGE_REQUEST:
            if "order_id" not in entities:
                required.append("order_id")
            if "reason" not in entities:
                required.append("reason")
        case SupportIntent.LOGISTICS_QUERY:
            if "order_id" not in entities:
                required.append("order_id")
        case _:
            pass

    return required


def _determine_dialogue_state(intent: SupportIntent, required_info: List[str]) -> DialogueState:
    """确定对话状态"""
    if not required_info:
        match intent:
            case SupportIntent.RETURN_REQUEST | SupportIntent.EXCHANGE_REQUEST:
                return DialogueState.POLICY_VALIDATION
            case SupportIntent.ORDER_QUERY | SupportIntent.LOGISTICS_QUERY:
                return DialogueState.TASK_COMPLETED
            case _:
                return DialogueState.INITIAL

    # 根据缺失信息确定状态
    if "order_id" in required_info:
        return DialogueState.AWAITING_ORDER_ID
    if "reason" in required_info:
        return DialogueState.AWAITING_REASON

    return DialogueState.INITIAL


def _generate_response(intent: SupportIntent, required_info: List[str], entities: Dict[str, Any]) -> str:
    """生成回复文本"""
    if not required_info:
        return _get_completion_response(intent)

    if "order_id" in required_info:
        return "好的，请问您要查询或处理哪个订单？您可以提供订单号，或者我帮您查询最近的订单。"

    if "reason" in required_info:
        order_id = entities.get("order_id", "")
        return f"收到，订单 {order_id}。请问您退货/换货的原因是什么？"

    return "请问还有什么可以帮您的吗？"


def _get_completion_response(intent: SupportIntent) -> str:
    """获取完成响应"""
    responses = {
        SupportIntent.ORDER_QUERY: "好的，我来帮您查询订单信息。",
        SupportIntent.RETURN_REQUEST: "收到，我来帮您处理退货申请。",
        SupportIntent.EXCHANGE_REQUEST: "收到，我来帮您处理换货申请。",
        SupportIntent.REFUND_INQUIRY: "好的，我来帮您查询退款信息。",
        SupportIntent.LOGISTICS_QUERY: "好的，我来帮您查询物流信息。",
        SupportIntent.POLICY_INQUIRY: "关于退换货政策，我来为您说明。",
        SupportIntent.COMPLAINT: "收到您的问题，我来帮您处理。",
        SupportIntent.GENERAL_CHAT: "您好，我是智能客服，有什么可以帮您的吗？"
    }
    return responses.get(intent, "您好，有什么可以帮您的吗？")
