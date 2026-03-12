"""
文件系统适配器 - 提供文件系统操作集成支持
"""

import os
import asyncio
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

try:
    import aiofiles
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False
    aiofiles = None


class FileType(Enum):
    """文件类型"""
    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"
    FTP = "ftp"
    SFTP = "sftp"


@dataclass
class FileConfig:
    """文件系统配置"""
    file_type: FileType = FileType.LOCAL
    root_dir: str = "."
    bucket_name: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    endpoint_url: Optional[str] = None
    host: str = "localhost"
    port: int = 21
    username: str = ""
    password: str = ""


class FileAdapter(ABC):
    """文件系统适配器抽象基类"""

    @abstractmethod
    async def connect(self) -> bool:
        """连接"""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """断开连接"""
        pass

    @abstractmethod
    async def list_files(self, path: str = ".") -> List[str]:
        """列出文件"""
        pass

    @abstractmethod
    async def read_file(self, file_path: str) -> bytes:
        """读取文件"""
        pass

    @abstractmethod
    async def write_file(self, file_path: str, data: bytes, overwrite: bool = True) -> bool:
        """写入文件"""
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        pass

    @abstractmethod
    async def create_directory(self, dir_path: str, recursive: bool = True) -> bool:
        """创建目录"""
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """检查是否存在"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass


class LocalFileAdapter(FileAdapter):
    """本地文件系统适配器"""

    def __init__(self, config: FileConfig):
        self.config = config
        self._root_dir = Path(config.root_dir).resolve()

    async def connect(self) -> bool:
        """连接"""
        if not self._root_dir.exists():
            self._root_dir.mkdir(parents=True, exist_ok=True)
        return True

    async def disconnect(self) -> bool:
        """断开连接"""
        return True

    async def list_files(self, path: str = ".") -> List[str]:
        """列出文件"""
        target_path = self._root_dir / path
        if not target_path.exists():
            return []

        files = []
        for item in target_path.iterdir():
            relative_path = item.relative_to(self._root_dir)
            files.append(str(relative_path))

        return sorted(files)

    async def read_file(self, file_path: str) -> bytes:
        """读取文件"""
        target_path = self._root_dir / file_path

        if not target_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        async with aiofiles.open(target_path, 'rb') as f:
            return await f.read()

    async def write_file(self, file_path: str, data: bytes, overwrite: bool = True) -> bool:
        """写入文件"""
        target_path = self._root_dir / file_path

        # 确保父目录存在
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if not overwrite and target_path.exists():
            raise FileExistsError(f"File already exists: {file_path}")

        async with aiofiles.open(target_path, 'wb') as f:
            await f.write(data)
        return True

    async def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        target_path = self._root_dir / file_path

        if not target_path.exists():
            return False

        try:
            target_path.unlink()
            return True
        except:
            return False

    async def create_directory(self, dir_path: str, recursive: bool = True) -> bool:
        """创建目录"""
        target_path = self._root_dir / dir_path
        target_path.mkdir(parents=True, exist_ok=True)
        return True

    async def exists(self, path: str) -> bool:
        """检查是否存在"""
        return (self._root_dir / path).exists()

    async def health_check(self) -> bool:
        """健康检查"""
        return self._root_dir.exists()


class S3FileAdapter(FileAdapter):
    """S3文件系统适配器"""

    def __init__(self, config: FileConfig):
        self.config = config
        self._s3_client = None

    async def connect(self) -> bool:
        """连接"""
        import boto3
        from botocore.config import Config

        session = boto3.Session()
        self._s3_client = session.client(
            's3',
            aws_access_key_id=self.config.access_key,
            aws_secret_access_key=self.config.secret_key,
            endpoint_url=self.config.endpoint_url,
            config=Config(signature_version='s3v4')
        )
        return True

    async def disconnect(self) -> bool:
        """断开连接"""
        self._s3_client = None
        return True

    async def list_files(self, path: str = ".") -> List[str]:
        """列出文件"""
        result = await asyncio.to_thread(
            self._s3_client.list_objects,
            Bucket=self.config.bucket_name,
            Prefix=path
        )
        if 'Contents' not in result:
            return []

        return [obj['Key'] for obj in result['Contents']]

    async def read_file(self, file_path: str) -> bytes:
        """读取文件"""
        result = await asyncio.to_thread(
            self._s3_client.get_object,
            Bucket=self.config.bucket_name,
            Key=file_path
        )
        return result['Body'].read()

    async def write_file(self, file_path: str, data: bytes, overwrite: bool = True) -> bool:
        """写入文件"""
        if not overwrite:
            try:
                await asyncio.to_thread(
                    self._s3_client.head_object,
                    Bucket=self.config.bucket_name,
                    Key=file_path
                )
                raise FileExistsError(f"File already exists: {file_path}")
            except:
                pass

        await asyncio.to_thread(
            self._s3_client.put_object,
            Bucket=self.config.bucket_name,
            Key=file_path,
            Body=data
        )
        return True

    async def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        await asyncio.to_thread(
            self._s3_client.delete_object,
            Bucket=self.config.bucket_name,
            Key=file_path
        )
        return True

    async def create_directory(self, dir_path: str, recursive: bool = True) -> bool:
        """创建目录 - S3不需要实际创建目录"""
        await asyncio.to_thread(
            self._s3_client.put_object,
            Bucket=self.config.bucket_name,
            Key=f"{dir_path}/"
        )
        return True

    async def exists(self, path: str) -> bool:
        """检查是否存在"""
        try:
            await asyncio.to_thread(
                self._s3_client.head_object,
                Bucket=self.config.bucket_name,
                Key=path
            )
            return True
        except:
            return False

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            await asyncio.to_thread(
                self._s3_client.head_bucket,
                Bucket=self.config.bucket_name
            )
            return True
        except:
            return False


class FTPFileAdapter(FileAdapter):
    """FTP文件系统适配器"""

    def __init__(self, config: FileConfig):
        self.config = config
        self._ftp = None

    async def connect(self) -> bool:
        """连接"""
        import ftplib
        self._ftp = ftplib.FTP()
        await asyncio.to_thread(self._ftp.connect, self.config.host, self.config.port)
        await asyncio.to_thread(self._ftp.login, self.config.username, self.config.password)
        await asyncio.to_thread(self._ftp.cwd, self.config.root_dir)
        return True

    async def disconnect(self) -> bool:
        """断开连接"""
        await asyncio.to_thread(self._ftp.quit)
        self._ftp = None
        return True

    async def list_files(self, path: str = ".") -> List[str]:
        """列出文件"""
        return await asyncio.to_thread(self._ftp.nlst, path)

    async def read_file(self, file_path: str) -> bytes:
        """读取文件"""
        data = b''

        def callback(chunk):
            nonlocal data
            data += chunk

        await asyncio.to_thread(self._ftp.retrbinary, f"RETR {file_path}", callback)
        return data

    async def write_file(self, file_path: str, data: bytes, overwrite: bool = True) -> bool:
        """写入文件"""
        if not overwrite and await self.exists(file_path):
            raise FileExistsError(f"File already exists: {file_path}")

        await asyncio.to_thread(
            self._ftp.storbinary,
            f"STOR {file_path}",
            (chunk for chunk in self._chunk_data(data))
        )
        return True

    async def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        try:
            await asyncio.to_thread(self._ftp.delete, file_path)
            return True
        except Exception:
            return False

    async def create_directory(self, dir_path: str, recursive: bool = True) -> bool:
        """创建目录"""
        if recursive:
            parts = dir_path.split('/')
            current = ''
            for part in parts:
                if part:
                    current += f"/{part}"
                    try:
                        await asyncio.to_thread(self._ftp.mkd, current)
                    except Exception:
                        await asyncio.to_thread(self._ftp.cwd, current)
        else:
            await asyncio.to_thread(self._ftp.mkd, dir_path)

        return True

    async def exists(self, path: str) -> bool:
        """检查是否存在"""
        try:
            await asyncio.to_thread(self._ftp.size, path)
            return True
        except Exception:
            try:
                await asyncio.to_thread(self._ftp.cwd, path)
                return True
            except Exception:
                return False

    async def health_check(self) -> bool:
        """健康检查"""
        return self._ftp is not None and self._ftp.sock is not None

    def _chunk_data(self, data: bytes, chunk_size: int = 8192):
        """分块数据"""
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]


# 工厂函数
def create_file_adapter(config: FileConfig) -> FileAdapter:
    """创建文件系统适配器"""
    if config.file_type == FileType.LOCAL:
        return LocalFileAdapter(config)
    elif config.file_type == FileType.S3:
        return S3FileAdapter(config)
    elif config.file_type == FileType.GCS:
        return S3FileAdapter(config)  # GCS与S3 API兼容
    elif config.file_type == FileType.FTP:
        return FTPFileAdapter(config)
    else:
        raise ValueError(f"Unknown file type: {config.file_type}")


# 便捷工厂函数
def create_local_file_adapter(root_dir: str = ".") -> FileAdapter:
    """创建本地文件系统适配器"""
    return create_file_adapter(FileConfig(
        file_type=FileType.LOCAL,
        root_dir=root_dir
    ))


def create_s3_file_adapter(bucket_name: str, access_key: str, secret_key: str, endpoint_url: str = None) -> FileAdapter:
    """创建S3文件系统适配器"""
    return create_file_adapter(FileConfig(
        file_type=FileType.S3,
        bucket_name=bucket_name,
        access_key=access_key,
        secret_key=secret_key,
        endpoint_url=endpoint_url
    ))
