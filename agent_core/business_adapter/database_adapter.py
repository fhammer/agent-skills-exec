"""
数据库适配器 - 提供各种数据库的集成支持
"""

import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod


class DatabaseType(Enum):
    """数据库类型"""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"
    REDIS = "redis"


@dataclass
class DatabaseConfig:
    """数据库配置"""
    database_type: DatabaseType
    connection_string: str
    host: str = ""
    port: int = 0
    database: str = ""
    username: str = ""
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    echo: bool = False
    auto_commit: bool = True
    connect_args: Dict[str, Any] = None


class DatabaseAdapter(ABC):
    """数据库适配器抽象基类"""

    @abstractmethod
    async def connect(self) -> bool:
        """连接"""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """断开连接"""
        pass

    @abstractmethod
    async def execute(self, query: str, params: Dict[str, Any] = None) -> Any:
        """执行查询"""
        pass

    @abstractmethod
    async def fetch_one(self, query: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """获取一条记录"""
        pass

    @abstractmethod
    async def fetch_all(self, query: str, params: Dict[str, Any] = None) -> List[Dict]:
        """获取多条记录"""
        pass

    @abstractmethod
    async def begin_transaction(self):
        """开始事务"""
        pass

    @abstractmethod
    async def commit_transaction(self):
        """提交事务"""
        pass

    @abstractmethod
    async def rollback_transaction(self):
        """回滚事务"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass


class SQLAdapter(DatabaseAdapter):
    """SQL数据库适配器"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._engine = None
        self._connection = None

    async def connect(self) -> bool:
        """连接"""
        try:
            if self._engine is None:
                if self.config.connection_string:
                    from sqlalchemy.ext.asyncio import create_async_engine
                    self._engine = create_async_engine(
                        self.config.connection_string,
                        pool_size=self.config.pool_size,
                        max_overflow=self.config.max_overflow,
                        pool_timeout=self.config.pool_timeout,
                        echo=self.config.echo
                    )

            if self._connection is None:
                self._connection = await self._engine.connect()

            return True
        except Exception as e:
            raise Exception(f"Failed to connect: {e}")

    async def disconnect(self) -> bool:
        """断开连接"""
        try:
            if self._connection:
                await self._connection.close()
            if self._engine:
                await self._engine.dispose()
            return True
        except Exception as e:
            raise Exception(f"Failed to disconnect: {e}")

    async def execute(self, query: str, params: Dict[str, Any] = None) -> Any:
        """执行查询"""
        try:
            if params is None:
                params = {}

            result = await self._connection.execute(text(query), params)

            if self.config.auto_commit:
                await self._connection.commit()

            return result.rowcount
        except Exception as e:
            raise Exception(f"Failed to execute query: {e}")

    async def fetch_one(self, query: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """获取一条记录"""
        try:
            if params is None:
                params = {}

            result = await self._connection.execute(text(query), params)
            row = result.fetchone()

            return dict(row) if row else None
        except Exception as e:
            raise Exception(f"Failed to fetch one: {e}")

    async def fetch_all(self, query: str, params: Dict[str, Any] = None) -> List[Dict]:
        """获取多条记录"""
        try:
            if params is None:
                params = {}

            result = await self._connection.execute(text(query), params)
            rows = result.fetchall()

            return [dict(row) for row in rows]
        except Exception as e:
            raise Exception(f"Failed to fetch all: {e}")

    async def begin_transaction(self):
        """开始事务"""
        try:
            return await self._connection.begin()
        except Exception as e:
            raise Exception(f"Failed to begin transaction: {e}")

    async def commit_transaction(self):
        """提交事务"""
        try:
            await self._connection.commit()
            return True
        except Exception as e:
            raise Exception(f"Failed to commit transaction: {e}")

    async def rollback_transaction(self):
        """回滚事务"""
        try:
            await self._connection.rollback()
            return True
        except Exception as e:
            raise Exception(f"Failed to rollback transaction: {e}")

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            query = "SELECT 1"
            await self.fetch_one(query)
            return True
        except Exception as e:
            return False


class MongoAdapter(DatabaseAdapter):
    """MongoDB适配器"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._client = None

    async def connect(self) -> bool:
        """连接"""
        try:
            import motor.motor_asyncio
            self._client = motor.motor_asyncio.AsyncIOMotorClient(self.config.connection_string)
            return True
        except Exception as e:
            raise Exception(f"Failed to connect: {e}")

    async def disconnect(self) -> bool:
        """断开连接"""
        if self._client:
            self._client.close()
            self._client = None
        return True

    async def execute(self, query: str, params: Dict[str, Any] = None) -> Any:
        """执行查询"""
        collection = self._client[self.config.database][query]
        if params.get("operation") == "insert_one":
            return await collection.insert_one(params.get("document"))
        elif params.get("operation") == "insert_many":
            return await collection.insert_many(params.get("documents"))
        elif params.get("operation") == "update_one":
            return await collection.update_one(params.get("filter"), params.get("update"))
        elif params.get("operation") == "update_many":
            return await collection.update_many(params.get("filter"), params.get("update"))
        elif params.get("operation") == "delete_one":
            return await collection.delete_one(params.get("filter"))
        elif params.get("operation") == "delete_many":
            return await collection.delete_many(params.get("filter"))
        return None

    async def fetch_one(self, query: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """获取一条记录"""
        collection = self._client[self.config.database][query]
        return await collection.find_one(params.get("filter", {}))

    async def fetch_all(self, query: str, params: Dict[str, Any] = None) -> List[Dict]:
        """获取多条记录"""
        collection = self._client[self.config.database][query]
        cursor = collection.find(params.get("filter", {}))
        results = []
        async for doc in cursor:
            results.append(doc)
        return results

    async def begin_transaction(self):
        """开始事务"""
        raise NotImplementedError("Transactions not supported")

    async def commit_transaction(self):
        """提交事务"""
        raise NotImplementedError("Transactions not supported")

    async def rollback_transaction(self):
        """回滚事务"""
        raise NotImplementedError("Transactions not supported")

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            await self._client.admin.command('ismaster')
            return True
        except Exception as e:
            return False


class RedisAdapter(DatabaseAdapter):
    """Redis适配器"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._connection = None

    async def connect(self) -> bool:
        """连接"""
        import redis.asyncio as redis
        self._connection = redis.Redis(
            host=self.config.host or 'localhost',
            port=self.config.port or 6379,
            db=self.config.database or 0,
            password=self.config.password
        )
        await self._connection.ping()
        return True

    async def disconnect(self) -> bool:
        """断开连接"""
        if self._connection:
            await self._connection.close()
        return True

    async def execute(self, query: str, params: Dict[str, Any] = None) -> Any:
        """执行命令"""
        return await self._connection.execute_command(query, *params.get("args", []))

    async def fetch_one(self, query: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """获取一个值"""
        return await self._connection.get(query)

    async def fetch_all(self, query: str, params: Dict[str, Any] = None) -> List[Dict]:
        """获取所有值"""
        raise NotImplementedError("Not applicable for Redis")

    async def begin_transaction(self):
        """开始事务"""
        raise NotImplementedError("Transactions not supported")

    async def commit_transaction(self):
        """提交事务"""
        raise NotImplementedError("Transactions not supported")

    async def rollback_transaction(self):
        """回滚事务"""
        raise NotImplementedError("Transactions not supported")

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            await self._connection.ping()
            return True
        except Exception as e:
            return False


# 工厂函数
def create_database_adapter(config: DatabaseConfig) -> DatabaseAdapter:
    """创建数据库适配器"""
    if config.database_type == DatabaseType.MYSQL:
        from sqlalchemy import text
        return SQLAdapter(config)
    elif config.database_type == DatabaseType.POSTGRESQL:
        from sqlalchemy import text
        return SQLAdapter(config)
    elif config.database_type == DatabaseType.SQLITE:
        from sqlalchemy import text
        return SQLAdapter(config)
    elif config.database_type == DatabaseType.MONGODB:
        return MongoAdapter(config)
    elif config.database_type == DatabaseType.REDIS:
        return RedisAdapter(config)
    else:
        raise ValueError(f"Unknown database type: {config.database_type}")
