"""Shared utility functions for health metrics calculations."""

from typing import Dict, Tuple, Optional


def calculate_bmi(height_cm: float, weight_kg: float) -> float:
    """Calculate Body Mass Index (BMI).

    Args:
        height_cm: Height in centimeters
        weight_kg: Weight in kilograms

    Returns:
        BMI value
    """
    if height_cm <= 0:
        raise ValueError("Height must be positive")
    if weight_kg <= 0:
        raise ValueError("Weight must be positive")

    height_m = height_cm / 100
    return weight_kg / (height_m * height_m)


def classify_bmi(bmi: float) -> str:
    """Classify BMI into category.

    Args:
        bmi: BMI value

    Returns:
        Category string
    """
    if bmi < 18.5:
        return "偏瘦"
    elif bmi < 24:
        return "正常"
    elif bmi < 28:
        return "超重"
    else:
        return "肥胖"


def classify_blood_pressure(sbp: int, dbp: int) -> str:
    """Classify blood pressure reading.

    Args:
        sbp: Systolic blood pressure (mmHg)
        dbp: Diastolic blood pressure (mmHg)

    Returns:
        Category string
    """
    if sbp >= 180 or dbp >= 110:
        return "高血压3级"
    elif sbp >= 160 or dbp >= 100:
        return "高血压2级"
    elif sbp >= 140 or dbp >= 90:
        return "高血压1级"
    elif sbp >= 130 or dbp >= 85:
        return "正常高值"
    elif sbp >= 90 and dbp >= 60:
        return "正常"
    else:
        return "低血压"


def check_indicator(
    value: float,
    ref_low: Optional[float] = None,
    ref_high: Optional[float] = None
) -> Tuple[str, float]:
    """Check if indicator value is within reference range.

    Args:
        value: Indicator value
        ref_low: Lower reference limit
        ref_high: Upper reference limit

    Returns:
        Tuple of (status, deviation_percent)
        - status: "normal", "high", or "low"
        - deviation_percent: Deviation from reference range
    """
    if ref_low is not None and value < ref_low:
        status = "low"
        if ref_low != 0:
            deviation_percent = ((ref_low - value) / ref_low) * 100
        else:
            deviation_percent = 0
    elif ref_high is not None and value > ref_high:
        status = "high"
        if ref_high != 0:
            deviation_percent = ((value - ref_high) / ref_high) * 100
        else:
            deviation_percent = 0
    else:
        status = "normal"
        deviation_percent = 0

    return status, round(deviation_percent, 1)


def format_indicator_result(
    name: str,
    value: float,
    unit: str,
    status: str,
    ref_low: Optional[float] = None,
    ref_high: Optional[float] = None
) -> str:
    """Format indicator result for display.

    Args:
        name: Indicator name
        value: Indicator value
        unit: Unit of measurement
        status: Status (normal/high/low)
        ref_low: Lower reference limit
        ref_high: Upper reference limit

    Returns:
        Formatted string
    """
    result = f"{name}: {value}{unit}"

    if status == "normal":
        result += " ✓"
    else:
        ref_range = ""
        if ref_low is not None and ref_high is not None:
            ref_range = f" (参考: {ref_low}-{ref_high})"
        elif ref_low is not None:
            ref_range = f" (参考: >{ref_low})"
        elif ref_high is not None:
            ref_range = f" (参考: <{ref_high})"

        if status == "high":
            result += f" ↑偏高{ref_range}"
        else:
            result += f" ↓偏低{ref_range}"

    return result
