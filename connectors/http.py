"""
HTTP API 连接器

支持 RESTful API 调用，支持多种认证方式。
"""

import asyncio
import time
import json
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import logging

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

from connectors.base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorType,
    ConnectorHealthStatus,
    HealthCheckResult,
)

logger = logging.getLogger(__name__)


class AuthType(Enum):
    """认证类型"""
    NONE = "none"
    BEARER = "bearer"
    API_KEY = "api_key"
    BASIC = "basic"
    OAUTH2 = "oauth2"


class HttpConnector(BaseConnector):
    """
    HTTP API 连接器

    支持多种认证方式和请求方法。
    """

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._session: Optional[aiohttp.ClientSession] = None
        self._base_url = config.connection_params.get("base_url", "")
        self._auth_config = config.connection_params.get("auth", {})
        self._auth_type = AuthType(self._auth_config.get("type", "none"))

    async def connect(self) -> bool:
        """建立 HTTP 连接（创建会话）"""
        if not HAS_AIOHTTP:
            raise ImportError("需要安装 aiohttp: pip install aiohttp")

        try:
            # 配置超时
            timeout = aiohttp.ClientTimeout(
                total=self.config.read_timeout,
                connect=self.config.connect_timeout,
            )

            # 配置连接器
            connector = aiohttp.TCPConnector(
                limit=self.config.pool_size,
                ssl=self.config.ssl_verify if self.config.ssl_enabled else False,
            )

            # 创建会话
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
            )

            self._connection = self._session
            self._health_status = ConnectorHealthStatus.HEALTHY
            self._stats.total_connections += 1
            self._stats.active_connections += 1
            logger.info(f"HTTP 连接器创建成功: {self.config.name} -> {self._base_url}")
            return True

        except Exception as e:
            logger.error(f"HTTP 连接器创建失败: {e}")
            self._health_status = ConnectorHealthStatus.UNHEALTHY
            self._stats.failed_connections += 1
            self._stats.last_error = str(e)
            return False

    async def disconnect(self) -> bool:
        """关闭 HTTP 连接"""
        try:
            if self._session and not self._session.closed:
                await self._session.close()

            self._connection = None
            self._session = None
            self._health_status = ConnectorHealthStatus.UNKNOWN
            self._stats.active_connections -= 1
            logger.info(f"HTTP 连接器已关闭: {self.config.name}")
            return True

        except Exception as e:
            logger.error(f"关闭 HTTP 连接器失败: {e}")
            return False

    async def health_check(self) -> HealthCheckResult:
        """健康检查"""
        start_time = time.time()

        try:
            # 尝试调用健康检查端点
            health_path = self.config.connection_params.get("health_check_path", "/health")
            await self.get(health_path)

            latency_ms = (time.time() - start_time) * 1000
            self._health_status = ConnectorHealthStatus.HEALTHY

            return HealthCheckResult(
                status=ConnectorHealthStatus.HEALTHY,
                message=f"HTTP API 连接正常: {self._base_url}",
                latency_ms=latency_ms,
                details={"base_url": self._base_url, "auth_type": self._auth_type.value},
            )

        except Exception as e:
            self._health_status = ConnectorHealthStatus.UNHEALTHY
            return HealthCheckResult(
                status=ConnectorHealthStatus.UNHEALTHY,
                message=f"健康检查失败: {str(e)}",
                details={"base_url": self._base_url, "error": str(e)},
            )

    # ==================== HTTP 方法 ====================

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        GET 请求

        Args:
            path: 请求路径
            params: 查询参数
            headers: 请求头

        Returns:
            响应数据
        """
        return await self._request("GET", path, params=params, headers=headers)

    async def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        POST 请求

        Args:
            path: 请求路径
            data: 表单数据
            json: JSON 数据
            headers: 请求头

        Returns:
            响应数据
        """
        return await self._request("POST", path, data=data, json=json, headers=headers)

    async def put(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        PUT 请求

        Args:
            path: 请求路径
            data: 表单数据
            json: JSON 数据
            headers: 请求头

        Returns:
            响应数据
        """
        return await self._request("PUT", path, data=data, json=json, headers=headers)

    async def patch(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        PATCH 请求

        Args:
            path: 请求路径
            data: 表单数据
            json: JSON 数据
            headers: 请求头

        Returns:
            响应数据
        """
        return await self._request("PATCH", path, data=data, json=json, headers=headers)

    async def delete(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        DELETE 请求

        Args:
            path: 请求路径
            params: 查询参数
            headers: 请求头

        Returns:
            响应数据
        """
        return await self._request("DELETE", path, params=params, headers=headers)

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        执行 HTTP 请求

        Args:
            method: 请求方法
            path: 请求路径
            params: 查询参数
            data: 表单数据
            json: JSON 数据
            headers: 请求头

        Returns:
            响应数据
        """
        url = self._build_url(path)
        request_headers = self._build_headers(headers)

        start_time = time.time()

        try:
            async with self._session.request(
                method,
                url,
                params=params,
                data=data,
                json=json,
                headers=request_headers,
            ) as response:
                # 更新统计
                latency_ms = (time.time() - start_time) * 1000
                self._update_latency_stats(latency_ms)

                # 解析响应
                response.raise_for_status()

                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return await response.json()
                else:
                    text = await response.text()
                    return {"data": text, "status": response.status}

        except aiohttp.ClientError as e:
            self._stats.failed_requests += 1
            self._stats.last_error = str(e)
            raise

    # ==================== 认证相关 ====================

    def _build_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """构建请求头"""
        headers = custom_headers or {}

        # 添加认证头
        if self._auth_type == AuthType.BEARER:
            token = self._auth_config.get("token", "")
            headers["Authorization"] = f"Bearer {token}"

        elif self._auth_type == AuthType.API_KEY:
            key_header = self._auth_config.get("key_header", "X-API-Key")
            key_value = self._auth_config.get("key_value", "")
            headers[key_header] = key_value

        elif self._auth_type == AuthType.BASIC:
            import base64
            username = self._auth_config.get("username", "")
            password = self._auth_config.get("password", "")
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"

        elif self._auth_type == AuthType.OAUTH2:
            access_token = self._auth_config.get("access_token", "")
            headers["Authorization"] = f"Bearer {access_token}"

        # 添加默认请求头
        headers.setdefault("User-Agent", "Agent-Framework-Connector/1.0")
        headers.setdefault("Accept", "application/json")

        return headers

    # ==================== 工具方法 ====================

    def _build_url(self, path: str) -> str:
        """构建完整 URL"""
        if not self._base_url:
            return path

        # 确保路径格式正确
        if not path.startswith("/"):
            path = f"/{path}"

        # 移除 base_url 末尾的斜杠
        base_url = self._base_url.rstrip("/")
        return f"{base_url}{path}"

    async def refresh_auth(self) -> bool:
        """刷新认证令牌（用于 OAuth2）"""
        if self._auth_type != AuthType.OAUTH2:
            return True

        try:
            token_url = self._auth_config.get("token_url", "")
            client_id = self._auth_config.get("client_id", "")
            client_secret = self._auth_config.get("client_secret", "")
            refresh_token = self._auth_config.get("refresh_token", "")

            async with self._session.post(
                token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
            ) as response:
                response.raise_for_status()
                token_data = await response.json()

                # 更新访问令牌
                self._auth_config["access_token"] = token_data.get("access_token")

                if "refresh_token" in token_data:
                    self._auth_config["refresh_token"] = token_data["refresh_token"]

                logger.info(f"OAuth2 令牌已刷新: {self.config.name}")
                return True

        except Exception as e:
            logger.error(f"刷新 OAuth2 令牌失败: {e}")
            self._stats.last_error = str(e)
            return False


# 便捷函数
async def create_http_connector(
    name: str,
    base_url: str,
    auth_type: str = "none",
    auth_config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> HttpConnector:
    """
    创建 HTTP 连接器

    Args:
        name: 连接器名称
        base_url: API 基础 URL
        auth_type: 认证类型 (none, bearer, api_key, basic, oauth2)
        auth_config: 认证配置
        **kwargs: 其他配置参数

    Returns:
        HTTP 连接器实例
    """
    config = ConnectorConfig(
        name=name,
        type=ConnectorType.HTTP,
        connection_params={
            "base_url": base_url,
            "auth": {
                "type": auth_type,
                **(auth_config or {}),
            },
            **kwargs,
        },
    )

    connector = HttpConnector(config)
    await connector.initialize()
    return connector
