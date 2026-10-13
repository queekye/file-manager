#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Windows交互处理模块，提供与Windows系统交互的功能。
使用pywin32库处理Windows注册表和系统API调用。
"""

import winreg
from typing import List, Optional

from loguru import logger


class PyWinHandler:
    """Windows交互处理类，处理注册表和系统API调用。"""

    def __init__(self, app_path: str, app_name: str = "文件管理器"):
        """
        初始化Windows交互处理器。

        Args:
            app_path: 应用程序路径
            app_name: 应用程序名称
        """
        self.app_path = app_path
        self.app_name = app_name

    def log_info(self, message: str) -> None:
        """记录信息日志。"""
        logger.info(message)

    def log_error(self, message: str, exc_info: Optional[Exception] = None) -> None:
        """记录错误日志。"""
        if exc_info:
            logger.exception(f"{message}: {exc_info}")
        else:
            logger.error(message)

    def handle_command(self, args: List[str]) -> bool:
        """
        处理命令行参数。

        Args:
            args: 命令行参数列表

        Returns:
            是否成功处理命令
        """
        try:
            self.log_info(f"处理命令: {' '.join(args)}")
            # 实现命令处理逻辑
            return True
        except Exception as e:
            self.log_error("处理命令时发生错误", e)
            return False

    def send_to_core_engine(
        self, file_paths: List[str], person_id: str, file_type_id: str, operation: str = "copy"
    ) -> bool:
        """
        发送文件操作请求到核心引擎。

        Args:
            file_paths: 文件路径列表
            person_id: 人员ID
            file_type_id: 文件类型ID
            operation: 操作类型 (copy/move)

        Returns:
            是否成功发送请求
        """
        try:
            self.log_info(
                f"发送请求到核心引擎: {operation} {len(file_paths)} 个文件到 {person_id}/{file_type_id}"
            )
            # 实现核心引擎调用逻辑
            # 这里可以集成到main.py中已有的文件处理逻辑
            return True
        except Exception as e:
            self.log_error("发送请求到核心引擎时发生错误\n", e)
            return False

    def get_registry_menu_command(self, file_ext: str = "*") -> Optional[str]:
        """
        获取注册表中的菜单命令。

        Args:
            file_ext: 文件扩展名，默认为*表示所有文件

        Returns:
            菜单命令字符串，如果不存在则返回None
        """
        try:
            key_path = f"{file_ext}\\shell\\{self.app_name}\\command"
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
                value, _ = winreg.QueryValueEx(key, "")
                return value
        except Exception as e:
            self.log_error(f"获取注册表菜单命令时发生错误: {key_path}", e)
            return None

    def is_menu_registered(self, file_ext: str = "*") -> bool:
        """
        检查菜单是否已注册。

        Args:
            file_ext: 文件扩展名，默认为*表示所有文件

        Returns:
            菜单是否已注册
        """
        return self.get_registry_menu_command(file_ext) is not None

    def create_command_string(self, include_wait: bool = True) -> str:
        """
        创建命令字符串。

        Args:
            include_wait: 是否包含等待参数

        Returns:
            命令字符串
        """
        cmd = f'"{self.app_path}" "%1"'
        if include_wait:
            cmd += ' "--wait"'
        return cmd
