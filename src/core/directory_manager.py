#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
目录管理模块，负责处理目录创建、检查和路径生成。
支持多级目录结构、目录模板和目录结构验证与修复。
"""

import datetime
import os
import shutil
import stat
import string
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from loguru import logger

from src.core.exceptions import (
    DirectoryCreationError,
    DirectoryNotFoundError,
    DirectoryPermissionError,
)
from src.core.template_data import TemplateData


class DirectoryManager:
    """增强的目录结构管理类，负责创建和维护复杂的目录结构。"""

    def __init__(self, base_directory: str, config=None):
        """
        初始化目录管理器。

        Args:
            base_directory: 基础目录路径，所有人员文件夹将创建在此目录下
            config: 系统配置对象，可选
        """
        self.config = config
        # 如果有配置对象，使用其 get_base_directory 方法获取当前活动目录
        if self.config and hasattr(self.config, "get_base_directory"):
            self.base_directory = Path(self.config.get_base_directory())
        else:
            self.base_directory = Path(base_directory)
        self._operation_log = []  # 用于记录目录操作，支持回滚
        self.MAX_PATH_LENGTH = 260  # Windows默认最大路径长度
        self.template_data = TemplateData()

    def update_base_directory(self) -> None:
        """
        从配置对象更新当前活动的基础目录。
        """
        if self.config and hasattr(self.config, "get_base_directory"):
            self.base_directory = Path(self.config.get_base_directory())

    def ensure_directory(self, path: str) -> bool:
        """
        确保指定路径的目录存在，如果不存在则创建。

        Args:
            path: 要确保存在的目录路径

        Returns:
            bool: 如果目录已存在或成功创建，则返回True

        Raises:
            DirectoryCreationError: 如果目录创建失败
            DirectoryPermissionError: 如果没有足够权限创建目录
        """
        directory_path = Path(path).resolve()
        base = self.base_directory.resolve()
        if not directory_path.is_relative_to(base):
            raise DirectoryCreationError("目标目录必须位于配置的归档根目录内")

        # 处理路径过长问题
        if len(str(directory_path.absolute())) >= self.MAX_PATH_LENGTH:
            directory_path = self._handle_long_path(directory_path)

        if directory_path.exists():
            if directory_path.is_dir():
                # 检查目录权限
                if not self._check_directory_permissions(directory_path):
                    logger.error(f"目录权限不足: {directory_path}")
                    raise DirectoryPermissionError(f"目录权限不足: {directory_path}")

                logger.debug(f"目录已存在: {directory_path}")
                return True
            else:
                logger.error(f"路径存在但不是目录: {directory_path}")
                raise DirectoryCreationError(f"路径存在但不是目录: {directory_path}")

        try:
            # 记录创建操作，用于可能的回滚
            self._log_operation("create", str(directory_path))

            # 创建目录
            directory_path.mkdir(parents=True, exist_ok=True)

            # 检查目录权限
            if not self._check_directory_permissions(directory_path):
                logger.error(f"创建的目录权限不足: {directory_path}")
                raise DirectoryPermissionError(f"创建的目录权限不足: {directory_path}")

            logger.info(f"成功创建目录: {directory_path}")
            return True
        except PermissionError as e:
            logger.error(f"没有权限创建目录: {directory_path}, 错误: {str(e)}")
            raise DirectoryPermissionError(f"没有权限创建目录: {str(e)}")
        except Exception as e:
            logger.error(f"创建目录失败: {directory_path}, 错误: {str(e)}")
            raise DirectoryCreationError(f"创建目录失败: {str(e)}")

    def get_target_path(self, person: Dict[str, Any], file_type: Dict[str, Any]) -> Path:
        """
        获取指定人员和文件类型的目标路径。

        Args:
            person: 人员字典
            file_type: 文件类型字典

        Returns:
            Path: 目标路径对象

        Raises:
            DirectoryNotFoundError: 如果基础目录不存在且无法创建
        """
        # 确保基础目录存在
        if not self.ensure_directory(str(self.base_directory)):
            raise DirectoryNotFoundError(f"无法创建或访问基础目录: {self.base_directory}")

        # 构建目标路径
        target_path = self.ensure_directory_structure(person, file_type)

        # 确保目标路径存在
        self.ensure_directory(str(target_path))

        return target_path

    def ensure_directory_structure(
        self, person: Dict[str, Any], file_type: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        确保特定人员和文件类型的完整目录结构存在。
        如果配置了目录模板，将使用模板生成目录结构。

        Args:
            person: 人员信息字典
            file_type: 文件类型信息字典，可选

        Returns:
            str: 创建的目录路径

        Raises:
            DirectoryCreationError: 如果目录创建失败
        """
        logger.debug(f"确保目录结构: {person}, {file_type}")
        if self.config:
            template_string = self.config.options.get("directory_template", "{person}/{type}")
            logger.debug(f"使用配置模板: {template_string}")
        else:
            # 默认模板
            template_string = "{person}/{type}"
            logger.debug(f"使用默认模板: {template_string}")

        template_vars = self.template_data.get_template_data(person, file_type)

        try:
            logger.debug(f"渲染模板: {template_string}, {template_vars}")
            # 渲染模板
            relative_path = self.template_data.render(template_string, **template_vars)
            logger.debug(f"渲染结果: {relative_path}")

            # 构建完整路径
            full_path = self.base_directory / relative_path

            # 确保目录存在
            self.ensure_directory(str(full_path))

            return str(full_path)
        except (KeyError, Exception) as e:
            logger.error(f"创建目录结构失败: {str(e)}")
            raise DirectoryCreationError(f"创建目录结构失败: {str(e)}")

    def directory_exists(self, path: str) -> bool:
        """
        检查指定路径的目录是否存在。

        Args:
            path: 要检查的目录路径

        Returns:
            bool: 如果目录存在则返回True，否则返回False
        """
        directory_path = Path(path)
        return directory_path.exists() and directory_path.is_dir()

    def list_subdirectories(self, path: Optional[str] = None) -> List[str]:
        """
        列出指定路径下的所有子目录。

        Args:
            path: 要列出子目录的路径，如果为None则使用基础目录

        Returns:
            List[str]: 子目录名称列表

        Raises:
            DirectoryNotFoundError: 如果指定路径不存在
        """
        directory_path = Path(path) if path else self.base_directory

        if not directory_path.exists() or not directory_path.is_dir():
            raise DirectoryNotFoundError(f"目录不存在: {directory_path}")

        return [item.name for item in directory_path.iterdir() if item.is_dir()]

    def get_person_file_type_directories(self, person_dir: str) -> List[str]:
        """
        获取指定人员目录下的所有文件类型目录。

        Args:
            person_dir: 人员目录名

        Returns:
            List[str]: 文件类型目录名列表

        Raises:
            DirectoryNotFoundError: 如果人员目录不存在
        """
        person_path = self.base_directory / person_dir

        if not person_path.exists() or not person_path.is_dir():
            raise DirectoryNotFoundError(f"人员目录不存在: {person_path}")

        return self.list_subdirectories(str(person_path))

    def validate_directory_structure(self) -> List[Dict[str, Any]]:
        """
        验证当前目录结构的完整性，检查权限和路径问题。

        Returns:
            List[Dict[str, Any]]: 问题列表，每个问题包含类型、路径和描述
        """
        issues = []

        # 检查基础目录
        try:
            if not self.directory_exists(str(self.base_directory)):
                issues.append(
                    {
                        "type": "missing",
                        "path": str(self.base_directory),
                        "description": "基础目录不存在",
                    }
                )
            elif not self._check_directory_permissions(self.base_directory):
                issues.append(
                    {
                        "type": "permission",
                        "path": str(self.base_directory),
                        "description": "基础目录权限不足",
                    }
                )
        except Exception as e:
            issues.append(
                {
                    "type": "error",
                    "path": str(self.base_directory),
                    "description": f"验证基础目录时出错: {str(e)}",
                }
            )

        # 如果配置对象存在，检查配置中定义的目录结构
        if self.config:
            # 检查人员和文件类型目录
            for person in self.config.get_all_persons():
                person_dir = person.get("directory", "")
                person_path = self.base_directory / person_dir

                # 检查人员目录
                if not self.directory_exists(str(person_path)):
                    issues.append(
                        {
                            "type": "missing",
                            "path": str(person_path),
                            "description": f'人员目录不存在: {person.get("name", person_dir)}',
                        }
                    )

                # 检查人员下的文件类型目录
                for file_type in self.config.file_types:
                    file_type_dir = file_type.get("directory", "")
                    file_type_path = person_path / file_type_dir

                    if not self.directory_exists(str(file_type_path)):
                        issues.append(
                            {
                                "type": "missing",
                                "path": str(file_type_path),
                                "description": f'文件类型目录不存在: {person.get("name", person_dir)}/{file_type.get("name", file_type_dir)}',
                            }
                        )

        # 检查路径长度问题
        for root, dirs, _ in os.walk(str(self.base_directory)):
            for d in dirs:
                path = os.path.join(root, d)
                if len(path) >= self.MAX_PATH_LENGTH:
                    issues.append(
                        {
                            "type": "long_path",
                            "path": path,
                            "description": f"路径过长，超过{self.MAX_PATH_LENGTH}字符",
                        }
                    )

        return issues

    def repair_directory_structure(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        修复目录结构问题。

        Args:
            issues: 需要修复的问题列表，通常来自validate_directory_structure方法

        Returns:
            Dict[str, Any]: 修复结果统计，包含成功、失败数量和详细信息
        """
        results = {"success": 0, "failed": 0, "details": []}

        # 开始一个事务，记录所有操作
        self._begin_transaction()

        try:
            for issue in issues:
                issue_type = issue.get("type", "")
                path = issue.get("path", "")

                if not path:
                    continue

                try:
                    if issue_type == "missing":
                        # 创建缺失的目录
                        self.ensure_directory(path)
                        results["success"] += 1
                        results["details"].append(
                            {"path": path, "action": "created", "status": "success"}
                        )

                    elif issue_type == "permission":
                        # 尝试修复权限问题
                        if self._fix_directory_permissions(Path(path)):
                            results["success"] += 1
                            results["details"].append(
                                {"path": path, "action": "permission_fixed", "status": "success"}
                            )
                        else:
                            results["failed"] += 1
                            results["details"].append(
                                {
                                    "path": path,
                                    "action": "permission_fix",
                                    "status": "failed",
                                    "error": "无法修复权限问题",
                                }
                            )

                    elif issue_type == "long_path":
                        # 尝试处理路径过长问题
                        shortened_path = self._handle_long_path(Path(path), create=True)
                        if shortened_path:
                            results["success"] += 1
                            results["details"].append(
                                {
                                    "path": path,
                                    "action": "path_shortened",
                                    "status": "success",
                                    "new_path": str(shortened_path),
                                }
                            )
                        else:
                            results["failed"] += 1
                            results["details"].append(
                                {
                                    "path": path,
                                    "action": "path_shorten",
                                    "status": "failed",
                                    "error": "无法处理路径过长问题",
                                }
                            )

                except Exception as e:
                    logger.error(f"修复目录问题失败: {path}, 错误: {str(e)}")
                    results["failed"] += 1
                    results["details"].append(
                        {"path": path, "action": "repair", "status": "failed", "error": str(e)}
                    )

            # 提交事务
            self._commit_transaction()

        except Exception as e:
            # 回滚事务
            self._rollback_transaction()
            logger.error(f"目录修复操作失败，已回滚: {str(e)}")
            raise DirectoryCreationError(f"目录修复操作失败: {str(e)}")

        return results

    def _check_directory_permissions(self, path: Path) -> bool:
        """
        检查目录权限是否足够（可读、可写）。

        Args:
            path: 目录路径

        Returns:
            bool: 如果权限足够则返回True，否则返回False
        """
        try:
            # 检查目录是否存在
            if not path.exists():
                return False

            # 检查是否为目录
            if not path.is_dir():
                return False

            # 检查读权限
            test_read = os.access(path, os.R_OK)

            # 检查写权限
            test_write = os.access(path, os.W_OK)

            # 如果需要，检查执行权限（在Unix系统上）
            test_exec = os.access(path, os.X_OK) if os.name != "nt" else True

            return test_read and test_write and test_exec

        except Exception as e:
            logger.error(f"检查目录权限时出错: {path}, 错误: {str(e)}")
            return False

    def _fix_directory_permissions(self, path: Path) -> bool:
        """Permission repair requires the user's own OS policy; never widen ACLs."""
        logger.warning(f"目录权限需要用户自行检查，未更改权限: {path}")
        return False

    def _handle_long_path(self, path: Path, create: bool = False) -> Optional[Path]:
        """
        处理路径过长问题，可能通过创建符号链接或截断路径处理。

        Args:
            path: 过长的路径
            create: 是否创建目录，如果不存在

        Returns:
            Path或None: 处理后的路径，如果无法处理则返回None
        """
        try:
            # 完整路径
            abs_path = path.absolute()
            path_str = str(abs_path)

            # 如果路径没有超出限制，直接返回
            if len(path_str) < self.MAX_PATH_LENGTH:
                return abs_path

            # 处理路径过长问题
            if os.name == "nt":  # Windows
                # 尝试使用Windows长路径支持
                # 将路径转换为UNC格式: \\?\C:\path\to\directory
                unc_path = f"\\\\?\\{path_str}"
                result_path = Path(unc_path)

                # 如果需要创建目录
                if create and not result_path.exists():
                    result_path.mkdir(parents=True, exist_ok=True)

                return result_path
            else:
                # 在Unix/Linux系统上，创建符号链接
                # 创建一个短名称的临时目录，然后创建符号链接指向原路径

                # 计算一个唯一的短名称
                import hashlib

                hash_obj = hashlib.md5(path_str.encode())
                short_name = hash_obj.hexdigest()[:8]

                # 在基础目录中创建一个链接目录
                link_dir = self.base_directory / ".links"
                if not link_dir.exists():
                    link_dir.mkdir(exist_ok=True)

                # 创建符号链接
                link_path = link_dir / short_name

                # 如果链接已存在且指向不同位置，删除它
                if link_path.exists() and link_path.is_symlink():
                    target = os.readlink(link_path)
                    if target != path_str:
                        link_path.unlink()

                # 创建符号链接
                if not link_path.exists():
                    # 确保目标路径存在（如果需要创建）
                    if create and not abs_path.exists():
                        abs_path.mkdir(parents=True, exist_ok=True)

                    # 创建链接
                    os.symlink(path_str, link_path)

                return link_path

        except Exception as e:
            logger.error(f"处理路径过长问题失败: {path}, 错误: {str(e)}")
            return None

    def _resolve_conflict(self, path: Path) -> Path:
        """
        解决目录名冲突，通过添加数字后缀。

        Args:
            path: 冲突的目录路径

        Returns:
            Path: 解决冲突后的新路径
        """
        if not path.exists():
            return path

        counter = 1
        while True:
            new_path = path.parent / f"{path.name}_{counter}"
            if not new_path.exists():
                return new_path
            counter += 1

    def _log_operation(
        self, operation_type: str, path: str, extra_data: Dict[str, Any] = None
    ) -> None:
        """
        记录目录操作，用于事务和回滚。

        Args:
            operation_type: 操作类型，如'create', 'delete', 'rename'
            path: 操作的路径
            extra_data: 额外的操作数据
        """
        log_entry = {
            "type": operation_type,
            "path": path,
            "timestamp": datetime.datetime.now().isoformat(),
            "extra": extra_data or {},
        }
        self._operation_log.append(log_entry)

    def _begin_transaction(self) -> None:
        """开始一个事务，清除之前的操作日志。"""
        self._operation_log = []

    def _commit_transaction(self) -> None:
        """提交事务，清除操作日志。"""
        self._operation_log = []

    def _rollback_transaction(self) -> None:
        """
        回滚事务，撤销所有记录的操作。
        注意：这只能尽最大努力回滚，某些操作可能无法完全恢复。
        """
        # 反向处理操作日志，以便最后的操作先回滚
        for entry in reversed(self._operation_log):
            try:
                operation_type = entry.get("type", "")
                path = entry.get("path", "")

                if operation_type == "create":
                    # 回滚创建操作 - 删除目录
                    directory_path = Path(path)
                    if directory_path.exists() and directory_path.is_dir():
                        # Leave non-empty directories intact; they may contain
                        # data written independently since this transaction.
                        directory_path.rmdir()

                elif operation_type == "delete":
                    # 回滚删除操作 - 恢复目录（如果有备份）
                    backup_path = entry.get("extra", {}).get("backup_path", "")
                    if backup_path and Path(backup_path).exists():
                        shutil.copytree(backup_path, path)

                elif operation_type == "rename":
                    # 回滚重命名操作 - 恢复原名
                    old_path = entry.get("extra", {}).get("old_path", "")
                    if old_path and Path(path).exists():
                        Path(path).rename(old_path)

            except Exception as e:
                logger.error(f"回滚操作失败: {entry}, 错误: {str(e)}")

        # 清除操作日志
        self._operation_log = []
