"""政策验证 Skill 执行器

验证退换货政策、检查订单资格
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta

try:
    from agent.llm_base import LLMProvider as LLMBase
except ImportError:
    LLMBase = Any

from examples.ecommerce.support.schema import (
    ValidationResult, FeePolicy, PolicyValidationResult
)


# 退货政策配置
RETURN_POLICY_DAYS = 7  # 7天无理由退货

# 不可退货商品类别
NON_RETURNABLE_CATEGORIES = ["定制商品", "生鲜食品", "贴身用品", "虚拟商品"]

# 质量问题原因类型
QUALITY_ISSUE_REASONS = ["quality_issue", "damaged", "defective", "not_as_described"]


def execute(llm: LLMBase, sub_task: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """执行政策验证"""

    order_id = context.get("order_id")
    service_type = context.get("service_type", "return")
    reason = context.get("reason", "")

    if not order_id:
        return {
            "structured": {
                "eligible": False,
                "order_id": "",
                "service_type": service_type
            },
            "text": "请提供订单号以便验证退货政策。"
        }

    return _validate_policy(order_id, service_type, reason)


def _validate_policy(order_id: str, service_type: str, reason: str) -> Dict[str, Any]:
    """验证政策"""

    # 模拟获取订单信息
    order_info = _get_order_info(order_id)

    if not order_info:
        return {
            "structured": {
                "eligible": False,
                "order_id": order_id,
                "service_type": service_type,
                "validation_results": {
                    "order_exists": {"passed": False, "reason": "订单不存在"}
                }
            },
            "text": f"未找到订单 {order_id}，请检查订单号是否正确。"
        }

    # 执行各项验证
    validation_results = {}
    eligible = True

    # 1. 时间限制验证
    time_validation = _validate_time_limit(order_info)
    validation_results["time_limit"] = time_validation
    if not time_validation["passed"]:
        eligible = False

    # 2. 商品类别验证
    category_validation = _validate_product_category(order_info)
    validation_results["product_category"] = category_validation
    if not category_validation["passed"]:
        eligible = False

    # 3. 订单状态验证
    status_validation = _validate_order_status(order_info)
    validation_results["order_status"] = status_validation
    if not status_validation["passed"]:
        eligible = False

    # 4. 费用政策
    fee_policy = _determine_fee_policy(reason, eligible)

    # 5. 下一步操作
    next_steps = _generate_next_steps(service_type, eligible, fee_policy)

    # 生成回复文本
    text = _generate_validation_text(
        eligible, order_info, validation_results, fee_policy
    )

    return {
        "structured": {
            "eligible": eligible,
            "order_id": order_id,
            "service_type": service_type,
            "validation_results": validation_results,
            "fee_policy": fee_policy.to_dict(),
            "next_steps": next_steps
        },
        "text": text
    }


def _get_order_info(order_id: str) -> Optional[Dict[str, Any]]:
    """获取订单信息"""
    # 使用动态日期生成模拟数据
    NOW = datetime.now()
    RECENT_TIME = NOW - timedelta(days=2)  # 2天前，符合退货条件

    mock_orders = {
        "20240228123456": {
            "order_id": "20240228123456",
            "status": "shipped",
            "create_time": RECENT_TIME.strftime("%Y-%m-%d 10:30:00"),
            "ship_time": (RECENT_TIME + timedelta(hours=4)).strftime("%Y-%m-%d 14:20:00"),
            "category": "手机",
            "product_name": "Redmi K70",
            "amount": 2499.00
        },
        "20240225098765": {
            "order_id": "20240225098765",
            "status": "received",
            "create_time": (NOW - timedelta(days=5)).strftime("%Y-%m-%d 15:20:00"),
            "ship_time": (NOW - timedelta(days=5)).strftime("%Y-%m-%d 18:00:00"),
            "receive_time": (NOW - timedelta(days=3)).strftime("%Y-%m-%d 10:15:00"),
            "category": "耳机",
            "product_name": "华为FreeBuds 4i",
            "amount": 499.00
        }
    }
    return mock_orders.get(order_id)


def _validate_time_limit(order_info: Dict[str, Any]) -> Dict[str, Any]:
    """验证时间限制"""
    ship_time = order_info.get("ship_time")
    if not ship_time:
        return {
            "passed": False,
            "reason": "订单未发货，无法申请退货"
        }

    try:
        ship_date = datetime.fromisoformat(ship_time)
        days_since_ship = (datetime.now() - ship_date).days
        remaining_days = RETURN_POLICY_DAYS - days_since_ship

        if days_since_ship <= RETURN_POLICY_DAYS:
            return {
                "passed": True,
                "policy": f"{RETURN_POLICY_DAYS}天无理由退货",
                "order_date": ship_time.split()[0],
                "deadline": (ship_date + timedelta(days=RETURN_POLICY_DAYS)).strftime("%Y-%m-%d"),
                "remaining_days": remaining_days,
                "days_since_ship": days_since_ship
            }
        else:
            return {
                "passed": False,
                "reason": f"已超过{RETURN_POLICY_DAYS}天退货期限（已过{days_since_ship - RETURN_POLICY_DAYS}天）"
            }
    except:
        return {
            "passed": False,
            "reason": "无法计算退货期限"
        }


def _validate_product_category(order_info: Dict[str, Any]) -> Dict[str, Any]:
    """验证商品类别"""
    category = order_info.get("category", "")

    if category in NON_RETURNABLE_CATEGORIES:
        return {
            "passed": False,
            "reason": f"{category}不支持退货"
        }

    return {
        "passed": True,
        "category": category,
        "returnable": True
    }


def _validate_order_status(order_info: Dict[str, Any]) -> Dict[str, Any]:
    """验证订单状态"""
    status = order_info.get("status")

    returnable_statuses = ["shipped", "received"]

    if status in returnable_statuses:
        return {
            "passed": True,
            "current_status": status,
            "returnable": True
        }

    return {
        "passed": False,
        "reason": f"当前订单状态为 {status}，不支持退货"
    }


def _determine_fee_policy(reason: str, eligible: bool) -> FeePolicy:
    """确定费用政策"""
    if not eligible:
        return FeePolicy(
            responsible_party="none",
            reason="不符合退货条件",
            buyer_cost=0.0,
            compensation=""
        )

    # 判断是否质量问题
    is_quality_issue = reason in QUALITY_ISSUE_REASONS

    if is_quality_issue:
        return FeePolicy(
            responsible_party="seller",
            reason="质量问题",
            buyer_cost=0.0,
            compensation="运费卖家承担，需提供运费凭证"
        )
    else:
        return FeePolicy(
            responsible_party="buyer",
            reason="非质量问题（7天无理由退货）",
            buyer_cost=10.0,
            compensation="买家承担运费"
        )


def _generate_next_steps(service_type: str, eligible: bool, fee_policy: FeePolicy) -> list:
    """生成下一步操作"""
    if not eligible:
        return ["订单不符合退货条件", "如需人工审核，请联系客服"]

    steps = [
        "填写退货原因",
        "选择退货方式（上门取件/自行寄回）",
        "寄回商品并保留运费凭证"
    ]

    if fee_policy.responsible_party == "seller":
        steps.append("等待卖家签收后退款")

    return steps


def _generate_validation_text(
    eligible: bool,
    order_info: Dict[str, Any],
    validation_results: Dict[str, Any],
    fee_policy: FeePolicy
) -> str:
    """生成验证结果文本"""
    product_name = order_info.get("product_name", "")

    if not eligible:
        # 找出失败原因
        failed_checks = [
            name for name, result in validation_results.items()
            if not result.get("passed", False)
        ]

        if failed_checks:
            failed_result = validation_results[failed_checks[0]]
            reason = failed_result.get("reason", "不符合退货条件")
            return f"订单 {order_info['order_id']}（{product_name}）{reason}。"

    # 符合条件
    lines = [
        f"订单 {order_info['order_id']}（{product_name}）符合退货条件。",
    ]

    # 时间信息
    time_result = validation_results.get("time_limit", {})
    if time_result.get("passed"):
        lines.append(f"退货期限：{time_result.get('deadline')}截止（剩余{time_result.get('remaining_days')}天）")

    # 费用信息
    if fee_policy.responsible_party == "seller":
        lines.append("费用：由于是质量问题，运费由卖家承担")
    else:
        lines.append(f"费用：非质量问题退货，买家承担运费（约¥{fee_policy.buyer_cost}）")

    return "\n".join(lines)
