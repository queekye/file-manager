#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文件选择器UI模块。
"""

from typing import List, Optional

from loguru import logger
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStyle,
    QVBoxLayout,
)


class FileSelector(QDialog):
    """文件选择器对话框类。"""

    file_selected = pyqtSignal(list)  # 文件选择完成信号

    def __init__(self, parent=None, title="选择文件", multi=True):
        """
        初始化文件选择器。

        Args:
            parent: 父窗口
            title: 窗口标题
            multi: 是否允许多选
        """
        super().__init__(parent)
        self.title = title
        self.multi = multi
        self.selected_files = []

        self.setup_ui()

    def setup_ui(self):
        """设置UI界面。"""
        # 设置窗口属性
        self.setWindowTitle(self.title)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # 创建主布局
        layout = QVBoxLayout()

        # 添加说明标签
        label = QLabel("已选择的文件和目录：")
        layout.addWidget(label)

        # 创建文件列表
        self.file_list = QListWidget()
        layout.addWidget(self.file_list)

        # 创建按钮布局
        button_layout = QHBoxLayout()

        # 添加文件按钮
        self.add_file_button = QPushButton("添加文件")
        self.add_file_button.clicked.connect(self.add_files_only)
        button_layout.addWidget(self.add_file_button)
        
        # 添加目录按钮
        self.add_dir_button = QPushButton("添加目录")
        self.add_dir_button.clicked.connect(self.add_directories)
        button_layout.addWidget(self.add_dir_button)

        # 清空按钮
        self.clear_button = QPushButton("清空")
        self.clear_button.clicked.connect(self.clear_files)
        button_layout.addWidget(self.clear_button)

        # 添加弹性空间
        button_layout.addStretch()

        # 确定和取消按钮
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setEnabled(False)  # 初始状态禁用

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        # 将按钮布局添加到主布局
        layout.addLayout(button_layout)

        # 设置主布局
        self.setLayout(layout)

    def add_files_only(self):
        """仅添加文件到列表。"""
        try:
            if self.multi:
                files, _ = QFileDialog.getOpenFileNames(self, "选择文件")
            else:
                file, _ = QFileDialog.getOpenFileName(self, "选择文件")
                files = [file] if file else []

            if files:
                # 添加新文件到列表
                for file in files:
                    if file not in self.selected_files:
                        self.selected_files.append(file)
                        item = QListWidgetItem(file)
                        # 添加文件图标（使用系统样式图标以确保跨平台兼容性）
                        item.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
                        self.file_list.addItem(item)

                # 启用确定按钮
                self.ok_button.setEnabled(True)

        except Exception as e:
            logger.exception(f"添加文件时发生错误: {str(e)}")

    def add_directories(self):
        """添加目录到列表。"""
        try:
            directory = QFileDialog.getExistingDirectory(self, "选择目录")
            
            if directory:
                if directory not in self.selected_files:
                    self.selected_files.append(directory)
                    item = QListWidgetItem(directory)
                    # 添加目录图标（使用系统样式图标以确保跨平台兼容性）
                    item.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
                    self.file_list.addItem(item)
                    
                # 启用确定按钮
                self.ok_button.setEnabled(True)

        except Exception as e:
            logger.exception(f"添加目录时发生错误: {str(e)}")

    def add_files(self):
        """添加文件到列表 (兼容旧代码)。"""
        self.add_files_only()
        self.add_directories()

    def clear_files(self):
        """清空文件列表。"""
        self.file_list.clear()
        self.selected_files.clear()
        self.ok_button.setEnabled(False)

    def get_selected_files(self) -> List[str]:
        """
        获取选择的文件列表。

        Returns:
            选择的文件路径列表
        """
        return self.selected_files

    @staticmethod
    def get_files(parent=None, title="选择文件", multi=True) -> Optional[List[str]]:
        """
        显示文件选择对话框并获取选择的文件。

        Args:
            parent: 父窗口
            title: 对话框标题
            multi: 是否允许多选

        Returns:
            选择的文件路径列表，如果取消则返回None
        """
        dialog = FileSelector(parent, title, multi)
        dialog.setWindowModality(Qt.ApplicationModal)  # 设置为模态对话框

        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_selected_files()
        return None
