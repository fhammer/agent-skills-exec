"""Shared TypedDict schemas for context data structures.

This module defines the data contracts used between Skills.
"""

from typing import TypedDict, List, Optional, Dict, Any


# ─── Parse Report Skill Schemas ───

class IndicatorResult(TypedDict):
    """Single indicator result from parse_report."""
    name: str
    value: float
    unit: str
    status: str  # "normal" | "high" | "low"
    deviation_percent: float
    ref_low: Optional[float]
    ref_high: Optional[float]


class BasicInfoResult(TypedDict):
    """Basic information from parse_report."""
    bmi: Dict[str, Any]
    blood_pressure: Dict[str, Any]


class ParseReportStructured(TypedDict):
    """Structured output from parse_report skill."""
    basic_info: BasicInfoResult
    indicators: List[IndicatorResult]
    summary: Dict[str, Any]


class ParseReportOutput(TypedDict):
    """Full output from parse_report skill."""
    structured: ParseReportStructured
    text: str
    metadata: Dict[str, Any]


# ─── Assess Risk Skill Schemas ───

class RiskFactor(TypedDict):
    """A risk factor."""
    factor: str
    description: str


class DimensionRisk(TypedDict):
    """Risk assessment for one dimension."""
    score: int
    level: str  # "low" | "medium" | "high"
    factors: List[str]


class AssessRiskStructured(TypedDict):
    """Structured output from assess_risk skill."""
    risk_scores: Dict[str, DimensionRisk]
    overall_risk: Dict[str, Any]


class AssessRiskOutput(TypedDict):
    """Full output from assess_risk skill."""
    structured: AssessRiskStructured
    text: str
    metadata: Dict[str, Any]


# ─── Generate Advice Skill Schemas ───

class AdviceItem(TypedDict):
    """A single advice item."""
    category: str
    priority: str  # "critical" | "important" | "suggested"
    content: str


class FollowupPlan(TypedDict):
    """Follow-up plan."""
    timing: str
    items: List[str]
    note: str


class GenerateAdviceStructured(TypedDict):
    """Structured output from generate_advice skill."""
    advice_items: List[AdviceItem]
    followup_plan: FollowupPlan


class GenerateAdviceOutput(TypedDict):
    """Full output from generate_advice skill."""
    structured: GenerateAdviceStructured
    text: str
    metadata: Dict[str, Any]


# ─── General Execution Context Schema ───

class ExecutionContext(TypedDict):
    """Context passed to skill execution."""
    sub_task: str
    user_input: str
    previous_results: Dict[str, Any]
    conversation_history: List[Dict[str, str]]
    available_tools: List[str]


# ─── Execution Plan Schema ───

class PlanStep(TypedDict):
    """A single step in execution plan."""
    skill: str
    sub_task: str
    confidence: float
    depends_on: List[str]


class ExecutionPlan(TypedDict):
    """Full execution plan."""
    intent: str
    steps: List[PlanStep]
    estimated_tokens: int


# ─── Skill Execution Result Schema ───

class SkillExecutionResult(TypedDict):
    """Result of skill execution."""
    skill_name: str
    sub_task: str
    success: bool
    structured: Optional[Dict[str, Any]]
    text: str
    error: Optional[str]
    execution_time_ms: float
    tokens_used: int
