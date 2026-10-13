#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
错误记录模块，定义了错误记录的数据结构。
"""

from datetime import datetime
from typing import Any, Dict, Optional


class ErrorRecord:
    """错误记录类，用于存储错误相关信息。"""

    def __init__(
        self,
        error_code: str,
        error_type: str,
        message: str,
        operation: str,
        file_path: str,
        timestamp: datetime = None,
        stack_trace: Optional[str] = None,
        recovery_attempts: int = 0,
        resolved: bool = False,
    ):
        """
        初始化错误记录。

        Args:
            error_code: 错误代码
            error_type: 错误类型
            message: 错误消息
            operation: 执行的操作
            file_path: 相关文件路径
            timestamp: 错误发生时间，如果为None则使用当前时间
            stack_trace: 堆栈跟踪信息
            recovery_attempts: 恢复尝试次数
            resolved: 是否已解决
        """
        self.error_code = error_code
        self.error_type = error_type
        self.message = message
        self.operation = operation
        self.file_path = file_path
        self.timestamp = timestamp or datetime.now()
        self.stack_trace = stack_trace
        self.recovery_attempts = recovery_attempts
        self.resolved = resolved

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于存储和序列化。"""
        return {
            "error_code": self.error_code,
            "error_type": self.error_type,
            "message": self.message,
            "operation": self.operation,
            "file_path": self.file_path,
            "timestamp": self.timestamp.isoformat(),
            "stack_trace": self.stack_trace,
            "recovery_attempts": self.recovery_attempts,
            "resolved": self.resolved,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorRecord":
        """从字典创建错误记录实例。"""
        timestamp = datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else None
        return cls(
            error_code=data.get("error_code", ""),
            error_type=data.get("error_type", ""),
            message=data.get("message", ""),
            operation=data.get("operation", ""),
            file_path=data.get("file_path", ""),
            timestamp=timestamp,
            stack_trace=data.get("stack_trace"),
            recovery_attempts=data.get("recovery_attempts", 0),
            resolved=data.get("resolved", False),
        )

    def increment_recovery_attempts(self) -> None:
        """增加恢复尝试次数。"""
        self.recovery_attempts += 1

    def mark_as_resolved(self) -> None:
        """标记错误为已解决。"""
        self.resolved = True

    def __str__(self) -> str:
        """返回错误记录的字符串表示。"""
        return (
            f"Error: {self.error_type} ({self.error_code}) - {self.message}\n"
            f"Operation: {self.operation} on {self.file_path}\n"
            f"Time: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        )
