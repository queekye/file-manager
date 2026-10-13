#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
错误日志记录器模块，负责错误日志的记录和管理。
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from src.utils.path_utils import get_app_root
from src.utils.state_paths import get_state_root

from .error_record import ErrorRecord


class ErrorLogger:
    """错误日志记录器，用于记录和管理错误信息。"""

    def __init__(self, log_dir: str = None, max_log_size: int = 10):
        """
        初始化错误日志记录器。

        Args:
            log_dir: 日志文件目录，如果为None则使用当前目录下的logs文件夹
            max_log_size: 日志文件最大大小（MB）
        """
        self.log_dir = log_dir or str(get_state_root() / "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, "errors.json")
        self.error_records = []
        self._load_failed = False
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, encoding="utf-8") as stream:
                    self.error_records = [ErrorRecord.from_dict(row) for row in json.load(stream)]
            except (OSError, ValueError, KeyError, TypeError):
                self._load_failed = True
                logger.warning("已有错误记录无法读取；保留原文件，新的错误仍记录到应用日志")

    def _save_records(self):
        if self._load_failed:
            return
        temporary = self.log_file + ".tmp"
        with open(temporary, "w", encoding="utf-8") as stream:
            json.dump([record.to_dict() for record in self.error_records], stream, ensure_ascii=False)
        os.replace(temporary, self.log_file)

    def get_recent_errors(self, limit: int = 10):
        return sorted(self.error_records, key=lambda record: record.timestamp, reverse=True)[:limit]

    def clear_resolved_errors(self):
        self.error_records = [record for record in self.error_records if not record.resolved]
        self._save_records()

    def log_error(self, error_record: ErrorRecord) -> None:
        """
        记录错误信息。

        Args:
            error_record: 错误记录对象
        """
        # 记录到文件日志
        logger.error(
            f"{error_record.error_type}({error_record.error_code}): "
            f"{error_record.message} - Operation: {error_record.operation} "
            f"on {error_record.file_path}"
        )
        self.error_records.append(error_record)
        with open(os.path.join(self.log_dir, "error.log"), "a", encoding="utf-8") as stream:
            stream.write(str(error_record) + "\n")
        self._save_records()
