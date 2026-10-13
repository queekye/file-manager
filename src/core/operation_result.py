#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文件操作结果模型，用于封装文件操作的结果信息。
"""

from datetime import datetime
from typing import Any, Optional


class FileOperationResult:
    """文件操作结果类，封装了文件操作的结果信息。"""

    def __init__(
        self,
        success: bool,
        message: str,
        source_path: str,
        destination_path: Optional[str] = None,
        operation_type: str = "",
        error: Optional[Exception] = None,
    ):
        """
        初始化文件操作结果对象。

        Args:
            success: 操作是否成功
            message: 操作消息
            source_path: 源文件路径
            destination_path: 目标文件路径（如果适用）
            operation_type: 操作类型，如 "copy", "move", "rename"
            error: 如果操作失败，包含异常信息
        """
        self.success = success
        self.message = message
        self.source_path = source_path
        self.destination_path = destination_path
        self.operation_type = operation_type
        self.timestamp = datetime.now()
        self.error = error

    def __str__(self) -> str:
        """返回结果的字符串表示。"""
        status = "成功" if self.success else "失败"
        return f"[{self.timestamp}] {self.operation_type} {status}: {self.message}"

    def as_dict(self) -> dict[str, Any]:
        """将结果转换为字典格式。"""
        return {
            "success": self.success,
            "message": self.message,
            "source_path": self.source_path,
            "destination_path": self.destination_path,
            "operation_type": self.operation_type,
            "timestamp": self.timestamp.isoformat(),
            "error": str(self.error) if self.error else None,
        }
