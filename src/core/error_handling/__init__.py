#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
错误处理模块，提供文件操作错误的处理机制。
"""

from .error_handler import (
    ErrorHandler,
    ErrorHandlingResult,
    FileOperationErrorHandler,
    with_error_handling,
)
from .error_record import ErrorRecord
from .logger import ErrorLogger
from .recovery import RecoveryManager, retry_operation

__all__ = [
    "ErrorRecord",
    "ErrorLogger",
    "RecoveryManager",
    "retry_operation",
    "ErrorHandlingResult",
    "ErrorHandler",
    "FileOperationErrorHandler",
    "with_error_handling",
]
