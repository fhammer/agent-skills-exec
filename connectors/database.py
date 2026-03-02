"""
数据库连接器

支持 PostgreSQL, MySQL, MongoDB 等数据库连接。
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union
from contextlib import asynccontextmanager
import logging

from connectors.base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorType,
    ConnectorHealthStatus,
    HealthCheckResult,
)

logger = logging.getLogger(__name__)


class DatabaseConnector(BaseConnector):
    """
    数据库连接器

    支持多种数据库类型的统一接口。
    """

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._db_type = config.connection_params.get("db_type", "postgresql")
        self._pool = None

    async def connect(self) -> bool:
        """建立数据库连接"""
        try:
            start_time = time.time()

            if self._db_type == "postgresql":
                return await self._connect_postgresql()
            elif self._db_type == "mysql":
                return await self._connect_mysql()
            elif self._db_type == "mongodb":
                return await self._connect_mongodb()
            elif self._db_type == "sqlite":
                return await self._connect_sqlite()
            else:
                raise ValueError(f"不支持的数据库类型: {self._db_type}")

        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            self._health_status = ConnectorHealthStatus.UNHEALTHY
            self._stats.failed_connections += 1
            self._stats.last_error = str(e)
            return False

    async def _connect_postgresql(self) -> bool:
        """连接 PostgreSQL"""
        try:
            import asyncpg
        except ImportError:
            raise ImportError("需要安装 asyncpg: pip install asyncpg")

        params = self.config.connection_params
        dsn = f"postgresql://{params.get('user', 'postgres')}:{params.get('password', '')}@{params.get('host', 'localhost')}:{params.get('port', 5432)}/{params.get('database', 'postgres')}"

        self._pool = await asyncpg.create_pool(
            dsn,
            min_size=1,
            max_size=self.config.pool_size,
            command_timeout=self.config.read_timeout,
        )

        self._connection = self._pool
        self._health_status = ConnectorHealthStatus.HEALTHY
        self._stats.total_connections += 1
        self._stats.active_connections += 1
        logger.info(f"PostgreSQL 连接成功: {self.config.name}")
        return True

    async def _connect_mysql(self) -> bool:
        """连接 MySQL"""
        try:
            import aiomysql
        except ImportError:
            raise ImportError("需要安装 aiomysql: pip install aiomysql")

        params = self.config.connection_params
        self._pool = await aiomysql.create_pool(
            host=params.get("host", "localhost"),
            port=params.get("port", 3306),
            user=params.get("user", "root"),
            password=params.get("password", ""),
            db=params.get("database", "test"),
            minsize=1,
            maxsize=self.config.pool_size,
            autocommit=False,
        )

        self._connection = self._pool
        self._health_status = ConnectorHealthStatus.HEALTHY
        self._stats.total_connections += 1
        self._stats.active_connections += 1
        logger.info(f"MySQL 连接成功: {self.config.name}")
        return True

    async def _connect_mongodb(self) -> bool:
        """连接 MongoDB"""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
        except ImportError:
            raise ImportError("需要安装 motor: pip install motor")

        params = self.config.connection_params
        connection_string = params.get(
            "connection_string",
            f"mongodb://{params.get('host', 'localhost')}:{params.get('port', 27017)}",
        )

        client = AsyncIOMotorClient(
            connection_string,
            maxPoolSize=self.config.pool_size,
            serverSelectionTimeoutMS=self.config.connect_timeout * 1000,
        )

        # 测试连接
        await client.admin.command("ping")

        self._connection = client
        self._health_status = ConnectorHealthStatus.HEALTHY
        self._stats.total_connections += 1
        self._stats.active_connections += 1
        logger.info(f"MongoDB 连接成功: {self.config.name}")
        return True

    async def _connect_sqlite(self) -> bool:
        """连接 SQLite"""
        try:
            import aiosqlite
        except ImportError:
            raise ImportError("需要安装 aiosqlite: pip install aiosqlite")

        db_path = self.config.connection_params.get("database", ":memory:")
        self._connection = await aiosqlite.connect(db_path)

        self._health_status = ConnectorHealthStatus.HEALTHY
        self._stats.total_connections += 1
        self._stats.active_connections += 1
        logger.info(f"SQLite 连接成功: {self.config.name}")
        return True

    async def disconnect(self) -> bool:
        """断开数据库连接"""
        try:
            if self._db_type == "sqlite":
                if self._connection:
                    await self._connection.close()
            elif self._db_type == "mongodb":
                if self._connection:
                    self._connection.close()
            else:
                if self._pool:
                    self._pool.close()
                    await self._pool.wait_closed()

            self._connection = None
            self._pool = None
            self._health_status = ConnectorHealthStatus.UNKNOWN
            self._stats.active_connections -= 1
            logger.info(f"数据库连接已断开: {self.config.name}")
            return True

        except Exception as e:
            logger.error(f"断开数据库连接失败: {e}")
            return False

    async def health_check(self) -> HealthCheckResult:
        """健康检查"""
        start_time = time.time()

        try:
            if self._db_type == "postgresql":
                await self._health_check_postgresql()
            elif self._db_type == "mysql":
                await self._health_check_mysql()
            elif self._db_type == "mongodb":
                await self._health_check_mongodb()
            elif self._db_type == "sqlite":
                await self._health_check_sqlite()

            latency_ms = (time.time() - start_time) * 1000
            self._health_status = ConnectorHealthStatus.HEALTHY

            return HealthCheckResult(
                status=ConnectorHealthStatus.HEALTHY,
                message=f"{self._db_type.upper()} 数据库连接正常",
                latency_ms=latency_ms,
                details={"db_type": self._db_type, "pool_size": self.config.pool_size},
            )

        except Exception as e:
            self._health_status = ConnectorHealthStatus.UNHEALTHY
            return HealthCheckResult(
                status=ConnectorHealthStatus.UNHEALTHY,
                message=f"健康检查失败: {str(e)}",
                details={"db_type": self._db_type, "error": str(e)},
            )

    async def _health_check_postgresql(self):
        """PostgreSQL 健康检查"""
        async with self._pool.acquire() as conn:
            await conn.fetchval("SELECT 1")

    async def _health_check_mysql(self):
        """MySQL 健康检查"""
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT 1")

    async def _health_check_mongodb(self):
        """MongoDB 健康检查"""
        await self._connection.admin.command("ping")

    async def _health_check_sqlite(self):
        """SQLite 健康检查"""
        async with self._connection.execute("SELECT 1") as cursor:
            await cursor.fetchone()

    # ==================== 数据库操作 ====================

    async def execute(
        self, query: str, params: Optional[Union[tuple, dict]] = None
    ) -> Any:
        """
        执行 SQL 查询

        Args:
            query: SQL 查询语句
            params: 查询参数

        Returns:
            查询结果
        """
        async with self._acquire_connection() as conn:
            start_time = time.time()

            if self._db_type == "postgresql":
                result = await self._execute_postgresql(conn, query, params)
            elif self._db_type == "mysql":
                result = await self._execute_mysql(conn, query, params)
            elif self._db_type == "sqlite":
                result = await self._execute_sqlite(conn, query, params)
            else:
                raise ValueError(f"execute 不支持数据库类型: {self._db_type}")

            latency_ms = (time.time() - start_time) * 1000
            self._update_latency_stats(latency_ms)

            return result

    async def _execute_postgresql(self, conn, query: str, params: Optional[tuple]):
        """执行 PostgreSQL 查询"""
        if params:
            return await conn.execute(query, *params)
        return await conn.execute(query)

    async def _execute_mysql(self, conn, query: str, params: Optional[tuple]):
        """执行 MySQL 查询"""
        async with conn.cursor() as cursor:
            if params:
                await cursor.execute(query, params)
            else:
                await cursor.execute(query)
            await conn.commit()
            return cursor.lastrowid

    async def _execute_sqlite(self, conn, query: str, params: Optional[tuple]):
        """执行 SQLite 查询"""
        if params:
            await conn.execute(query, params)
        else:
            await conn.execute(query)
        await conn.commit()
        return conn.lastrowid

    async def fetch_one(
        self, query: str, params: Optional[Union[tuple, dict]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取单条记录

        Args:
            query: SQL 查询语句
            params: 查询参数

        Returns:
            单条记录（字典格式）
        """
        async with self._acquire_connection() as conn:
            start_time = time.time()

            if self._db_type == "postgresql":
                result = await self._fetch_one_postgresql(conn, query, params)
            elif self._db_type == "mysql":
                result = await self._fetch_one_mysql(conn, query, params)
            elif self._db_type == "sqlite":
                result = await self._fetch_one_sqlite(conn, query, params)
            else:
                raise ValueError(f"fetch_one 不支持数据库类型: {self._db_type}")

            latency_ms = (time.time() - start_time) * 1000
            self._update_latency_stats(latency_ms)

            return result

    async def _fetch_one_postgresql(self, conn, query: str, params: Optional[tuple]):
        """PostgreSQL 获取单条记录"""
        if params:
            row = await conn.fetchrow(query, *params)
        else:
            row = await conn.fetchrow(query)
        return dict(row) if row else None

    async def _fetch_one_mysql(self, conn, query: str, params: Optional[tuple]):
        """MySQL 获取单条记录"""
        async with conn.cursor() as cursor:
            if params:
                await cursor.execute(query, params)
            else:
                await cursor.execute(query)
            row = await cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None

    async def _fetch_one_sqlite(self, conn, query: str, params: Optional[tuple]):
        """SQLite 获取单条记录"""
        async with conn.execute(query, params or ()) as cursor:
            row = await cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None

    async def fetch_many(
        self, query: str, params: Optional[Union[tuple, dict]] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取多条记录

        Args:
            query: SQL 查询语句
            params: 查询参数
            limit: 最大返回数量

        Returns:
            多条记录列表
        """
        async with self._acquire_connection() as conn:
            start_time = time.time()

            if self._db_type == "postgresql":
                result = await self._fetch_many_postgresql(conn, query, params, limit)
            elif self._db_type == "mysql":
                result = await self._fetch_many_mysql(conn, query, params, limit)
            elif self._db_type == "sqlite":
                result = await self._fetch_many_sqlite(conn, query, params, limit)
            else:
                raise ValueError(f"fetch_many 不支持数据库类型: {self._db_type}")

            latency_ms = (time.time() - start_time) * 1000
            self._update_latency_stats(latency_ms)

            return result

    async def _fetch_many_postgresql(self, conn, query: str, params: Optional[tuple], limit: int):
        """PostgreSQL 获取多条记录"""
        query = f"{query} LIMIT {limit}"
        if params:
            rows = await conn.fetch(query, *params)
        else:
            rows = await conn.fetch(query)
        return [dict(row) for row in rows]

    async def _fetch_many_mysql(self, conn, query: str, params: Optional[tuple], limit: int):
        """MySQL 获取多条记录"""
        query = f"{query} LIMIT {limit}"
        async with conn.cursor() as cursor:
            if params:
                await cursor.execute(query, params)
            else:
                await cursor.execute(query)
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    async def _fetch_many_sqlite(self, conn, query: str, params: Optional[tuple], limit: int):
        """SQLite 获取多条记录"""
        query = f"{query} LIMIT {limit}"
        async with conn.execute(query, params or ()) as cursor:
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    # ==================== MongoDB 操作 ====================

    async def find_one(self, collection: str, filter: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        MongoDB 查询单条记录

        Args:
            collection: 集合名称
            filter: 查询条件

        Returns:
            单条记录
        """
        if self._db_type != "mongodb":
            raise ValueError("find_one 仅支持 MongoDB")

        start_time = time.time()
        result = await self._connection[collection].find_one(filter)
        latency_ms = (time.time() - start_time) * 1000
        self._update_latency_stats(latency_ms)

        return result

    async def find_many(
        self, collection: str, filter: Dict[str, Any], limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        MongoDB 查询多条记录

        Args:
            collection: 集合名称
            filter: 查询条件
            limit: 最大返回数量

        Returns:
            多条记录列表
        """
        if self._db_type != "mongodb":
            raise ValueError("find_many 仅支持 MongoDB")

        start_time = time.time()
        cursor = self._connection[collection].find(filter).limit(limit)
        result = await cursor.to_list(length=limit)
        latency_ms = (time.time() - start_time) * 1000
        self._update_latency_stats(latency_ms)

        return result

    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """
        MongoDB 插入单条记录

        Args:
            collection: 集合名称
            document: 文档

        Returns:
            插入的文档ID
        """
        if self._db_type != "mongodb":
            raise ValueError("insert_one 仅支持 MongoDB")

        start_time = time.time()
        result = await self._connection[collection].insert_one(document)
        latency_ms = (time.time() - start_time) * 1000
        self._update_latency_stats(latency_ms)

        return str(result.inserted_id)

    async def update_one(
        self, collection: str, filter: Dict[str, Any], update: Dict[str, Any]
    ) -> int:
        """
        MongoDB 更新单条记录

        Args:
            collection: 集合名称
            filter: 查询条件
            update: 更新内容

        Returns:
            更新的文档数量
        """
        if self._db_type != "mongodb":
            raise ValueError("update_one 仅支持 MongoDB")

        start_time = time.time()
        result = await self._connection[collection].update_one(filter, {"$set": update})
        latency_ms = (time.time() - start_time) * 1000
        self._update_latency_stats(latency_ms)

        return result.modified_count

    async def delete_one(self, collection: str, filter: Dict[str, Any]) -> int:
        """
        MongoDB 删除单条记录

        Args:
            collection: 集合名称
            filter: 查询条件

        Returns:
            删除的文档数量
        """
        if self._db_type != "mongodb":
            raise ValueError("delete_one 仅支持 MongoDB")

        start_time = time.time()
        result = await self._connection[collection].delete_one(filter)
        latency_ms = (time.time() - start_time) * 1000
        self._update_latency_stats(latency_ms)

        return result.deleted_count

    # ==================== 上下文管理器 ====================

    @asynccontextmanager
    async def _acquire_connection(self):
        """获取数据库连接（上下文管理器）"""
        if self._db_type == "postgresql":
            async with self._pool.acquire() as conn:
                yield conn
        elif self._db_type == "mysql":
            async with self._pool.acquire() as conn:
                yield conn
        elif self._db_type == "sqlite":
            yield self._connection
        else:
            raise ValueError(f"不支持的数据库类型: {self._db_type}")

    @asynccontextmanager
    async def transaction(self):
        """事务上下文管理器"""
        if self._db_type == "postgresql":
            async with self._pool.acquire() as conn:
                async with conn.transaction():
                    yield conn
        elif self._db_type == "mysql":
            async with self._pool.acquire() as conn:
                await conn.begin()
                try:
                    yield conn
                    await conn.commit()
                except Exception:
                    await conn.rollback()
                    raise
        elif self._db_type == "sqlite":
            await self._connection.execute("BEGIN")
            try:
                yield self._connection
                await self._connection.commit()
            except Exception:
                await self._connection.rollback()
                raise
        else:
            raise ValueError(f"transaction 不支持数据库类型: {self._db_type}")


# 便捷函数
async def create_database_connector(
    name: str,
    db_type: str = "postgresql",
    host: str = "localhost",
    port: int = 5432,
    database: str = "postgres",
    user: str = "postgres",
    password: str = "",
    **kwargs
) -> DatabaseConnector:
    """
    创建数据库连接器

    Args:
        name: 连接器名称
        db_type: 数据库类型 (postgresql, mysql, mongodb, sqlite)
        host: 主机地址
        port: 端口
        database: 数据库名
        user: 用户名
        password: 密码
        **kwargs: 其他配置参数

    Returns:
        数据库连接器实例
    """
    config = ConnectorConfig(
        name=name,
        type=ConnectorType.DATABASE,
        connection_params={
            "db_type": db_type,
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
            **kwargs,
        },
    )

    connector = DatabaseConnector(config)
    await connector.initialize()
    return connector
