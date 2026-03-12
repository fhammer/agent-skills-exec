"""
消息队列适配器 - 提供各种消息队列的集成支持
"""

import asyncio
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod


class MQType(Enum):
    """消息队列类型"""
    RABBITMQ = "rabbitmq"
    REDIS = "redis"
    KAFKA = "kafka"
    SQS = "sqs"


@dataclass
class MQConfig:
    """消息队列配置"""
    mq_type: MQType
    host: str = "localhost"
    port: int = 5672
    username: str = "guest"
    password: str = "guest"
    virtual_host: str = "/"
    queue_name: str = "default"
    exchange_name: str = "default"
    exchange_type: str = "direct"
    routing_key: str = "default"
    durable: bool = True
    auto_delete: bool = False
    retry_exchange_name: str = "retry"
    dlq_name: str = "dlq"


class MessageQueueAdapter(ABC):
    """消息队列适配器抽象基类"""

    @abstractmethod
    async def connect(self) -> bool:
        """连接"""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """断开连接"""
        pass

    @abstractmethod
    async def publish(self, message: Dict[str, Any], routing_key: str = None) -> bool:
        """发布消息"""
        pass

    @abstractmethod
    async def consume(self, handler: Callable[[Dict[str, Any]], asyncio.Future], auto_ack: bool = False):
        """消费消息"""
        pass

    @abstractmethod
    async def acknowledge(self, delivery_tag: Any) -> bool:
        """确认消息"""
        pass

    @abstractmethod
    async def reject(self, delivery_tag: Any, requeue: bool = False) -> bool:
        """拒绝消息"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass


class RabbitMQAdapter(MessageQueueAdapter):
    """RabbitMQ适配器"""

    def __init__(self, config: MQConfig):
        self.config = config
        self._connection = None
        self._channel = None

    async def connect(self) -> bool:
        """连接"""
        import aio_pika
        try:
            # 连接
            self._connection = await aio_pika.connect_robust(
                f"amqp://{self.config.username}:{self.config.password}@{self.config.host}:"
                f"{self.config.port}/{self.config.virtual_host}"
            )

            # 创建通道
            self._channel = await self._connection.channel()

            # 声明交换机
            await self._channel.declare_exchange(
                self.config.exchange_name,
                self.config.exchange_type,
                durable=self.config.durable
            )

            # 声明队列
            self._queue = await self._channel.declare_queue(
                self.config.queue_name,
                durable=self.config.durable,
                auto_delete=self.config.auto_delete
            )

            # 绑定
            await self._queue.bind(
                self.config.exchange_name,
                routing_key=self.config.routing_key
            )

            return True

        except Exception as e:
            raise Exception(f"Failed to connect: {e}")

    async def disconnect(self) -> bool:
        """断开连接"""
        if self._channel:
            await self._channel.close()
        if self._connection:
            await self._connection.close()
        return True

    async def publish(self, message: Dict[str, Any], routing_key: str = None) -> bool:
        """发布消息"""
        import aio_pika
        if routing_key is None:
            routing_key = self.config.routing_key

        message_body = self._serialize_message(message)

        properties = aio_pika.BasicProperties(
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT if self.config.durable else aio_pika.DeliveryMode.TRANSIENT
        )

        await self._channel.default_exchange.publish(
            aio_pika.Message(
                body=message_body,
                properties=properties
            ),
            routing_key=routing_key
        )

        return True

    async def consume(
        self,
        handler: Callable[[Dict[str, Any]], asyncio.Future],
        auto_ack: bool = False
    ):
        """消费消息"""
        async def on_message(message):
            """消息处理回调"""
            try:
                data = self._deserialize_message(message.body)

                result = await handler(data)
                if result and not auto_ack:
                    await message.ack()
                elif not result and not auto_ack:
                    await message.reject(requeue=True)

            except Exception as e:
                if not auto_ack:
                    await message.reject(requeue=False)

        await self._queue.consume(on_message, no_ack=auto_ack)

    async def acknowledge(self, delivery_tag: Any) -> bool:
        """确认消息"""
        await self._channel.basic_ack(delivery_tag)
        return True

    async def reject(self, delivery_tag: Any, requeue: bool = False) -> bool:
        """拒绝消息"""
        await self._channel.basic_reject(delivery_tag, requeue=requeue)
        return True

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            return self._connection is not None and not self._connection.is_closed
        except:
            return False

    def _serialize_message(self, message: Dict[str, Any]) -> bytes:
        """序列化消息"""
        import json
        return json.dumps(message).encode('utf-8')

    def _deserialize_message(self, message_body: bytes) -> Dict[str, Any]:
        """反序列化消息"""
        import json
        return json.loads(message_body.decode('utf-8'))


class RedisMQAdapter(MessageQueueAdapter):
    """Redis消息队列适配器"""

    def __init__(self, config: MQConfig):
        self.config = config
        self._client = None

    async def connect(self) -> bool:
        """连接"""
        import redis.asyncio as redis
        self._client = redis.Redis(
            host=self.config.host,
            port=self.config.port,
            username=self.config.username,
            password=self.config.password
        )

        await self._client.ping()
        return True

    async def disconnect(self) -> bool:
        """断开连接"""
        if self._client:
            await self._client.close()
            self._client = None
        return True

    async def publish(self, message: Dict[str, Any], routing_key: str = None) -> bool:
        """发布消息"""
        import json

        queue = routing_key or self.config.queue_name

        await self._client.rpush(queue, json.dumps(message))
        return True

    async def consume(
        self,
        handler: Callable[[Dict[str, Any]], asyncio.Future],
        auto_ack: bool = False
    ):
        """消费消息"""
        import json

        while True:
            result = await self._client.blpop(self.config.queue_name, timeout=1)
            if result:
                queue, data = result
                message = json.loads(data.decode('utf-8'))
                await handler(message)

    async def acknowledge(self, delivery_tag: Any) -> bool:
        """确认消息 - 对于Redis不适用"""
        return True

    async def reject(self, delivery_tag: Any, requeue: bool = False) -> bool:
        """拒绝消息"""
        import json
        await self._client.rpush(
            self.config.dlq_name,
            json.dumps(delivery_tag)
        )
        return True

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            await self._client.ping()
            return True
        except:
            return False


class KafkaAdapter(MessageQueueAdapter):
    """Kafka适配器"""

    def __init__(self, config: MQConfig):
        self.config = config
        self._producer = None
        self._consumer = None

    async def connect(self) -> bool:
        """连接"""
        from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

        # 创建生产者
        self._producer = AIOKafkaProducer(
            bootstrap_servers=f"{self.config.host}:{self.config.port}"
        )

        await self._producer.start()

        # 创建消费者
        self._consumer = AIOKafkaConsumer(
            self.config.queue_name,
            bootstrap_servers=f"{self.config.host}:{self.config.port}",
            auto_offset_reset='earliest',
            group_id='agent-framework-group'
        )

        await self._consumer.start()
        return True

    async def disconnect(self) -> bool:
        """断开连接"""
        if self._producer:
            await self._producer.stop()
        if self._consumer:
            await self._consumer.stop()
        return True

    async def publish(self, message: Dict[str, Any], routing_key: str = None) -> bool:
        """发布消息"""
        import json

        if routing_key is None:
            routing_key = self.config.queue_name

        message_body = json.dumps(message).encode('utf-8')

        await self._producer.send(routing_key, value=message_body)
        return True

    async def consume(
        self,
        handler: Callable[[Dict[str, Any]], asyncio.Future],
        auto_ack: bool = False
    ):
        """消费消息"""
        import json

        async for msg in self._consumer:
            data = json.loads(msg.value.decode('utf-8'))
            await handler(data)
            if not auto_ack:
                await self._consumer.commit()

    async def acknowledge(self, delivery_tag: Any) -> bool:
        """确认消息"""
        await self._consumer.commit()
        return True

    async def reject(self, delivery_tag: Any, requeue: bool = False) -> bool:
        """拒绝消息"""
        return True

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 获取元数据
            topic_partitions = await self._producer.partitions_for(self.config.queue_name)
            return len(topic_partitions) > 0
        except:
            return False


# 工厂函数
def create_mq_adapter(config: MQConfig) -> MessageQueueAdapter:
    """创建消息队列适配器"""
    if config.mq_type == MQType.RABBITMQ:
        return RabbitMQAdapter(config)
    elif config.mq_type == MQType.REDIS:
        return RedisMQAdapter(config)
    elif config.mq_type == MQType.KAFKA:
        return KafkaAdapter(config)
    else:
        raise ValueError(f"Unknown MQ type: {config.mq_type}")
