#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
错误处理器模块，提供统一的错误处理接口和实现。
"""

import functools
import os
import traceback
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast

from ..exceptions import (
    ConfigurationError,
    DirectoryCreationError,
    DirectoryNotFoundError,
    DirectoryPermissionError,
    FileExistsError,
    FileManagerError,
    FileNotFoundError,
    FileOperationError,
    FileTypeNotFoundError,
    PersonNotFoundError,
)
from .error_record import ErrorRecord
from .logger import ErrorLogger
from .recovery import RecoveryManager, retry_operation


# 定义错误处理结果类型
class ErrorHandlingResult:
    """错误处理结果类，用于表示错误处理的结果。"""

    def __init__(
        self,
        success: bool = False,
        error_record: Optional[ErrorRecord] = None,
        recovery_attempted: bool = False,
        recovery_succeeded: bool = False,
        suggestions: List[str] = None,
    ):
        """
        初始化错误处理结果。

        Args:
            success: 处理是否成功
            error_record: 错误记录
            recovery_attempted: 是否尝试了恢复
            recovery_succeeded: 恢复是否成功
            suggestions: 建议列表
        """
        self.success = success
        self.error_record = error_record
        self.recovery_attempted = recovery_attempted
        self.recovery_succeeded = recovery_succeeded
        self.suggestions = suggestions or []

    @property
    def error_message(self) -> str:
        """获取错误消息。"""
        if self.error_record:
            return self.error_record.message
        return "未知错误"

    @property
    def has_suggestions(self) -> bool:
        """是否有建议。"""
        return len(self.suggestions) > 0

    def __bool__(self) -> bool:
        """布尔值表示处理是否成功。"""
        return self.success


# 错误代码前缀映射
ERROR_CODE_PREFIXES = {
    FileNotFoundError: "FNF",  # File Not Found
    DirectoryNotFoundError: "DNF",  # Directory Not Found
    DirectoryCreationError: "DCE",  # Directory Creation Error
    DirectoryPermissionError: "DPE",  # Directory Permission Error
    FileOperationError: "FOP",  # File Operation Error
    FileExistsError: "FEX",  # File Exists Error
    ConfigurationError: "CFG",  # Configuration Error
    PersonNotFoundError: "PNF",  # Person Not Found
    FileTypeNotFoundError: "TNF",  # Type Not Found
    Exception: "GEN",  # General Exception
}


class ErrorHandler:
    """错误处理器基类，定义错误处理的通用方法。"""

    def __init__(self, log_dir: str = None, backup_dir: str = None):
        """
        初始化错误处理器。

        Args:
            log_dir: 日志目录
            backup_dir: 备份目录
        """
        self.logger = ErrorLogger(log_dir=log_dir)
        self.recovery_manager = RecoveryManager(backup_dir=backup_dir)
        self._error_count = 0

    def handle_error(
        self, exception: Exception, operation: str, file_path: str, **context
    ) -> ErrorHandlingResult:
        """
        处理发生的错误。

        Args:
            exception: 捕获的异常
            operation: 执行的操作
            file_path: 相关文件路径
            **context: 其他上下文信息

        Returns:
            ErrorHandlingResult: 错误处理结果
        """
        # 获取错误类型
        error_type = type(exception).__name__

        # 生成错误代码
        error_code = self._generate_error_code(exception)

        # 获取堆栈跟踪
        stack_trace = traceback.format_exc()

        # 使用传入的错误消息或异常转换为字符串
        error_message = context.get("error_message", str(exception))

        # 创建错误记录
        error_record = ErrorRecord(
            error_code=error_code,
            error_type=error_type,
            message=error_message,
            operation=operation,
            file_path=file_path,
            timestamp=datetime.now(),
            stack_trace=stack_trace,
        )

        # 记录错误
        self.log_error(error_record)

        # 尝试恢复
        recovery_attempted = False
        recovery_succeeded = False

        if self._should_attempt_recovery(exception, operation, file_path):
            recovery_attempted = True
            recovery_succeeded = self._attempt_recovery(error_record, **context)

        # 生成建议
        suggestions = self.suggest_recovery(error_record)

        # 返回处理结果
        return ErrorHandlingResult(
            success=recovery_succeeded,
            error_record=error_record,
            recovery_attempted=recovery_attempted,
            recovery_succeeded=recovery_succeeded,
            suggestions=suggestions,
        )

    def _generate_error_code(self, exception: Exception) -> str:
        """
        生成错误代码。

        Args:
            exception: 异常对象

        Returns:
            错误代码
        """
        self._error_count += 1

        # 获取异常类型对应的前缀
        for exc_type, prefix in ERROR_CODE_PREFIXES.items():
            if isinstance(exception, exc_type):
                # 生成带有计数器的错误代码
                return f"{prefix}-{self._error_count:04d}"

        # 默认使用通用前缀
        return f"GEN-{self._error_count:04d}"

    def log_error(self, error_record: ErrorRecord) -> None:
        """
        记录错误到日志。

        Args:
            error_record: 错误记录
        """
        self.logger.log_error(error_record)

    def suggest_recovery(self, error_record: ErrorRecord) -> List[str]:
        """
        提供恢复建议。

        Args:
            error_record: 错误记录

        Returns:
            建议列表
        """
        # 基础实现，子类可以根据具体错误类型提供更详细的建议
        suggestions = []

        # 根据错误类型提供通用建议
        if "NotFound" in error_record.error_type:
            suggestions.append("请检查文件或目录路径是否正确")
            suggestions.append("文件可能已被删除或移动")
        elif "Permission" in error_record.error_type:
            suggestions.append("请检查您是否有足够的权限执行此操作")
            suggestions.append("尝试以管理员身份运行程序")
        elif "Creation" in error_record.error_type:
            suggestions.append("请检查磁盘空间是否充足")
            suggestions.append("确保目标位置可写入")
        elif "Exists" in error_record.error_type:
            suggestions.append("请使用不同的文件名或启用覆盖选项")
        elif "Configuration" in error_record.error_type:
            suggestions.append("请检查配置文件格式是否正确")
            suggestions.append("尝试重置为默认配置")

        return suggestions

    def _should_attempt_recovery(
        self, exception: Exception, operation: str, file_path: str
    ) -> bool:
        """
        判断是否应该尝试恢复。

        Args:
            exception: 异常对象
            operation: 执行的操作
            file_path: 相关文件路径

        Returns:
            是否应该尝试恢复
        """
        # 基础实现，子类可以根据具体情况决定是否尝试恢复
        return isinstance(exception, (FileOperationError, FileNotFoundError, FileExistsError))

    def _attempt_recovery(self, error_record: ErrorRecord, **context) -> bool:
        """
        尝试恢复操作。

        Args:
            error_record: 错误记录
            **context: 其他上下文信息

        Returns:
            恢复是否成功
        """
        # 基础实现，子类应该根据具体错误类型实现恢复逻辑
        return False

    def retry_operation(
        self,
        operation: Callable,
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions_to_check: Optional[List[Exception]] = None,
    ) -> Any:
        """
        尝试重试操作。

        Args:
            operation: 要执行的操作函数
            max_attempts: 最大尝试次数
            delay: 初始延迟（秒）
            backoff_factor: 延迟增长因子
            exceptions_to_check: 需要捕获的异常列表

        Returns:
            操作结果
        """
        exceptions_to_check = exceptions_to_check or [FileManagerError]
        return retry_operation(
            operation,
            max_attempts=max_attempts,
            delay=delay,
            backoff_factor=backoff_factor,
            exceptions_to_check=exceptions_to_check,
        )


# 类型变量，用于装饰器
T = TypeVar("T")


def with_error_handling(operation_name: str):
    """
    错误处理装饰器，用于包装需要错误处理的函数。

    Args:
        operation_name: 操作名称

    Returns:
        装饰后的函数
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                # 从self中获取错误处理器
                error_handler = getattr(self, "error_handler", None)

                if error_handler and isinstance(error_handler, ErrorHandler):
                    # 从args或kwargs中尝试获取file_path
                    file_path = ""
                    if args and isinstance(args[0], str):
                        file_path = args[0]
                    elif "file_path" in kwargs:
                        file_path = kwargs["file_path"]
                    elif "path" in kwargs:
                        file_path = kwargs["path"]

                    # 处理错误
                    result = error_handler.handle_error(
                        exception=e,
                        operation=operation_name,
                        file_path=file_path,
                        args=args,
                        kwargs=kwargs,
                        error_message=str(e),  # 添加错误消息
                    )

                    # 如果错误处理成功，尝试重新执行操作
                    if result.success and result.recovery_succeeded:
                        return func(self, *args, **kwargs)

                # 如果没有错误处理器或处理失败，重新抛出异常
                raise

        return wrapper

    return decorator


class FileOperationErrorHandler(ErrorHandler):
    """文件操作错误处理器，处理文件操作相关的错误。"""

    def _attempt_recovery(self, error_record: ErrorRecord, **context) -> bool:
        """
        尝试恢复文件操作错误。

        Args:
            error_record: 错误记录
            **context: 其他上下文信息

        Returns:
            恢复是否成功
        """
        # 增加恢复尝试次数
        error_record.increment_recovery_attempts()

        # 根据错误类型尝试不同的恢复策略
        if "FileNotFound" in error_record.error_type:
            return self._handle_file_not_found(error_record, **context)
        elif "DirectoryNotFound" in error_record.error_type:
            return self._handle_directory_not_found(error_record, **context)
        elif "Permission" in error_record.error_type:
            return self._handle_permission_error(error_record, **context)
        elif "FileExists" in error_record.error_type:
            return self._handle_file_exists_error(error_record, **context)

        return False

    def _handle_file_not_found(self, error_record: ErrorRecord, **context) -> bool:
        """处理文件未找到错误。"""
        file_path = error_record.file_path

        # 尝试从备份恢复
        file_name = os.path.basename(file_path)
        backup_path = self.recovery_manager.find_latest_backup(file_name)

        if backup_path:
            # 尝试从备份恢复
            return self.recovery_manager.restore_from_backup(backup_path, file_path)

        return False

    def _handle_directory_not_found(self, error_record: ErrorRecord, **context) -> bool:
        """处理目录未找到错误。"""
        dir_path = os.path.dirname(error_record.file_path)

        # 尝试创建目录
        try:
            os.makedirs(dir_path, exist_ok=True)
            return os.path.exists(dir_path)
        except Exception:
            return False

    def _handle_permission_error(self, error_record: ErrorRecord, **context) -> bool:
        """处理权限错误。"""
        # 权限错误通常需要用户干预，无法自动恢复
        return False

    def _handle_file_exists_error(self, error_record: ErrorRecord, **context) -> bool:
        """Reject conflicts without deleting or changing the existing target."""
        return False

    def suggest_recovery(self, error_record: ErrorRecord) -> List[str]:
        """
        提供恢复建议，扩展基类方法，增加更具体的建议。

        Args:
            error_record: 错误记录

        Returns:
            建议列表
        """
        suggestions = super().suggest_recovery(error_record)

        # 根据错误类型增加更具体的建议
        if "FileNotFound" in error_record.error_type:
            suggestions.append("可以尝试使用系统文件搜索功能查找文件")
        elif "DirectoryNotFound" in error_record.error_type:
            suggestions.append("请确保所有父目录已创建")
        elif "Permission" in error_record.error_type:
            suggestions.append("关闭可能正在使用此文件的其他程序")
            suggestions.append("检查文件是否被其他进程锁定")
        elif "FileExists" in error_record.error_type:
            suggestions.append("您可以选择覆盖现有文件或使用新的文件名")

        return suggestions
