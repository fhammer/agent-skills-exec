"""
订单售后客服 Agent - 数据模型定义

定义意图分类、订单查询、政策验证、工单创建等数据模型。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class SupportIntent(Enum):
    """售后客服意图类型"""
    ORDER_QUERY = "order_query"  # 订单查询
    RETURN_REQUEST = "return_request"  # 退货申请
    EXCHANGE_REQUEST = "exchange_request"  # 换货申请
    REFUND_INQUIRY = "refund_inquiry"  # 退款咨询
    POLICY_INQUIRY = "policy_inquiry"  # 政策咨询
    LOGISTICS_QUERY = "logistics_query"  # 物流查询
    COMPLAINT = "complaint"  # 投诉
    GENERAL_CHAT = "general_chat"  # 一般对话


class DialogueState(Enum):
    """对话状态"""
    INITIAL = "initial"
    AWAITING_ORDER_ID = "awaiting_order_id"  # 等待订单号
    AWAITING_REASON = "awaiting_reason"  # 等待原因
    AWAITING_EVIDENCE = "awaiting_evidence"  # 等待凭证
    POLICY_VALIDATION = "policy_validation"  # 政策验证中
    CASE_CREATION = "case_creation"  # 工单创建中
    TASK_COMPLETED = "task_completed"  # 任务完成
    HANDOVER_TO_HUMAN = "handover_to_human"  # 转人工


@dataclass
class IntentClassificationResult:
    """意图分类结果"""
    primary_intent: SupportIntent
    confidence: float
    secondary_intents: List[Dict[str, Any]] = field(default_factory=list)
    extracted_entities: Dict[str, Any] = field(default_factory=dict)
    required_info: List[str] = field(default_factory=list)
    dialogue_state: DialogueState = DialogueState.INITIAL
    text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "primary_intent": self.primary_intent.value,
            "confidence": self.confidence,
            "secondary_intents": self.secondary_intents,
            "extracted_entities": self.extracted_entities,
            "required_info": self.required_info,
            "dialogue_state": self.dialogue_state.value,
            "text": self.text
        }


@dataclass
class OrderItem:
    """订单商品"""
    product_id: str
    name: str
    quantity: int
    price: float
    image_url: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "quantity": self.quantity,
            "price": self.price,
            "image_url": self.image_url,
            "attributes": self.attributes
        }


@dataclass
class ShippingAddress:
    """收货地址"""
    name: str
    phone: str
    province: str
    city: str
    district: str
    address: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "phone": self.phone,
            "province": self.province,
            "city": self.city,
            "district": self.district,
            "address": self.address
        }


@dataclass
class LogisticsInfo:
    """物流信息"""
    company: str
    tracking_no: str
    status: str
    latest_update: str = ""
    estimated_delivery: str = ""
    tracks: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company": self.company,
            "tracking_no": self.tracking_no,
            "status": self.status,
            "latest_update": self.latest_update,
            "estimated_delivery": self.estimated_delivery,
            "tracks": self.tracks
        }


@dataclass
class Order:
    """订单"""
    order_id: str
    status: str
    status_text: str
    create_time: str
    pay_time: Optional[str] = None
    ship_time: Optional[str] = None
    receive_time: Optional[str] = None
    total_amount: float = 0.0
    items: List[OrderItem] = field(default_factory=list)
    shipping_address: Optional[ShippingAddress] = None
    logistics: Optional[LogisticsInfo] = None

    def is_returnable(self) -> bool:
        """是否可退货"""
        returnable_statuses = ["shipped", "received"]
        return self.status in returnable_statuses

    def days_since_ship(self) -> int:
        """发货天数"""
        from datetime import datetime
        if not self.ship_time:
            return 0
        try:
            ship_dt = datetime.fromisoformat(self.ship_time)
            return (datetime.now() - ship_dt).days
        except:
            return 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "status": self.status,
            "status_text": self.status_text,
            "create_time": self.create_time,
            "pay_time": self.pay_time,
            "ship_time": self.ship_time,
            "receive_time": self.receive_time,
            "total_amount": self.total_amount,
            "items": [item.to_dict() for item in self.items],
            "shipping_address": self.shipping_address.to_dict() if self.shipping_address else None,
            "logistics": self.logistics.to_dict() if self.logistics else None
        }


@dataclass
class OrderQueryResult:
    """订单查询结果"""
    query_type: str
    total_orders: int
    orders: List[Order]
    text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_type": self.query_type,
            "total_orders": self.total_orders,
            "orders": [order.to_dict() for order in self.orders],
            "text": self.text
        }


@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "reason": self.reason
        }


@dataclass
class FeePolicy:
    """费用政策"""
    responsible_party: str  # seller, buyer, platform
    reason: str
    buyer_cost: float = 0.0
    compensation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "responsible_party": self.responsible_party,
            "reason": self.reason,
            "buyer_cost": self.buyer_cost,
            "compensation": self.compensation
        }


@dataclass
class PolicyValidationResult:
    """政策验证结果"""
    eligible: bool
    order_id: str
    service_type: str  # return, exchange, refund
    validation_results: Dict[str, Any] = field(default_factory=dict)
    fee_policy: Optional[FeePolicy] = None
    next_steps: List[str] = field(default_factory=list)
    text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "eligible": self.eligible,
            "order_id": self.order_id,
            "service_type": self.service_type,
            "validation_results": self.validation_results,
            "fee_policy": self.fee_policy.to_dict() if self.fee_policy else None,
            "next_steps": self.next_steps,
            "text": self.text
        }


@dataclass
class ReturnAddress:
    """退货地址"""
    recipient: str
    phone: str
    address: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recipient": self.recipient,
            "phone": self.phone,
            "address": self.address
        }


@dataclass
class ReturnInfo:
    """退货信息"""
    reason: str
    reason_detail: str
    return_address: ReturnAddress
    deadline: str
    return_method: str = "self_ship"
    shipping_fee_policy: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reason": self.reason,
            "reason_detail": self.reason_detail,
            "return_address": self.return_address.to_dict(),
            "deadline": self.deadline,
            "return_method": self.return_method,
            "shipping_fee_policy": self.shipping_fee_policy
        }


@dataclass
class RefundInfo:
    """退款信息"""
    refund_amount: float
    refund_method: str
    estimated_refund_time: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "refund_amount": self.refund_amount,
            "refund_method": self.refund_method,
            "estimated_refund_time": self.estimated_refund_time
        }


@dataclass
class CaseCreationResult:
    """工单创建结果"""
    case_id: str
    case_type: str
    status: str
    created_at: str
    order_info: Dict[str, Any]
    return_info: Optional[ReturnInfo] = None
    refund_info: Optional[RefundInfo] = None
    next_steps: List[Dict[str, Any]] = field(default_factory=list)
    text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "case_type": self.case_type,
            "status": self.status,
            "created_at": self.created_at,
            "order_info": self.order_info,
            "return_info": self.return_info.to_dict() if self.return_info else None,
            "refund_info": self.refund_info.to_dict() if self.refund_info else None,
            "next_steps": self.next_steps,
            "text": self.text
        }


@dataclass
class SupportResult:
    """客服处理结果"""
    session_id: str
    user_id: Optional[str]
    intent: SupportIntent
    dialogue_state: DialogueState
    response_text: str
    order: Optional[Order] = None
    policy_validation: Optional[PolicyValidationResult] = None
    case: Optional[CaseCreationResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "intent": self.intent.value,
            "dialogue_state": self.dialogue_state.value,
            "response_text": self.response_text,
            "order": self.order.to_dict() if self.order else None,
            "policy_validation": self.policy_validation.to_dict() if self.policy_validation else None,
            "case": self.case.to_dict() if self.case else None,
            "metadata": self.metadata
        }
