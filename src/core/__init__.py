#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
核心文件管理模块。
"""

from loguru import logger

from src.core.directory_manager import DirectoryManager
from src.core.exceptions import (
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

# 导出主要类
from src.core.file_manager import FileManager
from src.core.operation_result import FileOperationResult

__all__ = [
    "FileManager",
    "DirectoryManager",
    "FileOperationResult",
    "FileManagerError",
    "FileNotFoundError",
    "DirectoryNotFoundError",
    "DirectoryCreationError",
    "DirectoryPermissionError",
    "FileOperationError",
    "FileExistsError",
    "ConfigurationError",
    "PersonNotFoundError",
    "FileTypeNotFoundError",
]
