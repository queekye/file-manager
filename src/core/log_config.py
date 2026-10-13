#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志配置模块，使用loguru库配置日志记录。
"""

import os
import sys
from typing import Optional

from loguru import logger
from src.utils.state_paths import get_state_root


def is_development_environment():
    """
    判断是否在开发环境中运行。
    
    Returns:
        bool: 如果是在开发环境中运行返回True，否则返回False
    """
    # 检查是否是打包环境
    if hasattr(sys, '_MEIPASS'):
        return False
        
    # 检查是否通过命令行参数启动（右键菜单或其他方式）
    # if len(sys.argv) > 1:
    #     return False
        
    # 检查是否是通过python直接运行的主程序
    main_script = sys.argv[0].lower()
    return 'python' in main_script or main_script.endswith('.py')


class LogConfig:
    """日志配置类，使用loguru配置日志记录。"""

    def __init__(
        self,
        log_dir: Optional[str] = None,
        log_level: str = "INFO",
        retention: str = "7 days",
        rotation: str = "10 MB",
        file_format: str = (
            "{time:YYYY-MM-DD HH:mm:ss} | {level} | "
            "{name}:{function}:{line} - {message}"
        ),
        console_format: str = (
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    ):
        """
        初始化日志配置。

        Args:
            log_dir: 日志目录路径，如果为None则使用默认路径
            log_level: 日志级别，可选值为DEBUG, INFO, WARNING, ERROR, CRITICAL
            retention: 日志保留时间
            rotation: 日志文件轮转大小
            file_format: 文件日志格式
            console_format: 控制台日志格式
        """
        # 优先使用环境变量中的日志路径
        self.log_dir = (
            log_dir
            or os.environ.get("LOGPATH")
            or str(get_state_root() / "logs")
        )
        self.log_level = log_level
        self.retention = retention
        self.rotation = rotation
        self.file_format = file_format
        self.console_format = console_format

        # 确保日志目录存在
        os.makedirs(self.log_dir, exist_ok=True)

        # 配置日志
        self.setup_logging()

    def setup_logging(self):
        """配置日志系统。"""
        try:
            # 移除默认处理器
            logger.remove()

            # 添加控制台处理器
            # 仅在开发环境下添加控制台输出
            if is_development_environment():
                logger.add(
                    sys.stderr,
                    format=self.console_format,
                    level=self.log_level,
                    colorize=True
                )

            # 添加文件处理器 - 普通日志
            logger.add(
                os.path.join(self.log_dir, "file_{time}.log"),
                format=self.file_format,
                level=self.log_level,
                rotation=self.rotation,
                retention=self.retention,
                encoding="utf-8",
                enqueue=True
            )

            # 添加文件处理器 - 错误日志
            logger.add(
                os.path.join(self.log_dir, "error_{time}.log"),
                format=self.file_format,
                level="ERROR",
                rotation=self.rotation,
                retention=self.retention,
                encoding="utf-8",
                backtrace=True,
                diagnose=False,
                enqueue=True
            )

            logger.info("日志系统初始化成功")
        except Exception as e:
            print(f"日志系统初始化失败: {str(e)}", file=sys.stderr)
            raise
