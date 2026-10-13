#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自定义异常类模块，定义了系统中使用的各种异常类型。
"""


class FileManagerError(Exception):
    """文件管理器基础异常类，其他所有异常都继承自此类。"""

    pass


class FileNotFoundError(FileManagerError):
    """指定的文件未找到时抛出的异常。"""

    pass


class DirectoryNotFoundError(FileManagerError):
    """指定的目录未找到时抛出的异常。"""

    pass


class DirectoryCreationError(FileManagerError):
    """创建目录失败时抛出的异常。"""

    pass


class DirectoryPermissionError(FileManagerError):
    """目录权限不足时抛出的异常。"""

    pass


class FileOperationError(FileManagerError):
    """文件操作（复制、移动、重命名等）失败时抛出的异常。"""

    pass


class FileExistsError(FileManagerError):
    """目标文件已存在时抛出的异常。"""

    pass


class ConfigurationError(FileManagerError):
    """配置错误时抛出的异常。"""

    pass


class PersonNotFoundError(FileManagerError):
    """指定的人员未找到时抛出的异常。"""

    pass


class FileTypeNotFoundError(FileManagerError):
    """指定的文件类型未找到时抛出的异常。"""

    pass
