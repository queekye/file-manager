#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
人员选择界面模块，提供带搜索功能的人员选择界面。PyQt5实现版本。
"""

import os
from typing import Any, Dict, List, Optional

from loguru import logger
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from src.core.person_manager import PersonManager
from src.windows.ui.search_engine import PersonSearchEngine
from src.windows.ui.style_config import get_column_widths, get_style_sheets, get_window_size


class PersonSelector:
    """人员选择界面，支持全名、拼音全拼和拼音首字母搜索。"""

    def __init__(
        self,
        persons: Optional[List[Dict[str, Any]]] = None,
        person_manager: Optional[PersonManager] = None,
        title: str = "选择人员",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化人员选择界面。

        Args:
            persons: 人员列表，每个人员为包含id和name的字典，如果提供了person_manager则可以不提供
            person_manager: 人员管理器，用于添加新人员和获取人员列表
            title: 窗口标题
            config: 配置对象，包含人员字段定义等配置信息
        """
        # 如果没有提供person_manager，则创建一个新的
        if not person_manager:
            person_manager = PersonManager(config=config)

        self.person_manager = person_manager
        self.config = config

        # 如果提供了person_manager但没有提供persons，则从person_manager获取
        if person_manager and persons is None:
            self.persons = person_manager.get_all_persons()
        else:
            self.persons = persons or []

        self.title = title
        self.selected_person_id = None

        # 创建搜索引擎
        self.search_engine = PersonSearchEngine(self.persons)

    def log_info(self, message: str) -> None:
        """记录信息日志。"""
        logger.info(message)

    def log_error(self, message: str, exc_info: Optional[Exception] = None) -> None:
        """记录错误日志。"""
        if exc_info:
            logger.exception(f"{message}: {exc_info}")
        else:
            logger.error(message)

    def show(self) -> Optional[str]:
        """
        显示人员选择界面。

        Returns:
            选择的人员ID，如果取消则返回None
        """
        try:
            # 创建对话框
            dialog = PersonSelectorDialog(
                self.persons, self.title, self.search_engine, self.person_manager
            )

            # 显示对话框并获取结果
            if dialog.exec_() == QDialog.Accepted:
                self.selected_person_id = dialog.result
                self.log_info(f"已选择人员ID: {self.selected_person_id}")
            else:
                self.selected_person_id = None
                self.log_info("用户取消选择人员")

            return self.selected_person_id

        except Exception as e:
            self.log_error("显示人员选择界面时发生错误", e)
            return None


class PersonSelectorDialog(QDialog):
    """人员选择对话框类，处理人员选择界面的显示和交互。"""

    def __init__(
        self,
        persons: List[Dict[str, Any]],
        title: str,
        search_engine: PersonSearchEngine,
        person_manager: Optional[PersonManager] = None,
    ):
        """
        初始化人员选择对话框。

        Args:
            persons: 人员列表
            title: 窗口标题
            search_engine: 人员搜索引擎
            person_manager: 人员管理器，用于添加新人员
        """
        super().__init__()

        self.persons = persons
        self.search_engine = search_engine
        self.person_manager = person_manager
        self.result = None

        # 设置窗口标题和大小
        self.setWindowTitle(title)
        width, height = get_window_size("person_selector")
        self.resize(width, height)

        # 设置样式
        self.setStyleSheet(get_style_sheets()["main_window"])

        # 创建界面
        self._create_widgets()

        # 填充人员列表
        self._populate_person_list()

    def _create_widgets(self) -> None:
        """创建界面控件。"""
        try:
            # 创建主布局
            layout = QVBoxLayout()

            # 创建目录选择区域
            if self.person_manager and hasattr(self.person_manager.config, "get_base_directory"):
                dir_layout = QHBoxLayout()

                # 显示当前目录
                dir_label = QLabel("当前目录:")
                self.current_dir_label = QLabel(self.person_manager.config.get_base_directory())
                self.current_dir_label.setStyleSheet("font-weight: bold;")

                # 创建目录切换按钮
                switch_dir_button = QPushButton("切换目录")
                switch_dir_button.clicked.connect(self._on_switch_directory)

                dir_layout.addWidget(dir_label)
                dir_layout.addWidget(self.current_dir_label)
                dir_layout.addStretch()
                dir_layout.addWidget(switch_dir_button)

                layout.addLayout(dir_layout)

            # 创建搜索框
            search_layout = QHBoxLayout()
            search_label = QLabel("搜索:")
            self.search_edit = QLineEdit()
            self.search_edit.textChanged.connect(self._on_search)
            search_layout.addWidget(search_label)
            search_layout.addWidget(self.search_edit)
            layout.addLayout(search_layout)

            # 创建帮助标签
            help_label = QLabel("支持全名、拼音全拼、拼音首字母搜索")
            help_label.setStyleSheet(get_style_sheets()["tip_label"])
            layout.addWidget(help_label)

            # 创建人员列表
            self.tree = QTreeWidget()
            self.tree.setHeaderLabels(["ID", "姓名", "目录名"])

            # 设置列宽
            widths = get_column_widths()["person_fields"]
            self.tree.setColumnWidth(0, widths["id"])
            self.tree.setColumnWidth(1, widths["name"])
            self.tree.setColumnWidth(2, widths["name"] + 50)  # 目录名列宽稍大一些

            layout.addWidget(self.tree)

            # 双击处理
            self.tree.itemDoubleClicked.connect(self._on_ok)

            # 创建按钮布局
            button_layout = QHBoxLayout()

            # 如果有人员管理器，添加"添加人员"、"扫描人员"和"删除人员"按钮
            if self.person_manager:
                add_button = QPushButton("添加人员")
                add_button.clicked.connect(self._on_add_person)
                button_layout.addWidget(add_button)

                scan_button = QPushButton("扫描人员")
                scan_button.clicked.connect(self._on_scan_persons)
                button_layout.addWidget(scan_button)

                delete_button = QPushButton("删除人员")
                delete_button.clicked.connect(self._on_delete_person)
                button_layout.addWidget(delete_button)

            # 添加弹簧
            button_layout.addStretch()

            # 创建确定和取消按钮
            self.ok_button = QPushButton("确定")
            self.ok_button.clicked.connect(self._on_ok)
            button_layout.addWidget(self.ok_button)

            self.cancel_button = QPushButton("取消")
            self.cancel_button.clicked.connect(self.reject)
            button_layout.addWidget(self.cancel_button)

            # 添加按钮布局
            layout.addLayout(button_layout)

            # 设置主布局
            self.setLayout(layout)

            # 设置初始焦点
            self.search_edit.setFocus()

        except Exception as e:
            logger.error("创建界面控件时发生错误", exc_info=True)

    def _populate_person_list(self, persons: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        填充人员列表。

        Args:
            persons: 人员列表，如果为None则使用所有人员
        """
        try:
            # 清空列表
            self.tree.clear()

            # 如果没有指定人员列表，使用所有人员
            if persons is None:
                persons = self.persons

            # 添加人员到列表
            for person in persons:
                person_id = person.get("id", "")
                person_name = person.get("name", "")
                person_directory = person.get("directory", "")

                item = QTreeWidgetItem([person_id, person_name, person_directory])
                self.tree.addTopLevelItem(item)

            # 如果有人员，选中第一个
            if self.tree.topLevelItemCount() > 0:
                first_item = self.tree.topLevelItem(0)
                self.tree.setCurrentItem(first_item)

        except Exception as e:
            logger.error("填充人员列表时发生错误", exc_info=True)

    def _on_search(self) -> None:
        """处理搜索事件。"""
        try:
            # 获取搜索关键词
            query = self.search_edit.text()

            # 搜索人员
            if query:
                search_results = self.search_engine.search(query)
                self._populate_person_list(search_results)
            else:
                self._populate_person_list(self.persons)

        except Exception as e:
            logger.error("搜索人员时发生错误", exc_info=True)

    def _on_add_person(self) -> None:
        """处理添加人员按钮点击事件。"""
        try:
            if not self.person_manager:
                QMessageBox.critical(self, "错误", "未提供人员管理器，无法添加人员")
                return

            # 创建添加人员对话框
            dialog = PersonAddDialog(self, self.person_manager)

            # 显示对话框并等待结果
            if dialog.exec_() == QDialog.Accepted and dialog.result:
                # 更新人员列表
                self.persons = self.person_manager.get_all_persons()
                logger.info(f"更新人员列表为： {len(self.persons)}人")

                # 直接添加新人员到搜索引擎索引
                self.search_engine.add_person(
                    {
                        "id": dialog.result.get("id", ""),
                        "name": dialog.result.get("name", ""),
                        "directory": dialog.result.get("directory", ""),
                    }
                )

                # 刷新列表显示
                self._populate_person_list()

                # 提示添加成功
                QMessageBox.information(
                    self, "提示", f"已成功添加人员: {dialog.result.get('name', '')}"
                )

        except Exception as e:
            logger.error("处理添加人员按钮点击事件时发生错误", exc_info=True)

    def _on_delete_person(self) -> None:
        """处理删除人员按钮点击事件。"""
        try:
            if not self.person_manager:
                QMessageBox.critical(self, "错误", "未提供人员管理器，无法删除人员")
                return

            # 获取选中的人员
            current_item = self.tree.currentItem()
            if not current_item:
                QMessageBox.information(self, "提示", "请选择要删除的人员")
                return

            # 获取人员信息
            person_id = current_item.text(0)
            person_name = current_item.text(1)
            person_directory = current_item.text(2)

            # 确认删除
            if (
                QMessageBox.question(
                    self,
                    "确认删除",
                    f"确定要删除人员 {person_name} (ID: {person_id}) 吗？\n此操作不可恢复！",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                == QMessageBox.Yes
            ):
                # 执行删除
                if self.person_manager.delete_person(person_id):
                    # 更新人员列表
                    self.persons = self.person_manager.get_all_persons()

                    # 从搜索引擎中移除
                    self.search_engine.remove_person(person_id)

                    # 刷新列表显示
                    self._populate_person_list()

                    # 提示删除成功
                    QMessageBox.information(
                        self,
                        "提示",
                        f"已成功删除人员: {person_name}\n\n"
                        f"注意：目录 '{person_directory}' 下的文件不会自动删除，\n"
                        "如有需要请手动删除相关文件。",
                    )
                else:
                    QMessageBox.critical(self, "错误", f"删除人员失败: {person_name}")

        except Exception as e:
            logger.error("处理删除人员按钮点击事件时发生错误", exc_info=True)
            QMessageBox.critical(self, "错误", f"删除人员时发生错误: {str(e)}")

    def _on_ok(self) -> None:
        """处理确定按钮点击事件。"""
        try:
            # 获取选中的人员
            current_item = self.tree.currentItem()

            if current_item:
                # 获取人员ID
                person_id = current_item.text(0)

                # 设置结果
                self.result = person_id

                # 接受对话框
                self.accept()
            else:
                QMessageBox.information(self, "提示", "请选择一个人员")

        except Exception as e:
            logger.error("处理确定按钮点击事件时发生错误", exc_info=True)

    def _on_scan_persons(self) -> None:
        """处理扫描人员按钮点击事件。"""
        try:
            if not self.person_manager:
                QMessageBox.critical(self, "错误", "未提供人员管理器，无法扫描人员")
                return

            # 获取默认目录
            default_dir = ""
            if self.person_manager.config and hasattr(
                self.person_manager.config, "get_base_directory"
            ):
                default_dir = self.person_manager.config.get_base_directory()
                logger.debug(f"使用配置的默认目录: {default_dir}")

            # 选择要扫描的目录
            base_dir = QFileDialog.getExistingDirectory(
                self,
                "选择要扫描的目录",
                default_dir,
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
            )

            if not base_dir:
                return

            logger.info(f"开始扫描目录: {base_dir}")

            # 创建进度对话框
            progress = QProgressDialog("正在扫描目录...", "取消", 0, 100, self)
            progress.setWindowTitle("扫描进度")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)

            try:
                # 获取目录下的所有文件夹
                subdirs = [
                    d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))
                ]
                total = len(subdirs)

                if total == 0:
                    QMessageBox.information(self, "提示", "所选目录下没有子目录")
                    return

                added_count = 0
                skipped_count = 0

                # 遍历所有文件夹
                for i, dir_name in enumerate(subdirs):
                    # 更新进度
                    progress.setValue(int((i + 1) * 100 / total))

                    # 检查是否取消
                    if progress.wasCanceled():
                        break

                    # 检查目录名是否已存在
                    existing_persons = self.person_manager.get_all_persons()
                    if any(p.get("directory") == dir_name for p in existing_persons):
                        logger.debug(f"跳过已存在的目录: {dir_name}")
                        skipped_count += 1
                        continue

                    try:
                        # 添加新人员
                        new_person = self.person_manager.add_person(dir_name, dir_name)
                        added_count += 1
                        # 直接添加新人员到搜索引擎索引
                        self.search_engine.add_person(new_person)
                        logger.info(f"添加新人员: {dir_name}")
                    except Exception as e:
                        logger.error(f"添加人员失败: {dir_name}, {str(e)}")

                # 关闭进度对话框
                progress.close()

                # 更新人员列表
                self.persons = self.person_manager.get_all_persons()
                self._populate_person_list()

                # 显示结果
                QMessageBox.information(
                    self,
                    "扫描完成",
                    f"扫描完成！\n\n"
                    f"共扫描到 {total} 个目录\n"
                    f"新增 {added_count} 个人员\n"
                    f"跳过 {skipped_count} 个已存在的目录",
                )

            except Exception as e:
                progress.close()
                logger.error(f"扫描目录时发生错误: {str(e)}", exc_info=True)
                QMessageBox.critical(self, "错误", f"扫描目录时发生错误: {str(e)}")

        except Exception as e:
            logger.error(f"处理扫描人员按钮点击事件时发生错误: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "错误", "处理扫描人员功能时发生错误")

    def _on_switch_directory(self) -> None:
        """处理切换目录按钮点击事件。"""
        try:
            if not self.person_manager or not hasattr(
                self.person_manager.config, "base_directories"
            ):
                return

            # 创建目录选择菜单
            menu = QMenu(self)

            # 添加所有可用目录
            for directory in self.person_manager.config.base_directories:
                action = menu.addAction(directory)
                action.setCheckable(True)
                action.setChecked(directory == self.person_manager.config.get_base_directory())

                # 使用 lambda 来传递目录参数
                action.triggered.connect(
                    lambda checked, d=directory: self._on_directory_selected(d)
                )

            # 在按钮位置显示菜单
            button = self.sender()
            menu.exec_(button.mapToGlobal(button.rect().bottomLeft()))

        except Exception as e:
            logger.error(f"切换目录时发生错误: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "错误", f"切换目录时发生错误: {str(e)}")

    def _on_directory_selected(self, directory: str) -> None:
        """处理目录选择事件。"""
        try:
            if self.person_manager.config.set_base_directory(directory):
                # 更新界面显示
                self.person_manager.config.save()
                self.current_dir_label.setText(directory)

                # 更新 PersonManager 的目录管理器
                self.person_manager.update_directory_manager()
                logger.info(f"已切换到目录: {directory}")
            else:
                logger.error(f"切换目录失败: {directory}")
                QMessageBox.critical(self, "错误", f"切换到目录 {directory} 失败")
        except Exception as e:
            logger.error(f"选择目录时发生错误: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "错误", f"选择目录时发生错误: {str(e)}")


class PersonAddDialog(QDialog):
    """人员添加对话框类，处理人员添加界面的显示和交互。"""

    def __init__(self, parent: QDialog, person_manager: PersonManager):
        """
        初始化人员添加对话框。

        Args:
            parent: 父窗口
            person_manager: 人员管理器
        """
        super().__init__(parent)

        if not person_manager:
            raise ValueError("必须提供person_manager参数")

        self.person_manager = person_manager
        self.result = None
        self.field_widgets = {}  # 存储字段控件的字典

        # 设置窗口属性
        self.setWindowTitle("添加新人员")
        self.setStyleSheet(get_style_sheets()["main_window"])
        width, height = get_window_size("person_selector")  # 使用相同的基准尺寸
        self.resize(int(width * 0.8), int(height * 0.7))  # 稍微小一点
        self.setModal(True)

        # 创建界面
        self._create_widgets()

    def _create_widgets(self) -> None:
        """创建界面控件。"""
        try:
            # 创建主布局
            layout = QVBoxLayout()

            # 创建表单布局
            form_layout = QFormLayout()

            # 添加必填字段：姓名
            self.name_edit = QLineEdit()
            name_label = QLabel("姓名:")
            name_label.setStyleSheet("color: red")  # 标记为必填
            form_layout.addRow(name_label, self.name_edit)

            # 添加必填字段：目录名
            self.directory_edit = QLineEdit()
            directory_label = QLabel("目录名:")
            directory_label.setStyleSheet("color: red")  # 标记为必填
            form_layout.addRow(directory_label, self.directory_edit)

            # 从配置中获取并添加其他字段
            config = self.person_manager.config or {}
            config_fields = config.person_fields
            logger.info(f"从配置中读取到 {len(config_fields)} 个字段")

            for field in config_fields:
                try:
                    field_id = field.get("id")
                    if not field_id:
                        logger.warning(f"跳过没有id的字段: {field}")
                        continue

                    field_name = field.get("name", field_id)
                    field_required = field.get("required", False)
                    field_default = field.get("default_value", "")
                    field_description = field.get("description", "")

                    # 创建输入框
                    edit = QLineEdit()
                    edit.setText(field_default)
                    self.field_widgets[field_id] = edit

                    # 创建标签
                    label = QLabel(f"{field_name}:")
                    if field_required:
                        label.setStyleSheet("color: red")
                    if field_description:
                        label.setToolTip(field_description)

                    # 添加到表单
                    form_layout.addRow(label, edit)
                    logger.debug(f"添加字段: {field_id} ({field_name})")
                except Exception as e:
                    logger.error(f"处理字段时发生错误: {field}, {str(e)}")

            # 添加表单布局
            layout.addLayout(form_layout)

            # 创建按钮布局
            button_layout = QHBoxLayout()
            button_layout.addStretch()

            # 创建确定和取消按钮
            ok_button = QPushButton("确定")
            ok_button.clicked.connect(self.accept)
            button_layout.addWidget(ok_button)

            cancel_button = QPushButton("取消")
            cancel_button.clicked.connect(self.reject)
            button_layout.addWidget(cancel_button)

            # 添加按钮布局
            layout.addLayout(button_layout)

            # 设置主布局
            self.setLayout(layout)

            # 设置初始焦点
            self.name_edit.setFocus()

        except Exception as e:
            logger.error(f"创建界面控件时发生错误: {str(e)}", exc_info=True)

    def get_person_field(self) -> Dict[str, Any]:
        """获取人员字段数据。"""
        try:
            # 获取基本字段
            field = {
                "name": self.name_edit.text(),
                "directory": self.directory_edit.text(),
            }

            # 获取配置的字段值
            for field_id, widget in self.field_widgets.items():
                value = widget.text()
                if value:  # 只添加非空值
                    field[field_id] = value

            return field
        except Exception as e:
            logger.error(f"获取人员字段数据时发生错误: {str(e)}")
            return {"name": "", "directory": ""}

    def accept(self):
        """验证并接受输入。"""
        try:
            if not self.name_edit.text():
                QMessageBox.warning(self, "警告", "姓名为必填项")
                return

            # 验证其他必填字段
            config = self.person_manager.config or {}
            config_fields = config.person_fields

            for field in config_fields:
                if field.get("required", False):
                    field_id = field.get("id")
                    if field_id in self.field_widgets and not self.field_widgets[field_id].text():
                        QMessageBox.warning(self, "警告", f"{field.get('name', field_id)}为必填项")
                        return

            # 获取人员字段数据
            person_data = self.get_person_field()
            name = person_data.pop("name")
            directory = person_data.pop("directory")

            # 添加人员
            try:
                new_person = self.person_manager.add_person(name, directory, **person_data)
                self.result = new_person
                super().accept()
            except Exception as e:
                logger.error(f"添加人员失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"添加人员失败: {str(e)}")
                return

        except Exception as e:
            logger.error(f"验证输入时发生错误: {str(e)}")
            QMessageBox.critical(self, "错误", "验证输入时发生错误")

    def reject(self):
        """取消输入。"""
        self.done(0)


# 测试代码
if __name__ == "__main__":
    import sys
    from pathlib import Path
    from PyQt5.QtWidgets import QApplication

    import yaml

    # 获取配置文件路径
    config_path = Path(__file__).parent.parent.parent.parent / "resources" / "config.yaml"

    # 加载配置文件
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logger.info(f"成功加载配置文件: {config_path}")
            logger.debug(f"配置内容: {config}")
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        config = {}

    # 创建人员管理器
    person_manager = PersonManager(config=config)

    # 创建应用
    app = QApplication(sys.argv)

    # 创建人员选择器
    selector = PersonSelector(person_manager=person_manager, config=config)

    # 显示人员选择界面
    result = selector.show()

    # 输出结果
    print(f"选择的人员ID: {result}")
