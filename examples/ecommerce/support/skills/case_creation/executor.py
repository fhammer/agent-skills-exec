"""工单创建 Skill 执行器

创建退货单、换货单、投诉工单
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random

try:
    from agent.llm_base import LLMProvider as LLMBase
except ImportError:
    LLMBase = Any

from examples.ecommerce.support.schema import (
    ReturnAddress, ReturnInfo, RefundInfo, CaseCreationResult
)


# 退货仓库地址
RETURN_WAREHOUSES = {
    "default": {
        "recipient": "售后服务中心",
        "phone": "400-888-8888",
        "address": "广东省深圳市南山区科技园xxx路xxx号"
    },
    "electronics": {
        "recipient": "电子产品售后部",
        "phone": "400-999-9999",
        "address": "广东省深圳市龙华区xxx路xxx号"
    }
}


def execute(llm: LLMBase, sub_task: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """执行工单创建"""

    order_id = context.get("order_id")
    service_type = context.get("service_type", "return")
    reason = context.get("reason", "")
    reason_detail = context.get("reason_detail", "")
    evidence = context.get("evidence", [])

    if not order_id:
        return {
            "structured": {
                "case_id": "",
                "status": "failed"
            },
            "text": "请提供订单号以创建售后工单。"
        }

    return _create_case(order_id, service_type, reason, reason_detail, evidence)


def _create_case(
    order_id: str,
    service_type: str,
    reason: str,
    reason_detail: str,
    evidence: List[str]
) -> Dict[str, Any]:
    """创建工单"""

    # 获取订单信息
    order_info = _get_order_info(order_id)

    if not order_info:
        return {
            "structured": {
                "case_id": "",
                "status": "failed",
                "order_info": {}
            },
            "text": f"未找到订单 {order_id}，无法创建工单。"
        }

    # 生成工单号
    case_id = _generate_case_id(service_type)

    # 创建时间
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 计算退货截止日期（3天内）
    deadline = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")

    # 构建退货信息
    return_info = ReturnInfo(
        reason=reason,
        reason_detail=reason_detail or _get_reason_text(reason),
        return_address=_get_return_address(order_info.get("category", "")),
        deadline=deadline,
        return_method="self_ship",
        shipping_fee_policy=_get_shipping_fee_policy(reason)
    )

    # 构建退款信息
    refund_info = RefundInfo(
        refund_amount=order_info.get("amount", 0),
        refund_method="original",
        estimated_refund_time="退货签收后3-5个工作日"
    )

    # 生成下一步操作
    next_steps = _generate_case_steps(return_info, refund_info)

    # 生成回复文本
    text = _generate_case_text(
        case_id, service_type, order_info, return_info, refund_info
    )

    return {
        "structured": {
            "case_id": case_id,
            "case_type": service_type,
            "status": "created",
            "created_at": created_at,
            "order_info": order_info,
            "return_info": return_info.to_dict(),
            "refund_info": refund_info.to_dict(),
            "next_steps": next_steps
        },
        "text": text
    }


def _get_order_info(order_id: str) -> Optional[Dict[str, Any]]:
    """获取订单信息"""
    mock_orders = {
        "20240228123456": {
            "order_id": "20240228123456",
            "product_id": "p_001",
            "product_name": "Redmi K70",
            "category": "手机",
            "amount": 2499.00,
            "status": "shipped"
        },
        "20240225098765": {
            "order_id": "20240225098765",
            "product_id": "e_002",
            "product_name": "华为FreeBuds 4i",
            "category": "耳机",
            "amount": 499.00,
            "status": "received"
        }
    }
    return mock_orders.get(order_id)


def _generate_case_id(service_type: str) -> str:
    """生成工单号"""
    prefix_map = {
        "return": "RT",
        "exchange": "EX",
        "refund": "RF",
        "complaint": "CP"
    }
    prefix = prefix_map.get(service_type, "CS")
    timestamp = datetime.now().strftime("%Y%m%d")
    random_num = random.randint(1000, 9999)
    return f"{prefix}{timestamp}{random_num}"


def _get_return_address(category: str) -> ReturnAddress:
    """获取退货地址"""
    # 根据商品类别选择仓库
    warehouse_key = "electronics" if category in ["手机", "电脑", "平板"] else "default"
    warehouse = RETURN_WAREHOUSES.get(warehouse_key, RETURN_WAREHOUSES["default"])

    return ReturnAddress(
        recipient=warehouse["recipient"],
        phone=warehouse["phone"],
        address=warehouse["address"]
    )


def _get_reason_text(reason: str) -> str:
    """获取原因文本"""
    reason_map = {
        "quality_issue": "质量问题",
        "damaged": "商品损坏",
        "defective": "功能故障",
        "not_as_described": "与描述不符",
        "no_longer_needed": "不想要了",
        "preference_issue": "不喜欢/不合适",
    }
    return reason_map.get(reason, "其他原因")


def _get_shipping_fee_policy(reason: str) -> str:
    """获取运费政策"""
    quality_reasons = ["quality_issue", "damaged", "defective", "not_as_described"]

    if reason in quality_reasons:
        return "运费由卖家承担，需提供运费凭证"
    else:
        return "运费由买家承担"


def _generate_case_steps(return_info: ReturnInfo, refund_info: RefundInfo) -> List[Dict[str, Any]]:
    """生成工单步骤"""
    return [
        {
            "step": 1,
            "action": "打包商品",
            "detail": "将商品及所有配件、发票完整打包"
        },
        {
            "step": 2,
            "action": "寄回商品",
            "detail": f"使用顺丰/京东寄到退货地址，{return_info.shipping_fee_policy}"
        },
        {
            "step": 3,
            "action": "等待退款",
            "detail": f"卖家签收后{refund_info.estimated_refund_time}原路退款"
        }
    ]


def _generate_case_text(
    case_id: str,
    service_type: str,
    order_info: Dict[str, Any],
    return_info: ReturnInfo,
    refund_info: RefundInfo
) -> str:
    """生成工单文本"""

    service_type_map = {
        "return": "退货",
        "exchange": "换货",
        "refund": "退款",
        "complaint": "投诉"
    }
    service_name = service_type_map.get(service_type, "售后")

    lines = [
        f"已为您创建{service_name}申请，{service_name}单号：{case_id}",
        "",
        "请在3天内将商品寄回以下地址：",
        f"收件人：{return_info.return_address.recipient}",
        f"地址：{return_info.return_address.address}",
        f"电话：{return_info.return_address.phone}",
        "",
        f"退货原因：{return_info.reason_detail}",
    ]

    if return_info.shipping_fee_policy:
        lines.append(f"运费政策：{return_info.shipping_fee_policy}")

    lines.extend([
        "",
        f"退款金额：¥{refund_info.refund_amount:.2f}",
        f"退款方式：原路退回",
        f"预计退款时间：{refund_info.estimated_refund_time}",
        "",
        "如有任何问题，可以随时联系我。"
    ])

    return "\n".join(lines)
