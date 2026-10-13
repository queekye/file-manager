#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文件类型选择界面模块，提供简单直接的文件类型选择界面。PyQt5实现版本。
"""

from typing import Any, Dict, List, Optional

from loguru import logger
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from src.windows.ui.style_config import get_column_widths, get_style_sheets, get_window_size


class FileTypeSelector:
    """文件类型选择界面，提供简单直接的文件类型选择。"""

    def __init__(self, file_types: List[Dict[str, Any]], title: str = "选择文件类型"):
        """
        初始化文件类型选择界面。

        Args:
            file_types: 文件类型列表，每个类型为包含id和name的字典
            title: 窗口标题
        """
        self.file_types = file_types
        self.title = title
        self.selected_type_id = None

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
        显示文件类型选择界面。

        Returns:
            选择的文件类型ID，如果取消则返回None
        """
        try:
            # 创建对话框
            dialog = FileTypeSelectorDialog(self.file_types, self.title)

            # 显示对话框并获取结果
            if dialog.exec_() == QDialog.Accepted:
                self.selected_type_id = dialog.result
                self.log_info(f"已选择文件类型ID: {self.selected_type_id}")
            else:
                self.selected_type_id = None
                self.log_info("用户取消选择文件类型")

            return self.selected_type_id

        except Exception as e:
            self.log_error("显示文件类型选择界面时发生错误", e)
            return None


class FileTypeSelectorDialog(QDialog):
    """文件类型选择对话框类，处理文件类型选择界面的显示和交互。"""

    def __init__(self, file_types: List[Dict[str, Any]], title: str):
        """
        初始化文件类型选择对话框。

        Args:
            file_types: 文件类型列表
            title: 窗口标题
        """
        super().__init__()

        self.file_types = file_types
        self.result = None

        # 设置窗口标题和大小
        self.setWindowTitle(title)
        width, height = get_window_size("file_type_selector")
        self.resize(width, height)

        # 设置样式
        self.setStyleSheet(get_style_sheets()["main_window"])

        # 创建界面
        self._create_widgets()

        # 填充文件类型列表
        self._populate_type_list()

    def _create_widgets(self) -> None:
        """创建界面控件。"""
        try:
            # 创建主布局
            layout = QVBoxLayout()

            # 创建说明标签
            instruction_label = QLabel("请选择文件类型:")
            instruction_label.setStyleSheet("font-weight: bold;")
            layout.addWidget(instruction_label)

            # 创建文件类型列表
            self.tree = QTreeWidget()
            self.tree.setHeaderLabels(["ID", "类型名称"])

            # 设置列宽
            widths = get_column_widths()["file_types"]
            self.tree.setColumnWidth(0, widths["id"])
            self.tree.setColumnWidth(1, widths["name"])

            layout.addWidget(self.tree)

            # 双击处理
            self.tree.itemDoubleClicked.connect(self._on_ok)

            # 创建按钮布局
            button_layout = QHBoxLayout()

            # 创建确定按钮
            self.ok_button = QPushButton("确定")
            self.ok_button.clicked.connect(self._on_ok)
            button_layout.addWidget(self.ok_button)

            # 创建取消按钮
            self.cancel_button = QPushButton("取消")
            self.cancel_button.clicked.connect(self.reject)
            button_layout.addWidget(self.cancel_button)

            # 添加按钮布局
            layout.addLayout(button_layout)

            # 设置主布局
            self.setLayout(layout)

        except Exception as e:
            logger.error("创建界面控件时发生错误", exc_info=True)

    def _populate_type_list(self) -> None:
        """填充文件类型列表。"""
        try:
            # 清空列表
            self.tree.clear()

            # 添加文件类型到列表
            for file_type in self.file_types:
                type_id = file_type.get("id", "")
                type_name = file_type.get("name", "")

                item = QTreeWidgetItem([type_id, type_name])
                self.tree.addTopLevelItem(item)

            # 如果有文件类型，选中第一个
            if self.tree.topLevelItemCount() > 0:
                first_item = self.tree.topLevelItem(0)
                self.tree.setCurrentItem(first_item)

        except Exception as e:
            logger.error("填充文件类型列表时发生错误", exc_info=True)

    def _on_ok(self) -> None:
        """处理确定按钮点击事件。"""
        try:
            # 获取选中的文件类型
            current_item = self.tree.currentItem()

            if current_item:
                # 获取文件类型ID
                type_id = current_item.text(0)

                # 设置结果
                self.result = type_id

                # 接受对话框
                self.accept()
            else:
                QMessageBox.information(self, "提示", "请选择一个文件类型")

        except Exception as e:
            logger.error("处理确定按钮点击事件时发生错误", exc_info=True)


# 测试代码
if __name__ == "__main__":
    import sys

    from PyQt5.QtWidgets import QApplication

    # 创建测试数据
    test_file_types = [
        {"id": "t001", "name": "文档"},
        {"id": "t002", "name": "图片"},
        {"id": "t003", "name": "视频"},
        {"id": "t004", "name": "音频"},
        {"id": "t005", "name": "压缩文件"},
        {"id": "t006", "name": "其他"},
    ]

    # 创建应用
    app = QApplication(sys.argv)

    # 创建文件类型选择器
    selector = FileTypeSelector(test_file_types)

    # 显示文件类型选择界面
    result = selector.show()

    # 输出结果
    print(f"选择的文件类型ID: {result}")
