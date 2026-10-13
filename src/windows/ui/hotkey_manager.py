#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
全局快捷键管理器模块。
使用 keyboard 库实现跨平台的全局快捷键功能。
"""

import threading
import os
from typing import Callable, Dict, Optional

import keyboard
from loguru import logger
from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMessageBox


class HotkeyManager(QObject):
    """全局快捷键管理器类。"""

    # 定义信号用于在主线程中执行回调
    hotkey_triggered = pyqtSignal(str)

    def __init__(self, config=None):
        """
        初始化快捷键管理器。

        Args:
            config: 配置对象，如果为None则使用默认快捷键
        """
        super().__init__()
        self.hotkeys = {}
        self.registered_hotkeys = {}
        self.callbacks = {}
        self.config = config
        self.listener_enabled = os.environ.get("FILE_MANAGER_DISABLE_HOTKEYS") != "1"

        # 连接信号到处理函数
        self.hotkey_triggered.connect(self._handle_hotkey)

        # 启动键盘监听线程
        self._keyboard_thread = None
        if self.listener_enabled:
            self._keyboard_thread = threading.Thread(target=self._start_keyboard_listener, daemon=True)
            self._keyboard_thread.start()

        logger.info("成功初始化全局快捷键管理器")
        self.load_hotkeys()

    def _start_keyboard_listener(self):
        """启动键盘监听线程"""
        keyboard.wait()

    def _handle_hotkey(self, action_id: str):
        """在主线程中处理快捷键回调"""
        if action_id in self.callbacks:
            try:
                self.callbacks[action_id]()
            except Exception as e:
                logger.error(f"执行快捷键回调时出错: {str(e)}")

    def load_hotkeys(self) -> None:
        """从配置文件加载快捷键设置。"""
        if self.config is not None:
            self.hotkeys = self.config.hotkeys
        else:
            # 使用默认快捷键
            self.hotkeys = {"add_to_file_manager": "ctrl+alt+f", "open_config": "ctrl+alt+c"}

    def save_hotkeys(self) -> None:
        """保存快捷键设置到配置文件。"""
        if self.config is not None:
            self.config.hotkeys = self.hotkeys
            try:
                self.config.save()
                logger.info("快捷键设置已保存到配置文件")
            except Exception as e:
                logger.error(f"保存快捷键设置失败: {str(e)}")

    def _convert_qt_to_keyboard(self, key_str: str) -> str:
        """
        将Qt的快捷键格式转换为keyboard库的格式。

        Args:
            key_str: Qt格式的快捷键字符串（例如："Ctrl+Alt+F"）

        Returns:
            keyboard格式的快捷键字符串（例如："ctrl+alt+f"）
        """
        return key_str.lower()

    def register_hotkey(self, window, action_id: str, callback: Callable) -> None:
        """
        注册快捷键。

        Args:
            window: 主窗口实例
            action_id: 动作ID
            callback: 回调函数
        """
        if not self.listener_enabled:
            return
        if action_id in self.hotkeys:
            try:
                # 如果已经注册，先注销
                if action_id in self.registered_hotkeys:
                    self.unregister_hotkey(action_id)

                # 转换快捷键格式
                hotkey = self._convert_qt_to_keyboard(self.hotkeys[action_id])

                try:
                    # 保存回调函数
                    self.callbacks[action_id] = callback

                    # 创建一个包装函数来发送信号
                    def hotkey_wrapper():
                        self.hotkey_triggered.emit(action_id)

                    # 注册全局快捷键
                    keyboard.add_hotkey(hotkey, hotkey_wrapper, suppress=True)

                    # 保存快捷键引用信息
                    self.registered_hotkeys[action_id] = hotkey
                    logger.info(f"成功注册全局快捷键: {action_id} = {hotkey}")

                except Exception as e:
                    logger.error(f"注册快捷键失败: {hotkey}, 错误: {str(e)}")
                    QMessageBox.warning(
                        window, "快捷键注册失败", f"快捷键 {hotkey} 注册失败，可能与其他程序冲突"
                    )

            except Exception as e:
                logger.exception(f"注册快捷键时发生错误: {str(e)}")

    def unregister_hotkey(self, action_id: str) -> None:
        """
        注销快捷键。

        Args:
            action_id: 动作ID
        """
        if action_id in self.registered_hotkeys:
            try:
                hotkey = self.registered_hotkeys[action_id]
                keyboard.remove_hotkey(hotkey)
                del self.registered_hotkeys[action_id]
                if action_id in self.callbacks:
                    del self.callbacks[action_id]
                logger.info(f"成功注销快捷键: {action_id}")
            except Exception as e:
                logger.exception(f"注销快捷键时发生错误: {str(e)}")

    def get_hotkey(self, action_id: str) -> Optional[str]:
        """
        获取指定动作的快捷键。

        Args:
            action_id: 动作ID

        Returns:
            快捷键字符串，如果不存在则返回None
        """
        return self.hotkeys.get(action_id)

    def set_hotkey(self, action_id: str, hotkey: str) -> bool:
        """
        设置快捷键。

        Args:
            action_id: 动作ID
            hotkey: 快捷键字符串

        Returns:
            是否成功设置
        """
        try:
            # 验证快捷键格式
            if QKeySequence(hotkey).isEmpty():
                logger.error(f"无效的快捷键格式: {hotkey}")
                return False

            # 如果快捷键已经注册，先注销它
            self.unregister_hotkey(action_id)

            # 更新快捷键设置
            self.hotkeys[action_id] = hotkey
            logger.info(f"成功设置快捷键: {action_id} = {hotkey}")

            # 保存到配置文件
            self.save_hotkeys()

            return True

        except Exception as e:
            logger.exception(f"设置快捷键时发生错误: {str(e)}")
            return False
