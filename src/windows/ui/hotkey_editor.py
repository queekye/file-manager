#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
快捷键编辑器界面模块。
"""

from typing import Dict, Optional

from loguru import logger
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeyEvent, QKeySequence
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class HotkeyEdit(QWidget):
    """快捷键编辑控件。"""

    def __init__(self, parent=None):
        """初始化快捷键编辑控件。"""
        super().__init__(parent)
        self.key_sequence = QKeySequence()
        self.recording = False
        self.keys_pressed = set()

        # 创建布局
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建显示标签
        self.display_label = QLabel()
        self.display_label.setMinimumWidth(150)
        self.display_label.setFrameStyle(QLabel.Panel | QLabel.Sunken)
        layout.addWidget(self.display_label)

        # 创建录制按钮
        self.record_button = QPushButton("录制")
        self.record_button.setCheckable(True)
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)

        # 创建清除按钮
        self.clear_button = QPushButton("清除")
        self.clear_button.clicked.connect(self.clear_shortcut)
        layout.addWidget(self.clear_button)

        self.setLayout(layout)
        self.update_display()

    def toggle_recording(self, checked: bool) -> None:
        """切换录制状态。"""
        self.recording = checked
        self.record_button.setText("停止" if checked else "录制")
        if checked:
            self.setFocus()
            self.keys_pressed.clear()
        self.update_display()

    def clear_shortcut(self) -> None:
        """清除快捷键。"""
        self.key_sequence = QKeySequence()
        self.keys_pressed.clear()
        self.update_display()

    def update_display(self) -> None:
        """更新显示。"""
        if self.recording:
            text = "按下快捷键..."
        else:
            text = self.key_sequence.toString() if not self.key_sequence.isEmpty() else "无快捷键"
        self.display_label.setText(text)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """处理按键按下事件。"""
        if not self.recording:
            return

        key = event.key()
        if key == Qt.Key_unknown:
            return

        # 记录按下的键
        if key == Qt.Key_Control:
            self.keys_pressed.add(Qt.CTRL)
        elif key == Qt.Key_Alt:
            self.keys_pressed.add(Qt.ALT)
        elif key == Qt.Key_Shift:
            self.keys_pressed.add(Qt.SHIFT)
        elif key == Qt.Key_Meta:
            self.keys_pressed.add(Qt.META)
        else:
            self.keys_pressed.add(key)

        # 更新快捷键
        modifiers = Qt.NoModifier
        for mod in (Qt.CTRL, Qt.ALT, Qt.SHIFT, Qt.META):
            if mod in self.keys_pressed:
                modifiers |= mod

        # 找到非修饰键
        main_key = next(
            (k for k in self.keys_pressed if k not in (Qt.CTRL, Qt.ALT, Qt.SHIFT, Qt.META)), None
        )

        if main_key:
            self.key_sequence = QKeySequence(modifiers | main_key)
            self.toggle_recording(False)

        self.update_display()
        event.accept()

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        """处理按键释放事件。"""
        if not self.recording:
            return

        key = event.key()
        if key == Qt.Key_unknown:
            return

        # 从按下的键集合中移除
        if key == Qt.Key_Control:
            self.keys_pressed.discard(Qt.CTRL)
        elif key == Qt.Key_Alt:
            self.keys_pressed.discard(Qt.ALT)
        elif key == Qt.Key_Shift:
            self.keys_pressed.discard(Qt.SHIFT)
        elif key == Qt.Key_Meta:
            self.keys_pressed.discard(Qt.META)
        else:
            self.keys_pressed.discard(key)

        self.update_display()
        event.accept()

    def get_key_sequence(self) -> QKeySequence:
        """获取当前的快捷键序列。"""
        return self.key_sequence

    def set_key_sequence(self, sequence: str) -> None:
        """设置快捷键序列。"""
        self.key_sequence = QKeySequence(sequence)
        self.update_display()


class HotkeyEditor(QDialog):
    """快捷键编辑器对话框。"""

    def __init__(self, hotkey_manager, parent=None):
        """初始化快捷键编辑器对话框。"""
        super().__init__(parent)
        self.hotkey_manager = hotkey_manager

        self.setWindowTitle("快捷键设置")
        self.setMinimumWidth(400)

        # 创建布局
        layout = QVBoxLayout()

        # 添加快捷键编辑控件
        self.hotkey_edits = {}

        # 添加文件管理器快捷键
        layout.addWidget(QLabel("添加文件快捷键:"))
        add_file_edit = HotkeyEdit()
        add_file_edit.set_key_sequence(hotkey_manager.get_hotkey("add_to_file_manager"))
        layout.addWidget(add_file_edit)
        self.hotkey_edits["add_to_file_manager"] = add_file_edit

        # 添加配置编辑器快捷键
        layout.addWidget(QLabel("打开配置快捷键:"))
        config_edit = HotkeyEdit()
        config_edit.set_key_sequence(hotkey_manager.get_hotkey("open_config"))
        layout.addWidget(config_edit)
        self.hotkey_edits["open_config"] = config_edit

        # 添加按钮
        button_layout = QHBoxLayout()
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.save_hotkeys)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def save_hotkeys(self) -> None:
        """保存快捷键设置。"""
        try:
            # 收集所有快捷键
            new_hotkeys = {}
            for action_id, edit in self.hotkey_edits.items():
                sequence = edit.get_key_sequence()
                if not sequence.isEmpty():
                    new_hotkeys[action_id] = sequence.toString()

            # 检查快捷键是否有冲突
            used_sequences = set()
            for action_id, sequence in new_hotkeys.items():
                if sequence in used_sequences:
                    QMessageBox.warning(
                        self, "快捷键冲突", f"快捷键 {sequence} 已被使用，请设置不同的快捷键"
                    )
                    return
                used_sequences.add(sequence)

            # 更新快捷键
            for action_id, sequence in new_hotkeys.items():
                if not self.hotkey_manager.set_hotkey(action_id, sequence):
                    QMessageBox.warning(
                        self, "设置失败", f"快捷键 {sequence} 设置失败，请尝试其他组合"
                    )
                    return

            self.accept()

        except Exception as e:
            logger.exception("保存快捷键设置时发生错误")
            QMessageBox.critical(self, "错误", f"保存快捷键设置失败：{str(e)}")
