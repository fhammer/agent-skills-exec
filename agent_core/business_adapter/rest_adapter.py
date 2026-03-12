"""
REST API 适配器 - 提供REST API集成支持
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import json


class HTTPMethod(Enum):
    """HTTP方法"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class AuthType(Enum):
    """认证类型"""
    NONE = "none"
    API_KEY = "api_key"
    BASIC = "basic"
    BEARER = "bearer"
    OAUTH2 = "oauth2"


@dataclass
class RESTConfig:
    """REST配置"""
    base_url: str
    auth_type: AuthType = AuthType.NONE
    api_key: Optional[str] = None
    api_key_header: str = "X-API-Key"
    username: Optional[str] = None
    password: Optional[str] = None
    bearer_token: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    default_headers: Dict[str, str] = field(default_factory=dict)
    verify_ssl: bool = True


class RESTAdapter:
    """REST API适配器"""

    def __init__(self, config: RESTConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None

    async def connect(self):
        """连接"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                base_url=self.config.base_url,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                connector=aiohttp.TCPConnector(verify_ssl=self.config.verify_ssl)
            )
        return True

    async def disconnect(self):
        """断开连接"""
        if self._session and not self._session.closed:
            await self._session.close()
        return True

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """GET请求"""
        return await self._request(HTTPMethod.GET, path, params=params, headers=headers)

    async def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """POST请求"""
        return await self._request(
            HTTPMethod.POST,
            path,
            data=data,
            json_data=json_data,
            headers=headers
        )

    async def put(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """PUT请求"""
        return await self._request(
            HTTPMethod.PUT,
            path,
            data=data,
            json_data=json_data,
            headers=headers
        )

    async def delete(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None
    ):
        """DELETE请求"""
        return await self._request(HTTPMethod.DELETE, path, headers=headers)

    async def patch(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """PATCH请求"""
        return await self._request(
            HTTPMethod.PATCH,
            path,
            data=data,
            json_data=json_data,
            headers=headers
        )

    async def _request(
        self,
        method: HTTPMethod,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """执行请求"""
        await self.connect()

        # 合并请求头
        request_headers = self.config.default_headers.copy()
        if headers:
            request_headers.update(headers)

        # 添加认证
        self._add_auth_headers(request_headers)

        # 执行请求（带重试）
        last_exception = None
        for attempt in range(self.config.max_retries):
            try:
                async with self._session.request(
                    method=method.value,
                    url=path,
                    params=params,
                    data=data,
                    json=json_data,
                    headers=request_headers
                ) as response:
                    result_data = await self._parse_response(response)
                    return {
                        "success": response.status >= 200 and response.status < 300,
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "data": result_data
                    }

            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    raise

        raise last_exception or Exception("Request failed")

    def _add_auth_headers(self, headers: Dict[str, str]):
        """添加认证头"""
        if self.config.auth_type == AuthType.API_KEY:
            headers[self.config.api_key_header] = self.config.api_key
        elif self.config.auth_type == AuthType.BASIC:
            import base64
            credentials = f"{self.config.username}:{self.config.password}".encode()
            encoded = base64.b64encode(credentials).decode()
            headers["Authorization"] = f"Basic {encoded}"
        elif self.config.auth_type == AuthType.BEARER:
            headers["Authorization"] = f"Bearer {self.config.bearer_token}"

    async def _parse_response(self, response: aiohttp.ClientResponse):
        """解析响应"""
        content_type = response.headers.get("Content-Type", "")

        if "application/json" in content_type:
            try:
                return await response.json()
            except:
                pass

        try:
            return await response.text()
        except:
            return None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()
