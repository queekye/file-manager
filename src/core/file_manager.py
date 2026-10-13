#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文件管理器核心模块，负责文件的复制、移动和重命名操作。
"""

import os
import hashlib
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from src.core.directory_manager import DirectoryManager
from src.core.error_handling import (
    FileOperationErrorHandler,
    with_error_handling,
)
from src.core.exceptions import (
    ConfigurationError,
    DirectoryNotFoundError,
    FileExistsError,
    FileNotFoundError,
    FileOperationError,
)
from src.core.naming import NamingEngine
from src.core.operation_result import FileOperationResult


class FileManager:
    """文件管理器核心类，负责处理文件操作。"""

    def __init__(
        self,
        directory_manager: DirectoryManager,
        naming_pattern: str = "{person}_{type}_{original_filename}{original_extension}",
        enable_error_handling: bool = True,
        log_dir: str = None,
        backup_dir: str = None,
        options: Dict[str, Any] = None,
    ):
        """
        初始化文件管理器。

        Args:
            directory_manager: 目录管理器
            naming_pattern: 文件命名模式
            enable_error_handling: 是否启用错误处理
            log_dir: 错误日志目录
            backup_dir: 备份文件目录
            options: 文件操作选项，包括：
                - copy_files: bool, 是否默认复制文件
                - create_directories: bool, 是否自动创建目标目录
                - open_after_operation: bool, 操作后是否打开文件夹
                - directory_template: str, 目录结构模板
                - preserve_timestamps: bool, 是否保留原始时间戳
        """
        self.directory_manager = directory_manager
        self.naming_engine = NamingEngine(naming_pattern)
        self._history = []

        # 设置默认选项
        self.options = {
            "copy_files": True,
            "create_directories": True,
            "open_after_operation": False,
            "directory_template": "{person}/{type}",
            "preserve_timestamps": True,
        }

        # 更新用户提供的选项
        if options:
            self.options.update(options)

        # 初始化错误处理器
        self.error_handler = (
            FileOperationErrorHandler(log_dir=log_dir, backup_dir=backup_dir)
            if enable_error_handling
            else None
        )
        self.enable_error_handling = enable_error_handling

    @with_error_handling("copy_file")
    def copy_file(
        self, source_path: str, person: Dict[str, Any], file_type: Dict[str, Any]
    ) -> FileOperationResult:
        """
        复制文件到指定人员和文件类型的目录，并根据命名规则重命名。

        Args:
            source_path: 源文件路径
            person: 目标人员信息
            file_type: 目标文件类型信息

        Returns:
            FileOperationResult: 操作结果对象

        Raises:
            FileNotFoundError: 如果源文件不存在
            DirectoryNotFoundError: 如果目标目录无法创建
            FileOperationError: 如果复制操作失败
        """
        try:
            # 检查源文件是否存在
            source_file = Path(source_path)
            if not source_file.exists():
                raise FileNotFoundError(f"源文件不存在: {source_path}")

            # 生成目标路径
            target_directory = self.directory_manager.get_target_path(person, file_type)

            # 使用命名引擎生成文件名
            new_filename = self.naming_engine.generate_name(
                original_filename=str(source_file), person=person, file_type=file_type
            )

            # 构建完整目标路径
            target_file = Path(target_directory) / new_filename

            # 处理文件名冲突
            if target_file.exists():
                target_file = self._handle_duplicate(target_file)

            # 根据选项决定是否创建目录
            if self.options["create_directories"]:
                os.makedirs(target_file.parent, exist_ok=True)
            elif not target_file.parent.exists():
                raise DirectoryNotFoundError(
                    f"目标目录不存在且未启用自动创建: {target_file.parent}"
                )

            # 根据选项决定复制方式
            if self.options["preserve_timestamps"]:
                shutil.copy2(source_file, target_file)  # 保留元数据
            else:
                shutil.copy(source_file, target_file)  # 不保留元数据

            # 创建并返回操作结果
            result = FileOperationResult(
                success=True,
                message=f"文件成功复制到 {target_file}",
                source_path=str(source_file),
                destination_path=str(target_file),
                operation_type="copy",
            )
            self._record_operation(result)

            # 根据选项决定是否打开文件
            if self.options["open_after_operation"]:
                self._open_file(target_file)

            return result

        except (FileNotFoundError, FileExistsError) as e:
            # 重新抛出特定异常
            raise e
        except Exception as e:
            # 将其他所有异常包装为FileOperationError
            error_msg = f"复制文件时发生错误: {str(e)}"
            logger.error(error_msg)
            raise FileOperationError(error_msg) from e

    @with_error_handling("move_file")
    def move_file(
        self, source_path: str, person: Dict[str, Any], file_type: Dict[str, Any]
    ) -> FileOperationResult:
        """
        移动文件到指定人员和文件类型的目录，并根据命名规则重命名。

        Args:
            source_path: 源文件路径
            person: 目标人员信息
            file_type: 目标文件类型信息

        Returns:
            FileOperationResult: 操作结果对象

        Raises:
            FileNotFoundError: 如果源文件不存在
            DirectoryNotFoundError: 如果目标目录无法创建
            FileOperationError: 如果移动操作失败
        """
        try:
            # 检查源文件是否存在
            source_file = Path(source_path)
            if not source_file.exists():
                raise FileNotFoundError(f"源文件不存在: {source_path}")

            # 生成目标路径
            target_directory = self.directory_manager.get_target_path(person, file_type)

            # 使用命名引擎生成文件名
            new_filename = self.naming_engine.generate_name(
                original_filename=str(source_file), person=person, file_type=file_type
            )

            # 构建完整目标路径
            target_file = Path(target_directory) / new_filename

            # 处理文件名冲突
            if target_file.exists():
                target_file = self._handle_duplicate(target_file)

            # 根据选项决定是否创建目录
            if self.options["create_directories"]:
                os.makedirs(target_file.parent, exist_ok=True)
            elif not target_file.parent.exists():
                raise DirectoryNotFoundError(
                    f"目标目录不存在且未启用自动创建: {target_file.parent}"
                )

            # 根据选项决定移动方式
            if self.options["preserve_timestamps"]:
                # 先复制保留元数据，再删除源文件
                shutil.copy2(source_file, target_file)
                os.remove(source_file)
            else:
                shutil.move(source_file, target_file)

            # 创建并返回操作结果
            result = FileOperationResult(
                success=True,
                message=f"文件成功移动到 {target_file}",
                source_path=str(source_file),
                destination_path=str(target_file),
                operation_type="move",
            )
            self._record_operation(result)

            # 根据选项决定是否打开文件
            if self.options["open_after_operation"]:
                self._open_file(target_file)

            return result

        except (FileNotFoundError, FileExistsError) as e:
            # 重新抛出特定异常
            raise e
        except Exception as e:
            # 将其他所有异常包装为FileOperationError
            error_msg = f"移动文件时发生错误: {str(e)}"
            logger.error(error_msg)
            raise FileOperationError(error_msg) from e

    @with_error_handling("rename_file")
    def rename_file(self, source_path: str, new_name: str) -> FileOperationResult:
        """
        重命名文件。

        Args:
            source_path: 源文件路径
            new_name: 新文件名（不含路径）

        Returns:
            FileOperationResult: 操作结果对象

        Raises:
            FileNotFoundError: 如果源文件不存在
            FileExistsError: 如果目标文件已存在
            FileOperationError: 如果重命名操作失败
        """
        try:
            # 检查源文件是否存在
            source_file = Path(source_path)
            if not source_file.exists():
                raise FileNotFoundError(f"源文件不存在: {source_file}")

            # 构建目标路径
            if not new_name or new_name in {".", ".."} or "/" in new_name or "\\" in new_name:
                raise FileOperationError("新文件名必须是单个文件名，不能包含目录路径")
            target_file = source_file.parent / new_name

            # 检查目标文件是否已存在
            if target_file.exists():
                raise FileExistsError(f"目标文件已存在: {target_file}")

            # 执行重命名操作
            source_file.rename(target_file)

            # 创建并返回操作结果
            result = FileOperationResult(
                success=True,
                message=f"文件成功重命名为 {target_file.name}",
                source_path=str(source_file),
                destination_path=str(target_file),
                operation_type="rename",
            )
            self._record_operation(result)
            return result

        except (FileNotFoundError, FileExistsError) as e:
            # 重新抛出特定异常
            raise e
        except Exception as e:
            # 将其他所有异常包装为FileOperationError
            error_msg = f"重命名文件时发生错误: {str(e)}"
            logger.error(error_msg)
            raise FileOperationError(error_msg) from e

    @with_error_handling("process_file")
    def process_file(
        self,
        source_path: str,
        person: Dict[str, Any],
        file_type: Dict[str, Any],
        copy: Optional[bool] = None,
    ) -> FileOperationResult:
        """
        处理文件 - 根据配置或参数决定复制或移动文件。

        Args:
            source_path: 源文件路径
            person: 目标人员信息
            file_type: 目标文件类型信息
            copy: 是否复制文件，如果为None则使用配置中的copy_files选项

        Returns:
            FileOperationResult: 操作结果对象
        """
        # 确定是否复制文件
        should_copy = copy if copy is not None else self.options["copy_files"]

        if should_copy:
            return self.copy_file(source_path, person, file_type)
        else:
            return self.move_file(source_path, person, file_type)

    def set_naming_pattern(self, pattern: str) -> None:
        """
        设置文件命名模式。

        Args:
            pattern: 新的命名模式
        """
        self.naming_engine = NamingEngine(pattern)
        logger.info(f"已更新文件命名模式: {pattern}")

    def get_naming_pattern(self) -> str:
        """
        获取当前文件命名模式。

        Returns:
            str: 当前命名模式
        """
        return self.naming_engine.pattern

    def get_supported_placeholders(self) -> Dict[str, str]:
        """
        获取支持的命名占位符列表。

        Returns:
            Dict[str, str]: 占位符及其描述字典
        """
        return self.naming_engine.get_supported_placeholders()

    @with_error_handling("handle_duplicate")
    def _handle_duplicate(self, file_path: Path) -> Path:
        """
        处理文件名冲突，如果目标文件已存在，则添加计数后缀。

        Args:
            file_path: 文件路径对象

        Returns:
            Path: 不冲突的文件路径
        """
        if not file_path.exists():
            return file_path

        # 分离文件名和扩展名
        name = file_path.stem
        ext = file_path.suffix
        parent = file_path.parent

        # 尝试添加计数后缀
        counter = 1
        while True:
            new_path = parent / f"{name}_{counter}{ext}"
            if not new_path.exists():
                return new_path
            counter += 1

    def _record_operation(self, result: FileOperationResult) -> None:
        """
        记录操作历史。

        Args:
            result: 操作结果对象
        """
        if result.destination_path and Path(result.destination_path).is_file():
            result.destination_sha256 = self._fingerprint(Path(result.destination_path))
        self._history.append(result)
        logger.info(str(result))

    @staticmethod
    def _fingerprint(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def get_operation_history(self) -> list[FileOperationResult]:
        """
        获取操作历史。

        Returns:
            list[FileOperationResult]: 操作历史列表
        """
        return self._history.copy()

    @with_error_handling("undo_operation")
    def undo_last_operation(self) -> Optional[FileOperationResult]:
        """
        撤销最后一次操作。

        Returns:
            Optional[FileOperationResult]: 撤销操作的结果，如果没有操作可撤销则返回None
        """
        # 检查是否有可以撤销的操作
        if not self._history:
            logger.warning("没有可以撤销的操作")
            return None

        # 获取最后一次操作
        last_operation = self._history[-1]

        try:
            target = Path(last_operation.destination_path or "")
            expected = getattr(last_operation, "destination_sha256", None)
            if expected and target.is_file() and self._fingerprint(target) != expected:
                raise FileOperationError("目标文件在操作后发生变化，拒绝自动撤销以保留修改")
            # 根据操作类型执行相应的撤销操作
            if last_operation.operation_type == "copy" and last_operation.success:
                return self._undo_copy_operation(last_operation)
            elif last_operation.operation_type == "move" and last_operation.success:
                return self._undo_move_operation(last_operation)
            elif last_operation.operation_type == "rename" and last_operation.success:
                return self._undo_rename_operation(last_operation)
            else:
                # 操作类型不支持撤销或操作未成功
                logger.warning(
                    f"不支持的撤销操作类型或操作未成功完成: "
                    f"{last_operation.operation_type}, success={last_operation.success}"
                )
                return None

        except Exception as e:
            # 撤销操作失败
            error_msg = f"撤销操作时发生错误: {str(e)}"
            logger.error(error_msg)
            return FileOperationResult(
                success=False,
                message=error_msg,
                source_path=last_operation.source_path,
                destination_path=last_operation.destination_path,
                operation_type=f"undo_{last_operation.operation_type}",
                error=e,
            )

    def _undo_copy_operation(self, operation: FileOperationResult) -> Optional[FileOperationResult]:
        """
        撤销复制操作。

        Args:
            operation: 要撤销的操作结果

        Returns:
            Optional[FileOperationResult]: 撤销操作的结果，如果无法撤销则返回None
        """
        # 删除复制的文件
        dest_file = Path(operation.destination_path)
        if dest_file.exists():
            os.remove(dest_file)

            # 记录撤销结果
            result = FileOperationResult(
                success=True,
                message="成功撤销复制操作，已删除目标文件",
                source_path=operation.source_path,
                destination_path=operation.destination_path,
                operation_type="undo_copy",
            )
            # 从历史记录中移除
            self._history.pop()
            return result
        else:
            # 目标文件不存在，无法撤销
            logger.warning(f"无法撤销复制操作，目标文件不存在: {dest_file}")
            return None

    def _undo_move_operation(self, operation: FileOperationResult) -> Optional[FileOperationResult]:
        """
        撤销移动操作。

        Args:
            operation: 要撤销的操作结果

        Returns:
            Optional[FileOperationResult]: 撤销操作的结果，如果无法撤销则返回None
        """
        # 将文件移回原始位置
        dest_file = Path(operation.destination_path)
        source_file = Path(operation.source_path)

        if dest_file.exists() and not source_file.exists():
            # 确保源目录存在
            source_file.parent.mkdir(parents=True, exist_ok=True)
            # 移动回原位置
            shutil.move(dest_file, source_file)

            # 记录撤销结果
            result = FileOperationResult(
                success=True,
                message="成功撤销移动操作，已将文件移回原位置",
                source_path=operation.destination_path,
                destination_path=operation.source_path,
                operation_type="undo_move",
            )
            # 从历史记录中移除
            self._history.pop()
            return result
        else:
            # 文件状态不允许撤销
            if not dest_file.exists():
                logger.warning(f"无法撤销移动操作，目标文件不存在: {dest_file}")
            if source_file.exists():
                logger.warning(f"无法撤销移动操作，源文件位置已有文件: {source_file}")
            return None

    def _undo_rename_operation(self, operation: FileOperationResult) -> Optional[FileOperationResult]:
        """
        撤销重命名操作。

        Args:
            operation: 要撤销的操作结果

        Returns:
            Optional[FileOperationResult]: 撤销操作的结果，如果无法撤销则返回None
        """
        # 将文件改回原始名称
        renamed_file = Path(operation.destination_path)
        original_file = Path(operation.source_path)

        if renamed_file.exists() and not original_file.exists():
            # 重命名回原名称
            renamed_file.rename(original_file)

            # 记录撤销结果
            result = FileOperationResult(
                success=True,
                message="成功撤销重命名操作，已将文件改回原名称",
                source_path=operation.destination_path,
                destination_path=operation.source_path,
                operation_type="undo_rename",
            )
            # 从历史记录中移除
            self._history.pop()
            return result
        else:
            # 文件状态不允许撤销
            if not renamed_file.exists():
                path = str(renamed_file)
                logger.warning(f"无法撤销重命名操作，重命名后的文件不存在: {path}")
            if original_file.exists():
                path = str(original_file)
                logger.warning(f"无法撤销重命名操作，原始文件位置已有文件: {path}")
            return None

    def get_recent_errors(self, limit: int = 10):
        """
        获取最近的错误记录。

        Args:
            limit: 最大记录数

        Returns:
            最近的错误记录列表
        """
        if self.error_handler:
            return self.error_handler.logger.get_recent_errors(limit)
        return []

    def clear_resolved_errors(self):
        """清除已解决的错误记录。"""
        if self.error_handler:
            self.error_handler.logger.clear_resolved_errors()

    def _open_file(self, file_path: Path):
        """
        打开文件夹。

        Args:
            file_path: 文件路径对象
        """
        try:
            directory_path = file_path.parent
            os.startfile(directory_path)
        except Exception as e:
            error_msg = f"打开文件夹时发生错误: {str(e)}"
            logger.error(error_msg)
            raise FileOperationError(error_msg) from e

    def update_options(self, new_options: Dict[str, Any]) -> None:
        """
        更新文件管理器选项。

        Args:
            new_options: 新的选项字典，将与现有选项合并

        Raises:
            ConfigurationError: 如果提供了无效的选项或尝试更新不允许修改的选项
        """
        # 验证选项
        valid_options = {
            "copy_files": bool,
            "create_directories": bool,
            "open_after_operation": bool,
            "preserve_timestamps": bool,
        }

        # 检查是否尝试更新directory_template选项
        # if 'directory_template' in new_options:
        #     raise ConfigurationError("不允许修改目录模板(directory_template)选项")

        # 检查选项类型
        for key, value in new_options.items():
            if key not in valid_options:
                raise ConfigurationError(f"无效的选项: {key}")
            if not isinstance(value, valid_options[key]):
                raise ConfigurationError(
                    f"选项 {key} 的类型应为 {valid_options[key].__name__}，而不是 {type(value).__name__}"
                )

        # 更新选项
        self.options.update(new_options)
        logger.info(f"已更新文件管理器选项: {new_options}")

    def get_options(self) -> Dict[str, Any]:
        """
        获取当前文件管理器选项。

        Returns:
            Dict[str, Any]: 当前选项的副本
        """
        return self.options.copy()

    def copy_directory(
        self, source_path: str, person: Dict[str, Any], file_type: Dict[str, Any]
    ) -> FileOperationResult:
        """
        复制整个目录到指定人员和文件类型的位置，只重命名目录本身，保持内部文件结构不变。

        Args:
            source_path: 源目录路径
            person: 目标人员信息
            file_type: 目标文件类型信息

        Returns:
            FileOperationResult: 操作结果对象

        Raises:
            FileNotFoundError: 如果源目录不存在
            DirectoryNotFoundError: 如果目标目录无法创建
            FileOperationError: 如果复制操作失败
        """
        try:
            # 检查源目录是否存在
            source_dir = Path(source_path)
            if not source_dir.exists() or not source_dir.is_dir():
                raise FileNotFoundError(f"源目录不存在: {source_path}")

            # 生成目标路径
            target_directory = self.directory_manager.get_target_path(person, file_type)

            # 使用命名引擎生成目录名
            new_dirname = self.naming_engine.generate_name(
                original_filename=source_dir.name, person=person, file_type=file_type
            )

            # 构建完整目标路径
            target_dir = Path(target_directory) / new_dirname

            # 处理目录名冲突
            if target_dir.exists():
                target_dir = self._handle_duplicate(target_dir)

            # 根据选项决定是否创建目录
            if self.options["create_directories"]:
                os.makedirs(target_dir.parent, exist_ok=True)
            elif not target_dir.parent.exists():
                raise DirectoryNotFoundError(f"目标目录不存在且未启用自动创建: {target_dir.parent}")

            # 复制整个目录，保持内部结构不变
            shutil.copytree(source_dir, target_dir)

            # 创建并返回操作结果
            result = FileOperationResult(
                success=True,
                message=f"目录成功复制到 {target_dir}",
                source_path=str(source_dir),
                destination_path=str(target_dir),
                operation_type="copy_directory",
            )
            self._record_operation(result)

            # 根据选项决定是否打开目录
            if self.options["open_after_operation"]:
                self._open_file(target_dir)

            return result

        except (FileNotFoundError, FileExistsError) as e:
            # 重新抛出特定异常
            raise e
        except Exception as e:
            # 将其他所有异常包装为FileOperationError
            error_msg = f"复制目录时发生错误: {str(e)}"
            logger.error(error_msg)
            raise FileOperationError(error_msg) from e

    def move_directory(
        self, source_path: str, person: Dict[str, Any], file_type: Dict[str, Any]
    ) -> FileOperationResult:
        """
        移动整个目录到指定人员和文件类型的位置，只重命名目录本身，保持内部文件结构不变。

        Args:
            source_path: 源目录路径
            person: 目标人员信息
            file_type: 目标文件类型信息

        Returns:
            FileOperationResult: 操作结果对象

        Raises:
            FileNotFoundError: 如果源目录不存在
            DirectoryNotFoundError: 如果目标目录无法创建
            FileOperationError: 如果移动操作失败
        """
        try:
            # 检查源目录是否存在
            source_dir = Path(source_path)
            if not source_dir.exists() or not source_dir.is_dir():
                raise FileNotFoundError(f"源目录不存在: {source_path}")

            # 生成目标路径
            target_directory = self.directory_manager.get_target_path(person, file_type)

            # 使用命名引擎生成目录名
            new_dirname = self.naming_engine.generate_name(
                original_filename=source_dir.name, person=person, file_type=file_type
            )

            # 构建完整目标路径
            target_dir = Path(target_directory) / new_dirname

            # 处理目录名冲突
            if target_dir.exists():
                target_dir = self._handle_duplicate(target_dir)

            # 根据选项决定是否创建目录
            if self.options["create_directories"]:
                os.makedirs(target_dir.parent, exist_ok=True)
            elif not target_dir.parent.exists():
                raise DirectoryNotFoundError(f"目标目录不存在且未启用自动创建: {target_dir.parent}")

            # 移动整个目录，保持内部结构不变
            shutil.move(source_dir, target_dir)

            # 创建并返回操作结果
            result = FileOperationResult(
                success=True,
                message=f"目录成功移动到 {target_dir}",
                source_path=str(source_dir),
                destination_path=str(target_dir),
                operation_type="move_directory",
            )
            self._record_operation(result)

            # 根据选项决定是否打开目录
            if self.options["open_after_operation"]:
                self._open_file(target_dir)

            return result

        except (FileNotFoundError, FileExistsError) as e:
            # 重新抛出特定异常
            raise e
        except Exception as e:
            # 将其他所有异常包装为FileOperationError
            error_msg = f"移动目录时发生错误: {str(e)}"
            logger.error(error_msg)
            raise FileOperationError(error_msg) from e
