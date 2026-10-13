#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库模块，负责管理SQLite数据库连接和提供基础操作。
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from src.utils.path_utils import get_app_root
from src.utils.state_paths import get_state_root


class Database:
    """数据库管理类，提供SQLite数据库连接和基础操作。"""

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库连接。

        Args:
            db_path: 数据库文件路径，如果为None则使用默认路径
        """
        if db_path is None:
            # 优先使用CONFIGPATH环境变量
            if "CONFIGPATH" in os.environ:
                self.db_path = os.path.join(os.environ["CONFIGPATH"], "persons.db")
            else:
                self.db_path = str(get_state_root() / "persons.db")
        else:
            self.db_path = db_path

        self.conn = None
        self.cursor = None

        # 初始化数据库
        self._initialize_db()

    def _initialize_db(self) -> None:
        """
        初始化数据库，创建必要的表结构。
        """
        try:
            # 确保数据库目录存在
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)

            # 连接数据库
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # 使查询结果可通过列名访问
            self.cursor = self.conn.cursor()

            # 创建persons表
            self.cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS persons (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                directory TEXT NOT NULL UNIQUE,
                additional_info TEXT,  -- 用于存储JSON格式的额外字段
                created_at TEXT NOT NULL,
                last_modified TEXT NOT NULL
            )
            """
            )

            # 创建last_id表，用于记录最后使用的ID
            self.cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
            )

            # 添加last_person_id设置，如果不存在
            self.cursor.execute(
                """
            INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
            """,
                ("last_person_id", "0"),
            )

            # 提交事务
            self.conn.commit()
            logger.info(f"数据库初始化完成: {self.db_path}")

        except sqlite3.Error as e:
            logger.error(f"初始化数据库失败: {str(e)}")
            if self.conn:
                self.conn.close()
            raise

    def close(self) -> None:
        """
        关闭数据库连接。
        """
        if self.conn:
            self.conn.close()
            logger.debug("数据库连接已关闭")

    def __enter__(self):
        """
        实现上下文管理器协议的进入方法。
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        实现上下文管理器协议的退出方法，确保关闭数据库连接。
        """
        self.close()

    def get_setting(self, key: str, default: Optional[str] = None) -> str:
        """
        获取设置值。

        Args:
            key: 设置键名
            default: 默认值，如果设置不存在

        Returns:
            str: 设置值
        """
        try:
            self.cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = self.cursor.fetchone()
            return result["value"] if result else default
        except sqlite3.Error as e:
            logger.error(f"获取设置失败 {key}: {str(e)}")
            return default

    def set_setting(self, key: str, value: str) -> bool:
        """
        设置值。

        Args:
            key: 设置键名
            value: 设置值

        Returns:
            bool: 是否成功设置
        """
        try:
            self.cursor.execute(
                """
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
            """,
                (key, value),
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"设置值失败 {key}: {str(e)}")
            self.conn.rollback()
            return False

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        执行查询并返回结果。

        Args:
            query: SQL查询语句
            params: 查询参数

        Returns:
            List[Dict[str, Any]]: 查询结果列表
        """
        try:
            self.cursor.execute(query, params)
            columns = [col[0] for col in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"执行查询失败: {str(e)}")
            return []

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        执行更新操作并返回影响的行数。

        Args:
            query: SQL更新语句
            params: 更新参数

        Returns:
            int: 影响的行数
        """
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"执行更新失败: {str(e)}")
            self.conn.rollback()
            return 0
