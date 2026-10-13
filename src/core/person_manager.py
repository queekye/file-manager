#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
人员管理模块，基于SQLite数据库实现。
"""

import json
import os
import re
from datetime import datetime
from functools import cached_property
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

try:
    from pypinyin import Style, lazy_pinyin

    PINYIN_SUPPORT = True
except ImportError:
    PINYIN_SUPPORT = False

from src.core.config import Config
from src.core.db import Database
from src.core.directory_manager import DirectoryManager
from src.core.exceptions import ConfigurationError
from src.core.template_data import TemplateData
from src.utils.path_utils import get_app_root
from src.utils.state_paths import get_state_root


class PersonManager:
    """人员管理类，负责处理人员数据。"""

    def __init__(self, db_path: Optional[str] = None, config: Optional[Config] = None):
        """
        初始化人员管理器。

        Args:
            db_path: 数据库文件路径，如果为None则使用默认路径
            config: 配置对象，包含人员字段定义
        """
        # 设置数据库路径
        db_path = db_path or str(get_state_root() / "persons.db")
        # 初始化数据库连接
        self.db = Database(db_path)

        # 缓存标记
        self._cache_invalidated = True

        # 保存配置对象引用
        self.config = config

        self.template_data = TemplateData()

        # 如果有配置对象，创建目录管理器
        if self.config and hasattr(self.config, "get_base_directory"):
            self.directory_manager = DirectoryManager(
                self.config.get_base_directory(), config=self.config
            )
        else:
            self.directory_manager = None

        # 导入默认数据（如果需要）
        # self._import_default_data_if_needed()

    @cached_property
    def persons(self) -> List[Dict[str, Any]]:
        """
        获取所有人员信息的缓存属性。

        Returns:
            List[Dict[str, Any]]: 所有人员信息列表
        """
        self._cache_invalidated = False
        return self.get_all_persons()

    @cached_property
    def last_id(self) -> int:
        """
        获取最后使用的人员ID的缓存属性。

        Returns:
            int: 最后使用的人员ID
        """
        self._cache_invalidated = False
        return int(self.db.get_setting("last_person_id", "0"))

    def _invalidate_cache(self) -> None:
        """
        使缓存失效，会在下次访问时重新加载数据。
        """
        if hasattr(self, "persons"):
            del self.persons
        if hasattr(self, "last_id"):
            del self.last_id
        self._cache_invalidated = True

    def get_person(self, person_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取人员。

        Args:
            person_id: 人员ID

        Returns:
            Dict或None: 找到的人员，如果未找到则返回None
        """
        result = self.db.execute_query("SELECT * FROM persons WHERE id = ?", (person_id,))

        if not result:
            return None

        # 处理额外字段
        person = result[0]
        self._process_additional_info(person)

        return person

    def get_person_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        根据姓名获取人员。

        Args:
            name: 人员姓名

        Returns:
            Dict或None: 找到的人员，如果未找到则返回None
        """
        result = self.db.execute_query("SELECT * FROM persons WHERE name = ?", (name,))

        if not result:
            return None

        # 处理额外字段
        person = result[0]
        self._process_additional_info(person)

        return person

    def get_person_by_directory(self, directory: str) -> Optional[Dict[str, Any]]:
        """
        根据目录名获取人员。

        Args:
            directory: 人员目录名

        Returns:
            Dict或None: 找到的人员，如果未找到则返回None
        """
        result = self.db.execute_query("SELECT * FROM persons WHERE directory = ?", (directory,))

        if not result:
            return None

        # 处理额外字段
        person = result[0]
        self._process_additional_info(person)

        return person

    def generate_directory_name(self, person: Dict[str, Any] = None, **additional_fields) -> str:
        """
        根据配置生成目录名称。

        Args:
            person: 人员字典
            **additional_fields: 其他字段

        Returns:
            str: 生成的目录名
        """
        # 默认模板
        directory_naming_template = "{name}_{id}"

        # 如果有配置对象，从配置中获取目录命名模板
        if self.config and hasattr(self.config, "options"):
            directory_naming_template = self.config.options.get(
                "directory_naming_template", "{name}_{id}"
            )

        try:
            # 使用字符串格式化替换占位符
            template_data = self.template_data.get_template_data(person=person, **additional_fields)
            directory = self.template_data.render(directory_naming_template, **template_data)
            return self._sanitize_directory_name(directory)
        except KeyError as e:
            logger.warning(f"目录命名模板缺少字段: {str(e)}")
            # 如果模板格式化失败，回退到默认方式
            return self._sanitize_directory_name(person["name"].lower())

    def _get_pinyin(self, text: str) -> str:
        """
        获取文本的拼音全拼。

        Args:
            text: 要转换的文本

        Returns:
            str: 拼音字符串
        """
        if PINYIN_SUPPORT:
            try:
                # 使用pypinyin获取拼音
                pinyin_list = lazy_pinyin(text)
                return "".join(pinyin_list).lower()
            except Exception as e:
                logger.warning(f"获取拼音失败: {str(e)}")

        # 如果没有pypinyin或者出错，简单处理非ASCII字符
        return self._sanitize_directory_name(text.lower())

    def _get_pinyin_first_letters(self, text: str) -> str:
        """
        获取文本的拼音首字母。

        Args:
            text: 要转换的文本

        Returns:
            str: 拼音首字母字符串
        """
        if PINYIN_SUPPORT:
            try:
                # 使用pypinyin获取拼音首字母
                first_letters = lazy_pinyin(text, style=Style.FIRST_LETTER)
                return "".join(first_letters).lower()
            except Exception as e:
                logger.warning(f"获取拼音首字母失败: {str(e)}")

        # 如果没有pypinyin或者出错，返回第一个字符
        return text[0].lower() if text else ""

    def _sanitize_directory_name(self, name: str) -> str:
        """
        清理目录名称，移除不允许用于文件名的字符。

        Args:
            name: 原始名称

        Returns:
            str: 清理后的名称
        """
        # 移除不允许用于文件名的字符
        # Windows文件名不能包含: \/:*?"<>|
        sanitized = re.sub(r'[\\/:*?"<>|]', "", name)

        # 替换空格为下划线
        sanitized = sanitized.replace(" ", "_")

        # 确保名称不为空
        if not sanitized:
            sanitized = "unnamed"

        return sanitized

    def add_person(
        self, name: str, directory: Optional[str] = None, **additional_fields
    ) -> Dict[str, Any]:
        """
        添加新人员。

        Args:
            name: 人员姓名
            directory: 可选的目录名，如果未提供则自动生成
            **additional_fields: 其他可选字段

        Returns:
            Dict: 新添加的人员数据

        Raises:
            ConfigurationError: 如果人员姓名为空或已存在相同目录名
        """
        if not name:
            raise ConfigurationError("人员姓名不能为空")

        logger.debug(f"开始添加人员: {name}，目录: {directory}")

        # 生成新ID
        last_id = int(self.db.get_setting("last_person_id", "0"))
        last_id += 1
        new_id = f"{last_id:03d}"
        person = {
            "id": new_id,
            "name": name,
            "directory": directory,
        }

        logger.debug(f"人员信息: {person}")

        # 如果未提供目录名，则根据配置自动生成
        if not directory:
            directory = self.generate_directory_name(person=person, **additional_fields)
            logger.debug(f"自动生成的目录: {directory}")
            person["directory"] = directory

        # 检查是否已存在相同目录名
        if self.get_person_by_directory(directory):
            # 尝试添加数字后缀来避免重复
            original_directory = directory
            counter = 1
            while self.get_person_by_directory(directory):
                directory = f"{original_directory}_{counter}"
                counter += 1
                # 防止无限循环
                if counter > 100:
                    raise ConfigurationError(f"无法生成唯一的目录名: {original_directory}")

        # 获取当前时间
        now = datetime.now().isoformat(timespec="seconds")

        # 处理额外字段
        # 如果提供了配置对象并且有人员字段定义，则检查并设置默认值
        if self.config and hasattr(self.config, "person_fields"):
            for field in self.config.person_fields:
                field_id = field.get("id")
                if field_id and field_id not in additional_fields and "default_value" in field:
                    additional_fields[field_id] = field.get("default_value", "")

        additional_info = (
            json.dumps(additional_fields, ensure_ascii=False) if additional_fields else None
        )

        # 添加到数据库
        self.db.execute_update(
            """
            INSERT INTO persons (id, name, directory, additional_info, created_at, last_modified)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (new_id, name, directory, additional_info, now, now),
        )

        # 更新最后ID
        self.db.set_setting("last_person_id", str(last_id))

        # 使缓存失效
        self._invalidate_cache()

        logger.info(f"添加人员: {name} (ID: {new_id})")

        # 返回新添加的人员数据
        person = {
            "id": new_id,
            "name": name,
            "directory": directory,
            "created_at": now,
            "last_modified": now,
        }

        # 添加其他可选字段
        person.update(additional_fields)

        logger.info(f"添加人员: {person}")

        return person

    def update_person(self, person_id: str, new_data: Dict[str, Any]) -> bool:
        """
        更新人员信息。

        Args:
            person_id: 要更新的人员ID
            new_data: 新的人员数据，将与现有数据合并

        Returns:
            bool: 是否成功更新
        """
        # 获取当前人员数据
        current_person = self.get_person(person_id)
        if not current_person:
            logger.warning(f"未找到要更新的人员 ID: {person_id}")
            return False

        # 不允许更改ID
        if "id" in new_data and new_data["id"] != person_id:
            logger.warning("不允许更改人员ID，忽略ID字段")
            new_data.pop("id")

        # 如果要更新目录名，检查是否与其他人员冲突
        if "directory" in new_data and new_data["directory"] != current_person.get("directory"):
            existing = self.get_person_by_directory(new_data["directory"])
            if existing and existing.get("id") != person_id:
                logger.warning(f"目录名 '{new_data['directory']}' 已被其他人员使用")
                return False

        # 准备更新数据
        update_fields = []
        params = []

        # 标准字段
        standard_fields = ["name", "directory"]
        for field in standard_fields:
            if field in new_data:
                update_fields.append(f"{field} = ?")
                params.append(new_data[field])

        # 处理额外字段
        extra_fields = {}
        # 先加载现有额外字段
        if current_person.get("additional_info"):
            try:
                if isinstance(current_person["additional_info"], str):
                    extra_fields = json.loads(current_person["additional_info"])
                else:
                    extra_fields = current_person["additional_info"]
            except json.JSONDecodeError:
                extra_fields = {}

        # 更新额外字段
        for key, value in new_data.items():
            if key not in standard_fields + [
                "id",
                "created_at",
                "last_modified",
                "additional_info",
            ]:
                extra_fields[key] = value

        # 添加额外字段到更新列表
        additional_info = json.dumps(extra_fields, ensure_ascii=False) if extra_fields else None
        update_fields.append("additional_info = ?")
        params.append(additional_info)

        # 更新最后修改时间
        now = datetime.now().isoformat(timespec="seconds")
        update_fields.append("last_modified = ?")
        params.append(now)

        # 添加ID到参数列表
        params.append(person_id)

        # 执行更新
        if update_fields:
            query = f"UPDATE persons SET {', '.join(update_fields)} WHERE id = ?"
            affected = self.db.execute_update(query, tuple(params))

            if affected > 0:
                # 使缓存失效
                self._invalidate_cache()

                logger.info(f"更新人员 ID: {person_id}")
                return True

        return False

    def delete_person(self, person_id: str) -> bool:
        """
        删除人员。

        Args:
            person_id: 要删除的人员ID

        Returns:
            bool: 是否成功删除
        """
        affected = self.db.execute_update("DELETE FROM persons WHERE id = ?", (person_id,))

        if affected > 0:
            # 使缓存失效
            self._invalidate_cache()

            logger.info(f"删除人员 ID: {person_id}")
            return True

        logger.warning(f"未找到要删除的人员 ID: {person_id}")
        return False

    def get_all_persons(self) -> List[Dict[str, Any]]:
        """
        获取所有人员信息。

        Returns:
            List[Dict[str, Any]]: 所有人员信息列表
        """
        result = self.db.execute_query("SELECT * FROM persons ORDER BY id")

        # 处理每个人员的额外字段
        for person in result:
            self._process_additional_info(person)

        return result

    def _process_additional_info(self, person: Dict[str, Any]) -> None:
        """
        处理人员的额外字段，将JSON字符串解析为字典并合并到人员数据中。

        Args:
            person: 人员数据字典，将被原地修改
        """
        if "additional_info" in person and person["additional_info"]:
            try:
                additional_info = json.loads(person["additional_info"])
                # 将额外字段合并到人员数据中
                person.update(additional_info)
            except json.JSONDecodeError:
                logger.warning(f"解析人员额外字段失败 ID: {person.get('id')}")

            # 删除额外字段键
            del person["additional_info"]

    def migrate_from_json(self, json_path: str) -> Tuple[int, int]:
        """
        从JSON文件迁移数据到SQLite数据库。

        Args:
            json_path: JSON文件路径

        Returns:
            Tuple[int, int]: 成功导入的人员数量和失败数量

        Raises:
            ConfigurationError: 如果JSON文件不存在或格式不正确
        """
        if not os.path.exists(json_path):
            raise ConfigurationError(f"JSON文件不存在: {json_path}")

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            persons = data.get("persons", [])
            last_id = data.get("last_id", 0)

            success_count = 0
            fail_count = 0

            # 导入人员数据
            for person in persons:
                try:
                    # 提取基本字段
                    person_id = person.get("id")
                    name = person.get("name")
                    directory = person.get("directory")

                    # 如果缺少必要字段，跳过
                    if not person_id or not name or not directory:
                        logger.warning(f"跳过导入人员，缺少必要字段: {person}")
                        fail_count += 1
                        continue

                    # 检查ID是否已存在
                    existing = self.get_person(person_id)
                    if existing:
                        logger.warning(f"跳过导入人员，ID已存在: {person_id}")
                        fail_count += 1
                        continue

                    # 提取额外字段
                    extra_fields = {}
                    for key, value in person.items():
                        if key not in ["id", "name", "directory", "created_at", "last_modified"]:
                            extra_fields[key] = value

                    additional_info = (
                        json.dumps(extra_fields, ensure_ascii=False) if extra_fields else None
                    )
                    created_at = person.get(
                        "created_at", datetime.now().isoformat(timespec="seconds")
                    )
                    last_modified = person.get(
                        "last_modified", datetime.now().isoformat(timespec="seconds")
                    )

                    # 添加到数据库
                    self.db.execute_update(
                        """
                        INSERT INTO persons (id, name, directory, additional_info, created_at, last_modified)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (person_id, name, directory, additional_info, created_at, last_modified),
                    )

                    success_count += 1

                except Exception as e:
                    logger.error(f"导入人员失败: {str(e)}")
                    fail_count += 1

            # 更新最后ID，如果JSON文件中的last_id更大
            current_last_id = int(self.db.get_setting("last_person_id", "0"))
            if last_id > current_last_id:
                self.db.set_setting("last_person_id", str(last_id))

            # 使缓存失效
            self._invalidate_cache()

            logger.info(f"从JSON文件迁移数据完成，成功: {success_count}，失败: {fail_count}")
            return success_count, fail_count

        except (json.JSONDecodeError, OSError) as e:
            raise ConfigurationError(f"读取JSON文件失败: {str(e)}")

    def export_to_json(self, json_path: str) -> bool:
        """
        将数据库中的人员数据导出到JSON文件。

        Args:
            json_path: 导出的JSON文件路径

        Returns:
            bool: 是否成功导出
        """
        try:
            # 获取所有人员
            persons = self.persons if not self._cache_invalidated else self.get_all_persons()

            # 获取最后ID
            last_id = (
                self.last_id
                if not self._cache_invalidated
                else int(self.db.get_setting("last_person_id", "0"))
            )

            # 创建数据字典
            data = {"persons": persons, "last_id": last_id}

            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(json_path)), exist_ok=True)

            # 写入JSON文件
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"成功导出人员数据到JSON文件: {json_path}")
            return True

        except Exception as e:
            logger.error(f"导出人员数据到JSON文件失败: {str(e)}")
            return False

    def close(self) -> None:
        """
        关闭数据库连接。
        """
        if self.db:
            self.db.close()

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

    def update_directory_manager(self) -> None:
        """更新目录管理器的当前目录。"""
        if self.directory_manager and self.config and hasattr(self.config, "get_base_directory"):
            self.directory_manager.update_base_directory()
            logger.info("已更新目录管理器的当前目录")
