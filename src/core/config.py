#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置管理模块，负责配置文件的加载、验证和保存。
"""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from loguru import logger

from src.core.exceptions import ConfigurationError
from src.utils.state_paths import get_state_root


class Config:
    """配置管理类，负责处理系统配置文件。"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器。

        Args:
            config_path: 用户配置文件路径，如果为None则使用默认路径
        """
        # 优先使用环境变量中的配置路径
        # 按优先级依次检查配置文件路径:
        # 1. 传入的config_path
        # 2. 环境变量CONFIGPATH下的config.yaml
        # 3. 默认路径下的config.yaml
        if config_path:
            self.config_path = config_path
        elif os.environ.get("CONFIGPATH"):
            self.config_path = os.path.join(os.environ.get("CONFIGPATH"), "config.yaml")
        else:
            self.config_path = str(get_state_root() / "config.yaml")

        # 初始化配置属性
        self.base_directories = []  # 修改为列表
        self.current_base_directory = ""  # 添加当前活动目录
        self.naming_pattern = ""
        self.options = {}
        self.file_types = []
        self.person_fields = []  # 人员属性字段配置
        self.hotkeys = {}  # 快捷键设置

        # 加载配置
        self.load()

    def load(self, config_path: Optional[str] = None) -> None:
        """
        加载配置文件。如果用户配置文件不存在，则从默认配置创建。

        Args:
            config_path: 可选的配置文件路径，覆盖初始化时设置的路径

        Raises:
            ConfigurationError: 如果配置文件不存在且无法创建，或者格式不正确
        """
        if config_path:
            self.config_path = config_path

        try:
            # 如果配置文件不存在，尝试从默认配置创建
            if not self.config_path or not os.path.exists(self.config_path):
                logger.info(f"配置文件不存在，尝试从默认配置创建: {self.config_path}")
                self._create_from_default()

            # 读取和解析配置文件
            try:
                # 尝试使用更快的CSafeLoader
                from yaml import CSafeLoader as SafeLoader
            except ImportError:
                from yaml import SafeLoader

            with open(self.config_path, "r", encoding="utf-8") as f:
                config_data = yaml.load(f, Loader=SafeLoader)

            # 验证配置数据
            if not self._validate_config_data(config_data):
                raise ConfigurationError("配置文件格式不正确或缺少必要字段")

            # 更新配置属性
            self.base_directories = config_data.get("base_directories", [])
            self.current_base_directory = config_data.get("current_base_directory", "")
            self.naming_pattern = config_data.get("naming_pattern", "")
            self.options = config_data.get("options", {})
            self.file_types = config_data.get("file_types", [])
            self.person_fields = config_data.get("person_fields", [])
            self.hotkeys = config_data.get(
                "hotkeys", {"add_to_file_manager": "Ctrl+Alt+F", "open_config": "Ctrl+Alt+C"}
            )

            logger.info(f"成功加载配置文件: {self.config_path}")

        except (yaml.YAMLError, OSError) as e:
            raise ConfigurationError(f"加载配置文件失败: {str(e)}")

    def save(self, config_path: Optional[str] = None) -> None:
        """
        保存配置到文件。

        Args:
            config_path: 可选的配置文件保存路径，覆盖初始化时设置的路径

        Raises:
            ConfigurationError: 如果保存配置文件失败
        """
        if config_path:
            self.config_path = config_path

        # 创建配置数据字典
        config_data = {
            "base_directories": self.base_directories,
            "current_base_directory": self.current_base_directory,
            "naming_pattern": self.naming_pattern,
            "options": self.options,
            "file_types": self.file_types,
            "person_fields": self.person_fields,
            "hotkeys": self.hotkeys,
        }

        try:
            # 如果路径不存在，确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)

            # 备份现有配置
            self._backup_config()

            # 保存配置文件
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    config_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False
                )

            logger.info(f"成功保存配置文件: {self.config_path}")

        except (yaml.YAMLError, OSError) as e:
            raise ConfigurationError(f"保存配置文件失败: {str(e)}")

    def validate(self) -> bool:
        """
        验证当前配置是否有效。

        Returns:
            bool: 配置是否有效
        """
        # 检查基本目录列表
        if not self.base_directories:
            logger.error("基本目录列表为空")
            return False

        # 检查当前活动目录
        if (
            not self.current_base_directory
            or self.current_base_directory not in self.base_directories
        ):
            logger.error("当前活动目录无效")
            return False

        # 检查命名模式
        if not self.naming_pattern:
            logger.error("文件命名模式未指定")
            return False

        # 检查文件类型列表
        if not self.file_types:
            logger.warning("未定义任何文件类型")

        # 检查每个文件类型的必要字段
        for ft in self.file_types:
            if "id" not in ft:
                logger.error("文件类型缺少'id'字段")
                return False
            if "name" not in ft:
                logger.error(f"文件类型 {ft.get('id', '未知')} 缺少'name'字段")
                return False
            if "directory" not in ft:
                logger.error(f"文件类型 {ft.get('id', '未知')} 缺少'directory'字段")
                return False

        # 检查人员字段配置
        for field in self.person_fields:
            if "id" not in field:
                logger.error("人员字段定义缺少'id'字段")
                return False
            if "name" not in field:
                logger.error(f"人员字段 {field.get('id', '未知')} 缺少'name'字段")
                return False

        return True

    def get_file_type(self, type_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取文件类型定义。

        Args:
            type_id: 文件类型ID

        Returns:
            Dict或None: 找到的文件类型定义，如果未找到则返回None
        """
        for ft in self.file_types:
            if ft.get("id") == type_id:
                return ft
        return None

    def add_file_type(self, file_type: Dict[str, Any]) -> bool:
        """
        添加新的文件类型定义。

        Args:
            file_type: 文件类型定义字典，必须包含id, name, directory字段

        Returns:
            bool: 是否成功添加

        Raises:
            ConfigurationError: 如果文件类型定义不完整或ID已存在
        """
        # 验证必要字段
        if "id" not in file_type or "name" not in file_type or "directory" not in file_type:
            raise ConfigurationError("文件类型定义不完整，必须包含id, name, directory字段")

        # 检查ID是否已存在
        if self.get_file_type(file_type["id"]):
            raise ConfigurationError(f"文件类型ID '{file_type['id']}' 已存在")

        # 添加文件类型
        self.file_types.append(file_type)
        logger.info(f"添加文件类型: {file_type['name']} (ID: {file_type['id']})")
        return True

    def delete_file_type(self, type_id: str) -> bool:
        """
        删除文件类型定义。

        Args:
            type_id: 要删除的文件类型ID

        Returns:
            bool: 是否成功删除
        """
        for i, ft in enumerate(self.file_types):
            if ft.get("id") == type_id:
                del self.file_types[i]
                logger.info(f"删除文件类型 ID: {type_id}")
                return True

        logger.warning(f"未找到要删除的文件类型 ID: {type_id}")
        return False

    def update_file_type(self, type_id: str, new_data: Dict[str, Any]) -> bool:
        """
        更新文件类型定义。

        Args:
            type_id: 要更新的文件类型ID
            new_data: 新的文件类型数据，将与现有数据合并

        Returns:
            bool: 是否成功更新
        """
        for i, ft in enumerate(self.file_types):
            if ft.get("id") == type_id:
                # 不允许更改ID
                if "id" in new_data and new_data["id"] != type_id:
                    logger.warning(f"不允许更改文件类型ID，忽略ID字段")
                    new_data.pop("id")

                # 更新数据
                self.file_types[i].update(new_data)
                logger.info(f"更新文件类型 ID: {type_id}")
                return True

        logger.warning(f"未找到要更新的文件类型 ID: {type_id}")
        return False

    def get_person_field(self, field_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取人员字段定义。

        Args:
            field_id: 人员字段ID

        Returns:
            Dict或None: 找到的人员字段定义，如果未找到则返回None
        """
        for field in self.person_fields:
            if field.get("id") == field_id:
                return field
        return None

    def add_person_field(self, field: Dict[str, Any]) -> bool:
        """
        添加新的人员字段定义。

        Args:
            field: 人员字段定义字典，必须包含id, name字段

        Returns:
            bool: 是否成功添加

        Raises:
            ConfigurationError: 如果人员字段定义不完整或ID已存在
        """
        # 验证必要字段
        if "id" not in field or "name" not in field:
            raise ConfigurationError("人员字段定义不完整，必须包含id, name字段")

        # 检查ID是否已存在
        if self.get_person_field(field["id"]):
            raise ConfigurationError(f"人员字段ID '{field['id']}' 已存在")

        # 添加人员字段
        self.person_fields.append(field)
        logger.info(f"添加人员字段: {field['name']} (ID: {field['id']})")
        return True

    def delete_person_field(self, field_id: str) -> bool:
        """
        删除人员字段定义。

        Args:
            field_id: 要删除的人员字段ID

        Returns:
            bool: 是否成功删除
        """
        for i, field in enumerate(self.person_fields):
            if field.get("id") == field_id:
                del self.person_fields[i]
                logger.info(f"删除人员字段 ID: {field_id}")
                return True

        logger.warning(f"未找到要删除的人员字段 ID: {field_id}")
        return False

    def update_person_field(self, field_id: str, new_data: Dict[str, Any]) -> bool:
        """
        更新人员字段定义。

        Args:
            field_id: 要更新的人员字段ID
            new_data: 新的人员字段数据，将与现有数据合并

        Returns:
            bool: 是否成功更新
        """
        for i, field in enumerate(self.person_fields):
            if field.get("id") == field_id:
                # 不允许更改ID
                if "id" in new_data and new_data["id"] != field_id:
                    logger.warning(f"不允许更改人员字段ID，忽略ID字段")
                    new_data.pop("id")

                # 更新数据
                self.person_fields[i].update(new_data)
                logger.info(f"更新人员字段 ID: {field_id}")
                return True

        logger.warning(f"未找到要更新的人员字段 ID: {field_id}")
        return False

    def _validate_config_data(self, config_data: Dict) -> bool:
        """
        验证配置数据是否包含所有必要字段。

        Args:
            config_data: 配置数据字典

        Returns:
            bool: 数据是否有效
        """
        # 检查必要字段
        if "base_directories" not in config_data:
            # 如果是旧版配置，将单一目录转换为列表
            if "base_directory" in config_data:
                config_data["base_directories"] = [config_data["base_directory"]]
                config_data["current_base_directory"] = config_data["base_directory"]
                del config_data["base_directory"]
            else:
                logger.error("配置缺少'base_directories'字段")
                return False

        # 验证 base_directories 是否为列表且不为空
        if (
            not isinstance(config_data["base_directories"], list)
            or not config_data["base_directories"]
        ):
            logger.error("'base_directories'字段必须是非空列表")
            return False

        # 验证 current_base_directory
        if "current_base_directory" not in config_data:
            config_data["current_base_directory"] = config_data["base_directories"][0]
        elif config_data["current_base_directory"] not in config_data["base_directories"]:
            logger.error("'current_base_directory'必须是'base_directories'中的一个值")
            return False

        if "naming_pattern" not in config_data:
            logger.error("配置缺少'naming_pattern'字段")
            return False

        # 其他字段可选，但如果存在，需要检查格式
        if "options" in config_data and not isinstance(config_data["options"], dict):
            logger.error("'options'字段必须是字典类型")
            return False
        else:
            # 确保options存在，并设置默认值
            if "options" not in config_data:
                config_data["options"] = {}

            # 设置默认目录模板，如果未指定
            if "directory_template" not in config_data["options"]:
                config_data["options"]["directory_template"] = "{person}/{type}"

        if "file_types" in config_data and not isinstance(config_data["file_types"], list):
            logger.error("'file_types'字段必须是列表类型")
            return False

        if "person_fields" in config_data and not isinstance(config_data["person_fields"], list):
            logger.error("'person_fields'字段必须是列表类型")
            return False
        else:
            # 确保person_fields存在
            if "person_fields" not in config_data:
                config_data["person_fields"] = []

        if "hotkeys" in config_data and not isinstance(config_data["hotkeys"], dict):
            logger.error("'hotkeys'字段必须是字典类型")
            return False
        else:
            # 确保hotkeys存在，并设置默认值
            if "hotkeys" not in config_data:
                config_data["hotkeys"] = {
                    "add_to_file_manager": "Ctrl+Alt+F",
                    "open_config": "Ctrl+Alt+C",
                }

        return True

    def _create_from_default(self) -> None:
        """
        从默认配置创建用户配置。

        Raises:
            ConfigurationError: 如果创建失败
        """
        try:
            # 构建默认配置
            default_config = {
                # 基本配置
                "base_directories": [str(Path(self.config_path).parent / "archive")],
                "current_base_directory": str(Path(self.config_path).parent / "archive"),
                # 文件命名模式
                "naming_pattern": "{person}_{type}_{date}_{original_filename}{original_extension}",
                # 操作选项
                "options": {
                    "copy_files": True,
                    "create_directories": True,
                    "open_after_operation": False,
                    "directory_template": "{person}/{type}-{year}-{month}",
                    "directory_naming_template": "{name}",
                    "auto_rename_duplicates": True,
                    "max_history_items": 100,
                    "preserve_timestamps": True,
                },
                # 快捷键设置
                "hotkeys": {"add_to_file_manager": "Ctrl+Alt+F", "open_config": "Ctrl+Alt+C"},
                # 人员字段定义
                "person_fields": [
                    {
                        "id": "contact",
                        "name": "联系方式",
                        "description": "电话或其他联系方式",
                        "required": False,
                        "default_value": "",
                    }
                ],
                # 文件类型定义
                "file_types": [
                    {
                        "id": "photo",
                        "name": "照片",
                        "directory": "Photos",
                        "description": "个人照片、证件照等",
                    }
                ],
            }

            # 确保目标目录存在
            os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)

            # 保存默认配置到文件
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    default_config, f, default_flow_style=False, allow_unicode=True, sort_keys=False
                )

            logger.info(f"已创建默认配置文件: {self.config_path}")

        except OSError as e:
            raise ConfigurationError(f"创建默认配置文件失败: {str(e)}")

    def _backup_config(self) -> None:
        """
        备份当前配置文件。
        """
        if os.path.exists(self.config_path):
            try:
                # 创建备份文件名，包含时间戳
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = os.path.join(os.path.dirname(self.config_path), "backup")
                os.makedirs(backup_dir, exist_ok=True)
                backup_path = os.path.join(
                    backup_dir, f"{os.path.basename(self.config_path)}.{timestamp}.bak"
                )

                # 复制文件
                shutil.copy2(self.config_path, backup_path)
                logger.info(f"已创建配置文件备份: {backup_path}")

            except OSError as e:
                logger.warning(f"创建配置文件备份失败: {str(e)}")

    def get_base_directory(self) -> str:
        """
        获取当前活动的基本目录。

        Returns:
            str: 当前活动的基本目录路径
        """
        return self.current_base_directory

    def set_base_directory(self, directory: str) -> bool:
        """
        设置当前活动的基本目录。

        Args:
            directory: 要设置为活动目录的路径

        Returns:
            bool: 是否成功设置
        """
        if directory in self.base_directories:
            self.current_base_directory = directory
            return True
        return False

    def add_base_directory(self, directory: str) -> bool:
        """
        添加新的基本目录。

        Args:
            directory: 要添加的目录路径

        Returns:
            bool: 是否成功添加
        """
        if directory not in self.base_directories:
            self.base_directories.append(directory)
            # 如果是第一个添加的目录，设置为当前活动目录
            if len(self.base_directories) == 1:
                self.current_base_directory = directory
            return True
        return False

    def remove_base_directory(self, directory: str) -> bool:
        """
        移除基本目录。

        Args:
            directory: 要移除的目录路径

        Returns:
            bool: 是否成功移除
        """
        if directory in self.base_directories:
            # 如果要移除的是当前活动目录，需要切换到其他目录
            if directory == self.current_base_directory:
                if len(self.base_directories) > 1:
                    self.current_base_directory = next(
                        d for d in self.base_directories if d != directory
                    )
                else:
                    return False  # 不允许移除最后一个目录

            self.base_directories.remove(directory)
            return True
        return False
