#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
命令行参数处理模块，用于解析和处理从右键菜单传递的命令行参数。
"""

import argparse
import os
from typing import List, NamedTuple, Optional

from loguru import logger


class CommandArgs(NamedTuple):
    """命令行参数类，用于从右键菜单传递参数到程序。"""

    file_paths: List[str]
    person_id: Optional[str] = None
    file_type_id: Optional[str] = None
    operation: str = "copy"
    show_ui: bool = True


class CommandProcessor:
    """命令行参数处理类，解析和处理命令行参数。"""

    def __init__(self):
        """初始化命令行参数处理器。"""
        pass

    def log_info(self, message: str) -> None:
        """记录信息日志。"""
        logger.info(message)

    def log_error(self, message: str, exc_info: Optional[Exception] = None) -> None:
        """记录错误日志。"""
        if exc_info:
            logger.exception(f"{message}: {exc_info}")
        else:
            logger.error(message)

    def parse_args(self, args: List[str]) -> CommandArgs:
        """
        解析命令行参数。

        Args:
            args: 命令行参数列表

        Returns:
            命令行参数对象
        """
        try:
            # 创建参数解析器
            parser = argparse.ArgumentParser(description="文件管理系统")

            # 添加参数
            parser.add_argument("files", nargs="*", help="文件路径")
            parser.add_argument("--person_id", help="人员ID")
            parser.add_argument("--file_type_id", help="文件类型ID")
            parser.add_argument(
                "--operation", default="copy", choices=["copy", "move"], help="操作类型"
            )
            parser.add_argument(
                "--show_ui", type=lambda x: x.lower() == "true", default=True, help="是否显示UI"
            )
            parser.add_argument("--wait", action="store_true", help="执行完成后等待用户按键")

            # 解析参数
            parsed_args, unknown = parser.parse_known_args(args)

            # 提取文件路径
            file_paths = []
            for arg in parsed_args.files:
                if os.path.exists(arg):
                    file_paths.append(arg)

            # 创建CommandArgs对象
            command_args = CommandArgs(
                file_paths=file_paths,
                person_id=parsed_args.person_id,
                file_type_id=parsed_args.file_type_id,
                operation=parsed_args.operation,
                show_ui=parsed_args.show_ui,
            )

            self.log_info(f"解析命令行参数: {command_args}")
            return command_args

        except Exception as e:
            self.log_error("解析命令行参数时发生错误", e)
            # 返回默认参数
            return CommandArgs(file_paths=[])

    def to_command_line(self, args: CommandArgs) -> str:
        """
        将CommandArgs对象转换为命令行字符串。

        Args:
            args: 命令行参数对象

        Returns:
            命令行字符串
        """
        try:
            # 构建命令行
            cmd_parts = []

            # 添加文件路径
            for file_path in args.file_paths:
                cmd_parts.append(f'"{file_path}"')

            # 添加选项参数
            if args.person_id:
                cmd_parts.append(f'--person_id "{args.person_id}"')

            if args.file_type_id:
                cmd_parts.append(f'--file_type_id "{args.file_type_id}"')

            if args.operation != "copy":
                cmd_parts.append(f"--operation {args.operation}")

            if not args.show_ui:
                cmd_parts.append("--show_ui false")

            # 构建完整命令行
            command_line = " ".join(cmd_parts)
            self.log_info(f"生成命令行: {command_line}")
            return command_line

        except Exception as e:
            self.log_error("生成命令行时发生错误", e)
            return ""
