"""需求分析 Skill 数据模型"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class PriceRange(BaseModel):
    """价格区间"""
    min: int = Field(default=0, description="最低价格")
    max: int = Field(default=99999, description="最高价格")


class Constraints(BaseModel):
    """需求约束"""
    price_range: Optional[PriceRange] = None
    brands: List[str] = Field(default_factory=list, description="品牌偏好列表")
    use_case: Optional[str] = None
    special_requirements: List[str] = Field(default_factory=list)


class DemandAnalysisResult(BaseModel):
    """需求分析结果"""
    intent: str = Field(description="意图类型")
    category: Optional[str] = Field(None, description="商品类别")
    constraints: Constraints = Field(default_factory=Constraints)
    missing_info: List[str] = Field(default_factory=list, description="缺失信息列表")


class DemandAnalysisResponse(BaseModel):
    """需求分析响应"""
    structured: DemandAnalysisResult
    text: str = Field(description="回复文本")
