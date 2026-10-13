#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
错误恢复模块，提供文件操作错误的恢复功能。
"""

import os
import shutil
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from src.utils.path_utils import get_app_root
from src.utils.state_paths import get_state_root


class RecoveryManager:
    """恢复管理器，用于处理文件操作的备份和恢复功能。"""

    def __init__(self, backup_dir: Optional[str] = None):
        """
        初始化恢复管理器。

        Args:
            backup_dir: 备份文件目录，如果为None则使用默认路径
        """
        self.backup_dir = backup_dir or str(get_state_root() / "backups")

        # 确保备份目录存在
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self, file_path: str) -> Optional[str]:
        """
        创建文件备份。

        Args:
            file_path: 需要备份的文件路径

        Returns:
            备份文件路径，如果备份失败则返回None
        """
        if not os.path.exists(file_path):
            return None

        # 创建以当前时间命名的备份目录
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_subdir = os.path.join(self.backup_dir, timestamp)
        os.makedirs(backup_subdir, exist_ok=True)

        # 生成备份文件路径
        file_name = os.path.basename(file_path)
        backup_path = os.path.join(backup_subdir, file_name)

        try:
            # 复制文件到备份位置
            shutil.copy2(file_path, backup_path)
            return backup_path
        except (IOError, OSError):
            return None

    def restore_from_backup(self, backup_path: str, target_path: str) -> bool:
        """
        从备份恢复文件。

        Args:
            backup_path: 备份文件路径
            target_path: 目标文件路径

        Returns:
            恢复是否成功
        """
        if not os.path.exists(backup_path):
            return False

        try:
            # 确保目标目录存在
            target_dir = os.path.dirname(target_path)
            os.makedirs(target_dir, exist_ok=True)

            # 复制备份文件到目标位置
            shutil.copy2(backup_path, target_path)
            return True
        except (IOError, OSError):
            return False

    def find_latest_backup(self, file_name: str) -> Optional[str]:
        """
        查找最新的备份文件。

        Args:
            file_name: 文件名

        Returns:
            最新备份文件的路径，如果没有找到则返回None
        """
        if not os.path.exists(self.backup_dir):
            return None

        # 获取所有备份子目录
        backup_dirs = [
            os.path.join(self.backup_dir, d)
            for d in os.listdir(self.backup_dir)
            if os.path.isdir(os.path.join(self.backup_dir, d))
        ]

        # 按照目录名（时间戳）排序
        backup_dirs.sort(reverse=True)

        # 查找包含指定文件名的最新备份
        for backup_dir in backup_dirs:
            backup_file = os.path.join(backup_dir, file_name)
            if os.path.exists(backup_file):
                return backup_file

        return None

    def clean_old_backups(self, days: int = 30) -> int:
        """
        清理指定天数前的旧备份。

        Args:
            days: 保留的天数

        Returns:
            删除的备份数量
        """
        if not os.path.exists(self.backup_dir):
            return 0

        # 当前时间
        now = time.time()
        # 保留期限（秒）
        retention_period = days * 24 * 60 * 60

        deleted_count = 0

        # 遍历备份子目录
        for d in os.listdir(self.backup_dir):
            backup_subdir = os.path.join(self.backup_dir, d)
            if os.path.isdir(backup_subdir):
                # 检查目录修改时间
                mtime = os.path.getmtime(backup_subdir)
                if now - mtime > retention_period:
                    try:
                        # 删除过期备份
                        shutil.rmtree(backup_subdir)
                        deleted_count += 1
                    except (IOError, OSError):
                        pass

        return deleted_count


def retry_operation(
    operation: Callable,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions_to_check: Optional[List[Exception]] = None,
) -> Any:
    """
    重试操作的装饰器函数。

    Args:
        operation: 要执行的操作函数
        max_attempts: 最大尝试次数
        delay: 初始延迟（秒）
        backoff_factor: 延迟增长因子
        exceptions_to_check: 需要捕获的异常列表

    Returns:
        操作结果

    Raises:
        Exception: 如果在最大尝试次数内操作仍然失败
    """
    exceptions_to_check = exceptions_to_check or [Exception]

    attempt = 0
    current_delay = delay

    while attempt < max_attempts:
        try:
            return operation()
        except tuple(exceptions_to_check) as e:
            attempt += 1

            # 如果达到最大尝试次数，则抛出异常
            if attempt >= max_attempts:
                raise e

            # 等待一段时间后重试
            time.sleep(current_delay)

            # 增加下次重试的延迟
            current_delay *= backoff_factor
