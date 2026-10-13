#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置编辑器界面模块。
"""

from typing import Any, Dict, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.config import Config
from src.core.exceptions import ConfigurationError
from src.windows.ui.hotkey_editor import HotkeyEditor


class ConfigEditor(QWidget):
    """配置编辑器界面类。"""

    def __init__(self, config: Config, hotkey_manager=None, parent: Optional[QWidget] = None):
        """
        初始化配置编辑器界面。

        Args:
            config: 配置对象
            hotkey_manager: 快捷键管理器实例
            parent: 父窗口
        """
        super().__init__(parent)
        self.config = config
        self.hotkey_manager = hotkey_manager
        self.init_ui()

    def init_ui(self):
        """初始化用户界面。"""
        # 设置窗口标题和大小
        self.setWindowTitle("配置编辑器")
        self.resize(1000, 800)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 创建主布局
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # 创建选项卡
        tab_widget = QTabWidget()
        tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(tab_widget)

        # 创建基本设置选项卡
        basic_tab = QWidget()
        basic_layout = QVBoxLayout()
        basic_tab.setLayout(basic_layout)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_content.setLayout(scroll_layout)

        # 基本目录设置
        base_dir_group = QGroupBox("基本目录设置")
        base_dir_layout = QVBoxLayout()
        base_dir_group.setLayout(base_dir_layout)

        # 目录列表
        self.base_dir_list = QListWidget()
        self.base_dir_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.base_dir_list.setMinimumHeight(100)
        for directory in self.config.base_directories:
            item = QListWidgetItem(directory)
            if directory == self.config.current_base_directory:
                item.setBackground(Qt.lightGray)
            self.base_dir_list.addItem(item)
        self.base_dir_list.itemClicked.connect(self.on_directory_selected)

        # 目录管理按钮
        dir_buttons_layout = QHBoxLayout()
        add_dir_button = QPushButton("添加目录")
        add_dir_button.clicked.connect(self.add_base_directory)
        remove_dir_button = QPushButton("移除目录")
        remove_dir_button.clicked.connect(self.remove_base_directory)
        set_current_button = QPushButton("设为当前目录")
        set_current_button.clicked.connect(self.set_current_directory)

        dir_buttons_layout.addWidget(add_dir_button)
        dir_buttons_layout.addWidget(remove_dir_button)
        dir_buttons_layout.addWidget(set_current_button)

        base_dir_layout.addWidget(self.base_dir_list)
        base_dir_layout.addLayout(dir_buttons_layout)

        scroll_layout.addWidget(base_dir_group)

        # 命名模式设置
        naming_group = QGroupBox("命名模式设置")
        naming_layout = QFormLayout()
        naming_group.setLayout(naming_layout)

        self.naming_pattern_edit = QLineEdit(self.config.naming_pattern)
        naming_layout.addRow("命名模式:", self.naming_pattern_edit)

        scroll_layout.addWidget(naming_group)

        # 选项设置
        options_group = QGroupBox("选项设置")
        options_layout = QFormLayout()
        options_group.setLayout(options_layout)

        self.option_widgets = {}

        # 复制文件选项
        self.option_widgets["copy_files"] = QCheckBox()
        self.option_widgets["copy_files"].setChecked(self.config.options.get("copy_files", True))
        options_layout.addRow("复制文件（否则移动）:", self.option_widgets["copy_files"])

        # 自动创建目录选项
        self.option_widgets["create_directories"] = QCheckBox()
        self.option_widgets["create_directories"].setChecked(
            self.config.options.get("create_directories", True)
        )
        options_layout.addRow("自动创建目录:", self.option_widgets["create_directories"])

        # 操作后打开文件夹选项
        self.option_widgets["open_after_operation"] = QCheckBox()
        self.option_widgets["open_after_operation"].setChecked(
            self.config.options.get("open_after_operation", False)
        )
        options_layout.addRow("操作后打开文件夹:", self.option_widgets["open_after_operation"])

        # 保留时间戳选项
        self.option_widgets["preserve_timestamps"] = QCheckBox()
        self.option_widgets["preserve_timestamps"].setChecked(
            self.config.options.get("preserve_timestamps", True)
        )
        options_layout.addRow("保留原始时间戳:", self.option_widgets["preserve_timestamps"])

        # 目录模板选项
        self.option_widgets["directory_template"] = QLineEdit()
        self.option_widgets["directory_template"].setText(
            self.config.options.get("directory_template", "{person}/{type}")
        )
        options_layout.addRow("目录模板:", self.option_widgets["directory_template"])

        # 目录命名模板选项
        self.option_widgets["directory_naming_template"] = QLineEdit()
        self.option_widgets["directory_naming_template"].setText(
            self.config.options.get("directory_naming_template", "{name_pinyin}_{id}")
        )
        options_layout.addRow(
            "人员文件夹命名模板:", self.option_widgets["directory_naming_template"]
        )

        # 自动处理文件名冲突选项
        self.option_widgets["auto_rename_duplicates"] = QCheckBox()
        self.option_widgets["auto_rename_duplicates"].setChecked(
            self.config.options.get("auto_rename_duplicates", True)
        )
        options_layout.addRow("自动处理文件名冲突:", self.option_widgets["auto_rename_duplicates"])

        # 历史记录数量选项
        self.option_widgets["max_history_items"] = QLineEdit()
        self.option_widgets["max_history_items"].setText(
            str(self.config.options.get("max_history_items", 100))
        )
        options_layout.addRow("保留历史记录数量:", self.option_widgets["max_history_items"])

        scroll_layout.addWidget(options_group)

        # 设置滚动区域的内容
        scroll_area.setWidget(scroll_content)
        basic_layout.addWidget(scroll_area)

        # 添加基本设置选项卡
        tab_widget.addTab(basic_tab, "基本设置")

        # 创建文件类型选项卡
        file_types_tab = self.create_file_types_tab()
        tab_widget.addTab(file_types_tab, "文件类型")

        # 创建人员字段选项卡
        person_fields_tab = self.create_person_fields_tab()
        tab_widget.addTab(person_fields_tab, "人员字段")

        # 创建快捷键设置选项卡
        hotkeys_tab = self.create_hotkeys_tab()
        tab_widget.addTab(hotkeys_tab, "快捷键设置")

        # 添加按钮
        button_layout = QHBoxLayout()
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.save_config)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.close)
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)

    def create_file_types_tab(self) -> QWidget:
        """创建文件类型选项卡。"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # 添加提示标签
        tip_label = QLabel("提示：双击列表项可以编辑文件类型")
        tip_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(tip_label)

        # 创建列表和编辑区域
        list_layout = QHBoxLayout()

        # 文件类型列表
        self.file_types_tree = QTreeWidget()
        self.file_types_tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.file_types_tree.setHeaderLabels(["名称", "ID", "目录", "描述"])
        self.file_types_tree.itemDoubleClicked.connect(self.edit_file_type)

        # 设置列宽
        self.file_types_tree.setColumnWidth(0, 180)  # 名称
        self.file_types_tree.setColumnWidth(1, 120)  # ID
        self.file_types_tree.setColumnWidth(2, 180)  # 目录
        self.file_types_tree.setColumnWidth(3, 300)  # 描述

        # 添加现有文件类型
        for ft in self.config.file_types:
            item = QTreeWidgetItem()
            item.setData(0, Qt.UserRole, ft)
            item.setText(0, ft["name"])
            item.setText(1, ft["id"])
            item.setText(2, ft["directory"])
            item.setText(3, ft.get("description", ""))
            self.file_types_tree.addTopLevelItem(item)

        list_layout.addWidget(self.file_types_tree)

        # 添加/删除按钮
        button_layout = QVBoxLayout()
        add_button = QPushButton("+")
        add_button.clicked.connect(self.add_file_type)
        delete_button = QPushButton("-")
        delete_button.clicked.connect(self.delete_file_type)

        button_layout.addWidget(add_button)
        button_layout.addWidget(delete_button)
        button_layout.addStretch()

        list_layout.addLayout(button_layout)
        layout.addLayout(list_layout)

        return tab

    def create_person_fields_tab(self) -> QWidget:
        """创建人员字段选项卡。"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # 添加提示标签
        tip_label = QLabel("提示：双击列表项可以编辑人员字段")
        tip_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(tip_label)

        # 创建列表和编辑区域
        list_layout = QHBoxLayout()

        # 人员字段列表
        self.person_fields_tree = QTreeWidget()
        self.person_fields_tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.person_fields_tree.setHeaderLabels(["名称", "ID", "描述", "必填", "默认值"])
        self.person_fields_tree.itemDoubleClicked.connect(self.edit_person_field)

        # 设置列宽
        self.person_fields_tree.setColumnWidth(0, 150)  # 名称
        self.person_fields_tree.setColumnWidth(1, 100)  # ID
        self.person_fields_tree.setColumnWidth(2, 200)  # 描述
        self.person_fields_tree.setColumnWidth(3, 80)  # 必填
        self.person_fields_tree.setColumnWidth(4, 150)  # 默认值

        # 添加现有人员字段
        for field in self.config.person_fields:
            item = QTreeWidgetItem()
            item.setData(0, Qt.UserRole, field)
            item.setText(0, field["name"])
            item.setText(1, field["id"])
            item.setText(2, field.get("description", ""))
            item.setText(3, "是" if field.get("required", False) else "否")
            item.setText(4, field.get("default_value", ""))
            self.person_fields_tree.addTopLevelItem(item)

        list_layout.addWidget(self.person_fields_tree)

        # 添加/删除按钮
        button_layout = QVBoxLayout()
        add_button = QPushButton("+")
        add_button.clicked.connect(self.add_person_field)
        delete_button = QPushButton("-")
        delete_button.clicked.connect(self.delete_person_field)

        button_layout.addWidget(add_button)
        button_layout.addWidget(delete_button)
        button_layout.addStretch()

        list_layout.addLayout(button_layout)
        layout.addLayout(list_layout)

        return tab

    def create_hotkeys_tab(self) -> QWidget:
        """创建快捷键设置选项卡。"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # 添加提示标签
        tip_label = QLabel("提示：点击'录制'按钮，然后按下想要设置的快捷键组合")
        tip_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(tip_label)

        # 创建快捷键编辑器
        if self.hotkey_manager is None:
            from src.windows.ui.hotkey_manager import HotkeyManager

            self.hotkey_manager = HotkeyManager(self.config)

        self.hotkey_editor = HotkeyEditor(self.hotkey_manager, self)
        layout.addWidget(self.hotkey_editor)

        return tab

    def add_file_type(self):
        """添加新的文件类型。"""
        try:
            # 创建新的文件类型对话框
            dialog = FileTypeDialog(self)
            if dialog.exec_():
                file_type = dialog.get_file_type()
                if self.config.add_file_type(file_type):
                    item = QTreeWidgetItem()
                    item.setData(0, Qt.UserRole, file_type)
                    item.setText(0, file_type["name"])
                    item.setText(1, file_type["id"])
                    item.setText(2, file_type["directory"])
                    item.setText(3, file_type.get("description", ""))
                    self.file_types_tree.addTopLevelItem(item)
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def delete_file_type(self):
        """删除选中的文件类型。"""
        current_item = self.file_types_tree.currentItem()
        if current_item:
            file_type = current_item.data(0, Qt.UserRole)
            if (
                QMessageBox.question(self, "确认", f"确定要删除文件类型 {file_type['name']} 吗？")
                == QMessageBox.Yes
            ):
                if self.config.delete_file_type(file_type["id"]):
                    self.file_types_tree.takeTopLevelItem(
                        self.file_types_tree.indexOfTopLevelItem(current_item)
                    )

    def add_person_field(self):
        """添加新的人员字段。"""
        try:
            # 创建新的人员字段对话框
            dialog = PersonFieldDialog(self)
            if dialog.exec_():
                field = dialog.get_person_field()
                if self.config.add_person_field(field):
                    item = QTreeWidgetItem()
                    item.setData(0, Qt.UserRole, field)
                    item.setText(0, field["name"])
                    item.setText(1, field["id"])
                    item.setText(2, field.get("description", ""))
                    item.setText(3, "是" if field.get("required", False) else "否")
                    item.setText(4, field.get("default_value", ""))
                    self.person_fields_tree.addTopLevelItem(item)
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def delete_person_field(self):
        """删除选中的人员字段。"""
        current_item = self.person_fields_tree.currentItem()
        if current_item:
            field = current_item.data(0, Qt.UserRole)
            if (
                QMessageBox.question(self, "确认", f"确定要删除人员字段 {field['name']} 吗？")
                == QMessageBox.Yes
            ):
                if self.config.delete_person_field(field["id"]):
                    self.person_fields_tree.takeTopLevelItem(
                        self.person_fields_tree.indexOfTopLevelItem(current_item)
                    )

    def edit_file_type(self, item: Optional[QTreeWidgetItem] = None):
        """编辑文件类型。"""
        if item is None:
            item = self.file_types_tree.currentItem()
        if item:
            file_type = item.data(0, Qt.UserRole)
            dialog = FileTypeDialog(self)

            # 设置当前值
            dialog.id_edit.setText(file_type["id"])
            dialog.id_edit.setEnabled(False)  # ID不允许修改
            dialog.name_edit.setText(file_type["name"])
            dialog.directory_edit.setText(file_type["directory"])
            dialog.description_edit.setText(file_type.get("description", ""))

            if dialog.exec_():
                new_file_type = dialog.get_file_type()
                if self.config.update_file_type(file_type["id"], new_file_type):
                    item.setText(0, new_file_type["name"])
                    item.setText(1, new_file_type["id"])
                    item.setText(2, new_file_type["directory"])
                    item.setText(3, new_file_type.get("description", ""))
                    item.setData(0, Qt.UserRole, new_file_type)

    def edit_person_field(self, item: Optional[QTreeWidgetItem] = None):
        """编辑人员字段。"""
        if item is None:
            item = self.person_fields_tree.currentItem()
        if item:
            field = item.data(0, Qt.UserRole)
            dialog = PersonFieldDialog(self)

            # 设置当前值
            dialog.id_edit.setText(field["id"])
            dialog.id_edit.setEnabled(False)  # ID不允许修改
            dialog.name_edit.setText(field["name"])
            dialog.description_edit.setText(field.get("description", ""))
            dialog.default_value_edit.setText(field.get("default_value", ""))

            if dialog.exec_():
                new_field = dialog.get_person_field()
                if self.config.update_person_field(field["id"], new_field):
                    item.setText(0, new_field["name"])
                    item.setText(1, new_field["id"])
                    item.setText(2, new_field.get("description", ""))
                    item.setText(3, "是" if new_field.get("required", False) else "否")
                    item.setText(4, new_field.get("default_value", ""))
                    item.setData(0, Qt.UserRole, new_field)

    def add_base_directory(self):
        """添加新的基本目录。"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择基本目录", "", QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if directory:
            if directory not in self.config.base_directories:
                self.config.add_base_directory(directory)
                item = QListWidgetItem(directory)
                if directory == self.config.current_base_directory:
                    item.setBackground(Qt.lightGray)
                self.base_dir_list.addItem(item)

    def remove_base_directory(self):
        """移除选中的基本目录。"""
        current_item = self.base_dir_list.currentItem()
        if current_item:
            directory = current_item.text()
            if len(self.config.base_directories) <= 1:
                QMessageBox.warning(self, "警告", "不能删除最后一个目录")
                return
            if (
                QMessageBox.question(self, "确认", f"确定要移除目录 {directory} 吗？")
                == QMessageBox.Yes
            ):
                if self.config.remove_base_directory(directory):
                    self.base_dir_list.takeItem(self.base_dir_list.row(current_item))
                    # 更新当前目录的显示
                    for i in range(self.base_dir_list.count()):
                        item = self.base_dir_list.item(i)
                        if item.text() == self.config.current_base_directory:
                            item.setBackground(Qt.lightGray)
                        else:
                            item.setBackground(Qt.white)

    def set_current_directory(self):
        """将选中的目录设置为当前目录。"""
        current_item = self.base_dir_list.currentItem()
        if current_item:
            directory = current_item.text()
            if self.config.set_base_directory(directory):
                # 更新所有项的背景色
                for i in range(self.base_dir_list.count()):
                    item = self.base_dir_list.item(i)
                    if item.text() == directory:
                        item.setBackground(Qt.lightGray)
                    else:
                        item.setBackground(Qt.white)

    def on_directory_selected(self, item):
        """当目录被选中时的处理。"""
        # 这里可以添加其他处理逻辑，比如显示目录信息等
        pass

    def save_config(self):
        """保存配置更改。"""
        try:
            # 更新命名模式
            self.config.naming_pattern = self.naming_pattern_edit.text()

            # 更新选项
            new_options = {}
            for key, widget in self.option_widgets.items():
                if isinstance(widget, QCheckBox):
                    new_options[key] = widget.isChecked()
                elif isinstance(widget, QLineEdit):
                    value = widget.text()
                    # 对于max_history_items，需要转换为整数
                    if key == "max_history_items":
                        try:
                            value = int(value)
                        except ValueError:
                            raise ConfigurationError("历史记录数量必须是一个有效的数字")
                    new_options[key] = value

            self.config.options = new_options

            # 保存快捷键设置
            if self.hotkey_editor is not None:
                for action_id, edit in self.hotkey_editor.hotkey_edits.items():
                    sequence = edit.get_key_sequence()
                    if not sequence.isEmpty():
                        self.config.hotkeys[action_id] = sequence.toString()

            # 保存配置
            self.config.save()

            QMessageBox.information(self, "成功", "配置已保存")
            self.close()

        except ConfigurationError as e:
            QMessageBox.critical(self, "错误", f"保存配置失败：{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发生未知错误：{str(e)}")


class FileTypeDialog(QDialog):
    """文件类型编辑对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("文件类型")
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()
        self.setLayout(layout)

        # 创建输入框
        self.id_edit = QLineEdit()
        self.name_edit = QLineEdit()
        self.directory_edit = QLineEdit()
        self.description_edit = QLineEdit()

        # 添加字段说明
        id_label = QLabel("ID:")
        id_label.setToolTip("文件类型的唯一标识符")
        name_label = QLabel("名称:")
        name_label.setToolTip("文件类型的显示名称")
        directory_label = QLabel("目录:")
        directory_label.setToolTip("文件类型的存储目录")
        description_label = QLabel("描述:")
        description_label.setToolTip("文件类型的详细描述（可选）")

        # 添加到布局
        layout.addRow(id_label, self.id_edit)
        layout.addRow(name_label, self.name_edit)
        layout.addRow(directory_label, self.directory_edit)
        layout.addRow(description_label, self.description_edit)

        # 添加按钮
        buttons = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)

        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

    def get_file_type(self) -> Dict[str, Any]:
        """获取文件类型数据。"""
        file_type = {
            "id": self.id_edit.text(),
            "name": self.name_edit.text(),
            "directory": self.directory_edit.text(),
            "description": self.description_edit.text(),
        }

        # 如果描述为空，从字典中移除
        if not file_type["description"]:
            file_type.pop("description")

        return file_type

    def accept(self):
        """验证并接受输入。"""
        if not self.id_edit.text() or not self.name_edit.text() or not self.directory_edit.text():
            QMessageBox.warning(self, "警告", "ID、名称和目录为必填项")
            return
        super().accept()

    def reject(self):
        """取消输入。"""
        self.done(0)


class PersonFieldDialog(QDialog):
    """人员字段编辑对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("人员字段")
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()
        self.setLayout(layout)

        # 创建输入框
        self.id_edit = QLineEdit()
        self.name_edit = QLineEdit()
        self.description_edit = QLineEdit()
        self.default_value_edit = QLineEdit()

        # 添加字段说明
        id_label = QLabel("ID:")
        id_label.setToolTip("字段的唯一标识符")
        name_label = QLabel("名称:")
        name_label.setToolTip("字段的显示名称")
        description_label = QLabel("描述:")
        description_label.setToolTip("字段的详细描述")
        default_value_label = QLabel("默认值:")
        default_value_label.setToolTip("字段的默认值（可选）")

        # 添加到布局
        layout.addRow(id_label, self.id_edit)
        layout.addRow(name_label, self.name_edit)
        layout.addRow(description_label, self.description_edit)
        layout.addRow(default_value_label, self.default_value_edit)

        # 添加按钮
        buttons = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)

        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

    def get_person_field(self) -> Dict[str, Any]:
        """获取人员字段数据。"""
        field = {
            "id": self.id_edit.text(),
            "name": self.name_edit.text(),
            "description": self.description_edit.text(),
            "default_value": self.default_value_edit.text(),
            "required": False,  # 默认设置为非必填
        }

        # 如果描述为空，从字典中移除
        if not field["description"]:
            field.pop("description")

        # 如果默认值为空，从字典中移除
        if not field["default_value"]:
            field.pop("default_value")

        return field

    def accept(self):
        """验证并接受输入。"""
        if not self.id_edit.text() or not self.name_edit.text():
            QMessageBox.warning(self, "警告", "ID和名称为必填项")
            return
        super().accept()

    def reject(self):
        """取消输入。"""
        self.done(0)
