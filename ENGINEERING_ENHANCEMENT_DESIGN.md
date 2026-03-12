# 工程化详细设计文档

## 1. 数据持久化

### 1.1 当前问题

**内存存储租户数据**：
```python
# 当前实现 - 内存存储（问题严重）
class TenantManager:
    def __init__(self):
        self._tenants = {}  # 内存存储！
        self._tenant_by_api_key = {}  # 内存存储！
```

**问题**：
1. 服务重启数据丢失
2. 不支持多实例部署
3. 内存泄漏风险
4. 无法实现水平扩展

### 1.2 工业级设计方案

**核心架构**：

```python
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
import asyncio
import json
from datetime import datetime
from contextlib import asynccontextmanager

# ==================== 数据模型 ====================

class TenantStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    PENDING = "pending"

@dataclass
class TenantConfig:
    """租户配置"""
    max_tokens_per_day: int = 100000
    max_requests_per_minute: int = 100
    allowed_models: List[str] = None
    allowed_skills: List[str] = None
    custom_settings: Dict[str, Any] = None

    def __post_init__(self):
        if self.allowed_models is None:
            self.allowed_models = ["gpt-3.5-turbo", "gpt-4"]
        if self.allowed_skills is None:
            self.allowed_skills = ["*"]  # 允许所有
        if self.custom_settings is None:
            self.custom_settings = {}

@dataclass
class Tenant:
    """租户模型"""
    tenant_id: str
    name: str
    status: TenantStatus
    config: TenantConfig
    api_key_hash: str  # 存储API Key的哈希，不是明文
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于数据库存储）"""
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "status": self.status.value,
            "config": json.dumps({
                "max_tokens_per_day": self.config.max_tokens_per_day,
                "max_requests_per_minute": self.config.max_requests_per_minute,
                "allowed_models": self.config.allowed_models,
                "allowed_skills": self.config.allowed_skills,
                "custom_settings": self.config.custom_settings
            }),
            "api_key_hash": self.api_key_hash,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "metadata": json.dumps(self.metadata)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tenant":
        """从字典创建（用于数据库读取）"""
        config_data = json.loads(data["config"])
        config = TenantConfig(
            max_tokens_per_day=config_data.get("max_tokens_per_day", 100000),
            max_requests_per_minute=config_data.get("max_requests_per_minute", 100),
            allowed_models=config_data.get("allowed_models", ["gpt-3.5-turbo", "gpt-4"]),
            allowed_skills=config_data.get("allowed_skills", ["*"]),
            custom_settings=config_data.get("custom_settings", {})
        )

        return cls(
            tenant_id=data["tenant_id"],
            name=data["name"],
            status=TenantStatus(data["status"]),
            config=config,
            api_key_hash=data["api_key_hash"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            last_accessed_at=datetime.fromisoformat(data["last_accessed_at"]) if data.get("last_accessed_at") else None,
            metadata=json.loads(data["metadata"]) if data.get("metadata") else {}
        )


# ==================== 数据库层 ====================

class DatabaseConnection(ABC):
    """数据库连接抽象基类"""

    @abstractmethod
    async def connect(self) -> None:
        """连接数据库"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass

    @abstractmethod
    async def execute(self, query: str, params: Optional[Dict] = None) -> Any:
        """执行查询"""
        pass

    @abstractmethod
    async def fetch_one(self, query: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """获取一条记录"""
        pass

    @abstractmethod
    async def fetch_many(self, query: str, params: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
        """获取多条记录"""
        pass


class PostgreSQLConnection(DatabaseConnection):
    """PostgreSQL连接实现"""

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 30
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout

        self._engine = None
        self._session_factory = None

    async def connect(self) -> None:
        """连接数据库"""
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker

        # 创建异步引擎
        database_url = f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

        self._engine = create_async_engine(
            database_url,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            echo=False  # 生产环境关闭SQL日志
        )

        # 创建会话工厂
        self._session_factory = sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # 测试连接
        async with self._engine.connect() as conn:
            await conn.execute("SELECT 1")

        logger.info(f"Connected to PostgreSQL at {self.host}:{self.port}/{self.database}")

    async def disconnect(self) -> None:
        """断开连接"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Disconnected from PostgreSQL")

    @asynccontextmanager
    async def session(self):
        """获取数据库会话（上下文管理器）"""
        if not self._session_factory:
            raise RuntimeError("Database not connected")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e

    async def execute(self, query: str, params: Optional[Dict] = None) -> Any:
        """执行查询"""
        async with self.session() as session:
            result = await session.execute(query, params or {})
            return result

    async def fetch_one(self, query: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """获取一条记录"""
        async with self.session() as session:
            result = await session.execute(query, params or {})
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            return None

    async def fetch_many(self, query: str, params: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
        """获取多条记录"""
        async with self.session() as session:
            result = await session.execute(query, params or {})
            rows = result.fetchmany(limit)
            return [dict(row._mapping) for row in rows]


# ==================== 仓储层 ====================

class TenantRepository:
    """租户仓储"""

    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def create(self, tenant: Tenant) -> Tenant:
        """创建租户"""
        query = """
            INSERT INTO tenants (
                tenant_id, name, status, config, api_key_hash,
                created_at, updated_at, metadata
            ) VALUES (
                :tenant_id, :name, :status, :config, :api_key_hash,
                :created_at, :updated_at, :metadata
            )
            RETURNING *
        """

        result = await self._db.fetch_one(query, tenant.to_dict())
        return Tenant.from_dict(result)

    async def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """根据ID获取租户"""
        query = "SELECT * FROM tenants WHERE tenant_id = :tenant_id"
        result = await self._db.fetch_one(query, {"tenant_id": tenant_id})

        if result:
            return Tenant.from_dict(result)
        return None

    async def get_by_api_key_hash(self, api_key_hash: str) -> Optional[Tenant]:
        """根据API Key哈希获取租户"""
        query = "SELECT * FROM tenants WHERE api_key_hash = :api_key_hash"
        result = await self._db.fetch_one(query, {"api_key_hash": api_key_hash})

        if result:
            return Tenant.from_dict(result)
        return None

    async def update(self, tenant: Tenant) -> Tenant:
        """更新租户"""
        tenant.updated_at = datetime.utcnow()

        query = """
            UPDATE tenants SET
                name = :name,
                status = :status,
                config = :config,
                api_key_hash = :api_key_hash,
                updated_at = :updated_at,
                last_accessed_at = :last_accessed_at,
                metadata = :metadata
            WHERE tenant_id = :tenant_id
            RETURNING *
        """

        result = await self._db.fetch_one(query, tenant.to_dict())
        return Tenant.from_dict(result)

    async def delete(self, tenant_id: str) -> bool:
        """删除租户"""
        query = "DELETE FROM tenants WHERE tenant_id = :tenant_id"
        result = await self._db.execute(query, {"tenant_id": tenant_id})
        return result.rowcount > 0

    async def list_all(
        self,
        status: Optional[TenantStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Tenant], int]:
        """列出所有租户"""
        # 构建查询条件
        conditions = []
        params = {}

        if status:
            conditions.append("status = :status")
            params["status"] = status.value

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        # 查询总数
        count_query = f"SELECT COUNT(*) as total FROM tenants{where_clause}"
        count_result = await self._db.fetch_one(count_query, params)
        total = count_result["total"]

        # 查询列表
        query = f"""
            SELECT * FROM tenants
            {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """
        params["limit"] = limit
        params["offset"] = offset

        results = await self._db.fetch_many(query, params, limit)
        tenants = [Tenant.from_dict(row) for row in results]

        return tenants, total


# ==================== 服务层 ====================

class TenantService:
    """租户服务"""

    def __init__(
        self,
        repository: TenantRepository,
        cache: Optional[Any] = None,
        event_publisher: Optional[Any] = None
    ):
        self._repository = repository
        self._cache = cache
        self._event_publisher = event_publisher

    async def create_tenant(
        self,
        name: str,
        config: Optional[TenantConfig] = None
    ) -> Tenant:
        """创建租户"""
        import secrets
        import hashlib

        # 生成租户ID
        tenant_id = f"tenant_{secrets.token_hex(8)}"

        # 生成API Key并哈希存储
        api_key = secrets.token_urlsafe(32)
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # 创建租户对象
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            status=TenantStatus.ACTIVE,
            config=config or TenantConfig(),
            api_key_hash=api_key_hash,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={
                "api_key_plain": api_key,  # 仅在创建时返回一次
                "created_by": "system"
            }
        )

        # 保存到数据库
        created_tenant = await self._repository.create(tenant)

        # 发布事件
        if self._event_publisher:
            await self._event_publisher.publish(
                "tenant.created",
                {
                    "tenant_id": tenant_id,
                    "name": name,
                    "created_at": created_tenant.created_at.isoformat()
                }
            )

        # 缓存
        if self._cache:
            await self._cache.set(
                f"tenant:{tenant_id}",
                created_tenant,
                ttl=3600
            )

        return created_tenant

    async def get_tenant_by_api_key(self, api_key: str) -> Optional[Tenant]:
        """根据API Key获取租户"""
        import hashlib

        # 计算API Key的哈希
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # 先从缓存查找
        if self._cache:
            tenant = await self._cache.get(f"tenant:api_key:{api_key_hash}")
            if tenant:
                return tenant

        # 从数据库查找
        tenant = await self._repository.get_by_api_key_hash(api_key_hash)

        # 缓存
        if tenant and self._cache:
            await self._cache.set(
                f"tenant:api_key:{api_key_hash}",
                tenant,
                ttl=3600
            )

        return tenant

    async def validate_tenant_access(
        self,
        tenant_id: str,
        required_permission: str
    ) -> Tuple[bool, Optional[str]]:
        """验证租户访问权限

        Returns:
            (是否允许, 错误信息)
        """
        # 获取租户
        tenant = await self._repository.get_by_id(tenant_id)
        if not tenant:
            return False, f"Tenant {tenant_id} not found"

        # 检查状态
        if tenant.status == TenantStatus.SUSPENDED:
            return False, "Tenant is suspended"
        if tenant.status == TenantStatus.CANCELLED:
            return False, "Tenant is cancelled"

        # 检查权限（简化实现）
        # 实际实现应该更复杂，检查具体的权限

        return True, None


# ==================== 缓存层 ====================

class CacheProvider(ABC):
    """缓存提供者基类"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """设置缓存值"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """删除缓存值"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass


class RedisCacheProvider(CacheProvider):
    """Redis缓存提供者"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        pool_size: int = 10
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.pool_size = pool_size
        self._redis = None

    async def connect(self) -> None:
        """连接Redis"""
        import redis.asyncio as redis

        self._redis = await redis.from_url(
            f"redis://{self.host}:{self.port}/{self.db}",
            password=self.password,
            max_connections=self.pool_size
        )

        # 测试连接
        await self._redis.ping()
        logger.info(f"Connected to Redis at {self.host}:{self.port}/{self.db}")

    async def disconnect(self) -> None:
        """断开连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Disconnected from Redis")

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self._redis:
            raise RuntimeError("Redis not connected")

        value = await self._redis.get(key)
        if value is None:
            return None

        # 尝试解析JSON
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value.decode('utf-8') if isinstance(value, bytes) else value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """设置缓存值"""
        if not self._redis:
            raise RuntimeError("Redis not connected")

        # 序列化为JSON
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        elif not isinstance(value, (str, bytes)):
            value = str(value)

        await self._redis.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        """删除缓存值"""
        if not self._redis:
            raise RuntimeError("Redis not connected")

        await self._redis.delete(key)

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._redis:
            raise RuntimeError("Redis not connected")

        return await self._redis.exists(key) > 0


# ==================== 数据库表结构 ====================

"""
-- 租户表
CREATE TABLE tenants (
    tenant_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    config JSONB NOT NULL DEFAULT '{}',
    api_key_hash VARCHAR(128) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- 索引
CREATE INDEX idx_tenants_status ON tenants(status);
CREATE INDEX idx_tenants_api_key_hash ON tenants(api_key_hash);
CREATE INDEX idx_tenants_created_at ON tenants(created_at);

-- 会话表（用于存储对话上下文）
CREATE TABLE sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL,
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_sessions_tenant_id ON sessions(tenant_id);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- 审计日志表
CREATE TABLE audit_logs (
    log_id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) REFERENCES tenants(tenant_id) ON DELETE SET NULL,
    session_id VARCHAR(64) REFERENCES sessions(session_id) ON DELETE SET NULL,
    action VARCHAR(64) NOT NULL,
    resource_type VARCHAR(64) NOT NULL,
    resource_id VARCHAR(64),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_tenant_id ON audit_logs(tenant_id);
CREATE INDEX idx_audit_logs_session_id ON audit_logs(session_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);

-- 配置使用分区表（如果数据量大）
-- CREATE TABLE audit_logs_2024_01 PARTITION OF audit_logs
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- 更新触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
"""

# ==================== 使用示例 ====================

async def main():
    # 1. 创建数据库连接
    db = PostgreSQLConnection(
        host="localhost",
        port=5432,
        database="agent_skills",
        user="postgres",
        password="password",
        pool_size=10
    )

    # 2. 创建缓存连接
    cache = RedisCacheProvider(
        host="localhost",
        port=6379,
        db=0
    )

    # 3. 连接数据库和缓存
    await db.connect()
    await cache.connect()

    try:
        # 4. 创建仓储
        tenant_repo = TenantRepository(db)

        # 5. 创建服务
        tenant_service = TenantService(
            repository=tenant_repo,
            cache=cache
        )

        # 6. 创建租户
        tenant = await tenant_service.create_tenant(
            name="Example Corp",
            config=TenantConfig(
                max_tokens_per_day=1000000,
                max_requests_per_minute=1000,
                allowed_models=["gpt-4", "gpt-3.5-turbo"],
                allowed_skills=["*"]
            )
        )

        print(f"Created tenant: {tenant.tenant_id}")
        print(f"API Key: {tenant.metadata.get('api_key_plain')}")  # 仅在创建时返回

        # 7. 验证租户访问
        is_allowed, error = await tenant_service.validate_tenant_access(
            tenant.tenant_id,
            "read"
        )
        print(f"Access allowed: {is_allowed}, Error: {error}")

    finally:
        # 8. 断开连接
        await db.disconnect()
        await cache.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
