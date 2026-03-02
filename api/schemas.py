"""API 请求/响应模型"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== 租户相关 ====================

class LLMConfig(BaseModel):
    """LLM 配置"""
    provider: str = "anthropic"
    model: str = "glm-4.7"
    api_key: str
    base_url: Optional[str] = None


class TenantCreateRequest(BaseModel):
    """创建租户请求"""
    name: str
    llm_config: Optional[LLMConfig] = None
    skill_whitelist: Optional[List[str]] = None
    rate_limit: Optional[Dict[str, int]] = None
    custom_tools: Optional[List[str]] = None


class TenantResponse(BaseModel):
    """租户响应"""
    tenant_id: str
    name: str
    api_key: str
    llm_config: LLMConfig
    skill_whitelist: List[str]
    rate_limit: Dict[str, int]
    is_active: bool
    created_at: str


# ==================== 对话相关 ====================

class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., description="用户消息")
    user_id: str = Field(..., description="用户 ID")
    session_id: Optional[str] = Field(None, description="会话 ID，首次可为空")
    stream: bool = Field(False, description="是否流式输出")
    context: Optional[Dict[str, Any]] = Field(None, description="额外上下文")


class ChatResponse(BaseModel):
    """对话响应"""
    response: str
    session_id: str
    success: bool
    metrics: Optional[Dict[str, Any]] = None


# ==================== 技能相关 ====================

class SkillUploadRequest(BaseModel):
    """上传技能请求"""
    tenant_id: str
    skill_name: str
    files: Dict[str, str] = Field(..., description="技能文件，key 为文件名")
    description: Optional[str] = None
    triggers: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class SkillResponse(BaseModel):
    """技能响应"""
    skill_id: str
    tenant_id: str
    name: str
    description: str
    triggers: List[str]
    tags: List[str]
    is_active: bool


# ==================== 会话相关 ====================

class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str
    tenant_id: str
    user_id: str
    created_at: str
    last_active: str


class SessionHistoryResponse(BaseModel):
    """会话历史响应"""
    session_id: str
    messages: List[Dict[str, Any]]
    total: int


# ==================== 工具相关 ====================

class ToolRegisterRequest(BaseModel):
    """注册工具请求"""
    tenant_id: str
    tool: Dict[str, Any]


class ToolResponse(BaseModel):
    """工具响应"""
    name: str
    description: str
    category: str


# ==================== 指标相关 ====================

class MetricsResponse(BaseModel):
    """指标响应"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    total_tokens_used: int
    active_sessions: int


# ==================== 健康检查 ====================

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    timestamp: str
    database: str
    redis: str
