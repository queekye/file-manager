#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
轻量级人员文件管理系统主程序入口。
"""

import argparse
import os
import sys
import time

from loguru import logger
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon, QWidget

from src.core import DirectoryManager, FileManager
from src.core.config import Config
from src.core.log_config import LogConfig
from src.core.person_manager import PersonManager
from src.windows.ui.file_selector import FileSelector
from src.windows.ui.hotkey_manager import HotkeyManager
from src.utils.path_utils import get_app_root


def init_managers():
    """初始化配置和人员管理器。

    Returns:
        tuple: (config, person_manager) 配置对象和人员管理器对象
    """
    try:
        config = Config(None)  # 使用默认配置路径
        person_manager = PersonManager(config=config)
        return config, person_manager
    except Exception as e:
        logger.exception(f"初始化管理器失败: {e}")
        return None, None


def select_files_from_dialog(parent=None, multi=True, title="选择文件"):
    """显示文件和目录选择对话框。

    Args:
        parent: 父窗口
        multi: 是否支持多选文件
        title: 对话框标题

    Returns:
        list: 选择的文件和目录路径列表
    """
    try:
        return FileSelector.get_files(parent, title, multi) or []
    except Exception as e:
        logger.exception(f"显示文件和目录选择对话框失败: {e}")
        return []


def wait_for_user_input():
    """等待用户输入。"""
    if "--wait" in sys.argv:
        input("按Enter键退出...")


def show_config_editor_window(config_path=None, hotkey_manager=None):
    """显示配置编辑器窗口。"""
    try:
        from src.windows.ui.config_editor import ConfigEditor

        # 加载配置
        config = Config(config_path)
        # 创建并显示编辑器
        editor = ConfigEditor(config, hotkey_manager=hotkey_manager)
        editor.show()
        return editor
    except Exception as e:
        logger.exception(f"显示配置编辑器失败：{str(e)}")
        return None


def get_person_and_type_from_ui(config, person_manager):
    """通过UI获取用户选择的人员和文件类型。

    Returns:
        tuple: (person, file_type) 如果用户取消则返回 (None, None)
    """
    try:
        from src.windows.ui import FileTypeSelector, PersonSelector

        # 显示人员选择界面
        selector = PersonSelector(
            person_manager=person_manager, title="选择目标人员", config=config
        )
        person_id = selector.show()

        if not person_id:
            logger.warning("操作取消: 未选择人员")
            return None, None

        # 获取选择的人员信息
        persons = person_manager.get_all_persons()
        selected_person = next((p for p in persons if p["id"] == person_id), None)

        if not selected_person:
            logger.error(f"错误: 未找到ID为 {person_id} 的人员")
            return None, None

        # 显示文件类型选择界面
        selector = FileTypeSelector(config.file_types, title="选择文件类型")
        type_id = selector.show()

        if not type_id:
            logger.warning("操作取消: 未选择文件类型")
            return None, None

        # 获取选择的文件类型信息
        selected_type = next((t for t in config.file_types if t["id"] == type_id), None)

        if not selected_type:
            logger.error(f"错误: 未找到ID为 {type_id} 的文件类型")
            return None, None

        return selected_person, selected_type

    except Exception as e:
        logger.exception(f"选择人员和文件类型时发生错误: {e}")
        return None, None


def process_files(files, person, file_type, config: Config):
    """处理文件列表。

    Args:
        files (list): 文件路径列表
        person (dict): 选择的人员信息
        file_type (dict): 选择的文件类型信息
        config (Config): 配置对象
        operation (str): 操作类型，'copy' 或 'move'
    """
    try:
        operation = "copy" if config.options["copy_files"] else "move"
        # 创建管理器实例
        directory_manager = DirectoryManager(config.get_base_directory(), config=config)
        file_manager = FileManager(
            directory_manager, naming_pattern=config.naming_pattern, options=config.options
        )

        # 处理每个文件
        logger.info("\n开始处理文件...")
        logger.info(f"目标人员: {person['name']} (ID: {person['id']})")
        logger.info(f"文件类型: {file_type['name']} (ID: {file_type['id']})")
        logger.info(f"操作类型: {operation}")
        logger.info(f"目标目录: {config.get_base_directory()}")

        for i, file_path in enumerate(files, 1):
            logger.info(f"处理文件 {i}/{len(files)}: {file_path}")

            try:
                if operation == "copy":
                    if os.path.isdir(file_path):
                        result = file_manager.copy_directory(file_path, person, file_type)
                    else:
                        result = file_manager.copy_file(file_path, person, file_type)
                    
                    file_type_str = '目录' if os.path.isdir(file_path) else '文件'
                    if result.success:
                        logger.success(
                            f"{file_type_str}复制成功: {result.destination_path}"
                        )
                    else:
                        logger.error(
                            f"{file_type_str}复制失败: {result.message}"
                        )
                else:  # move
                    if os.path.isdir(file_path):
                        result = file_manager.move_directory(file_path, person, file_type)
                    else:
                        result = file_manager.move_file(file_path, person, file_type)
                    if result.success:
                        logger.success(
                            f"{'目录' if os.path.isdir(file_path) else '文件'}移动成功: {result.destination_path}"
                        )
                    else:
                        logger.error(
                            f"{'目录' if os.path.isdir(file_path) else '文件'}移动失败: {result.message}"
                        )
            except Exception as e:
                logger.exception(f"处理文件 {file_path} 时发生错误: {e}")

            # 添加一点延迟，让用户看到进度
            time.sleep(0.2)

        logger.info("\n文件处理完成!")

    except Exception as e:
        logger.exception(f"处理文件时发生错误: {e}")


class MainWindow(QWidget):
    """主窗口类，用于处理全局快捷键和系统托盘。"""

    def __init__(self):
        """初始化主窗口。"""
        super().__init__()

        # 初始化类属性
        self.tray_icon = None
        self.current_dialog = None
        self.file_manager_dialog = None
        self.config_editor_dialog = None

        # 加载配置
        try:
            self.config = Config()
        except Exception as e:
            logger.exception("加载配置失败")
            QMessageBox.critical(self, "错误", f"加载配置失败：{str(e)}")
            sys.exit(1)

        # 初始化快捷键管理器
        self.hotkey_manager = HotkeyManager(config=self.config)

        # 注册快捷键
        self.hotkey_manager.register_hotkey(self, "add_to_file_manager", self.show_file_manager)
        self.hotkey_manager.register_hotkey(self, "open_config", self.show_config_editor)

        # 创建系统托盘图标
        self.create_tray_icon()

        # 隐藏主窗口
        self.hide()

    def create_tray_icon(self):
        """创建系统托盘图标。"""
        if self.tray_icon is None:
            self.tray_icon = QSystemTrayIcon(self)

            # 获取图标路径
            if hasattr(sys, "_MEIPASS"):
                # 如果是打包后的程序，使用_MEIPASS中的路径
                icon_path = os.path.join(sys._MEIPASS, "resources", "app.ico")
            else:
                # 如果是开发环境，使用相对路径
                icon_path = os.path.join(os.path.dirname(__file__), "windows", "icons", "app.ico")

            if not os.path.exists(icon_path):
                logger.warning(f"找不到图标文件: {icon_path}")
                return

            self.tray_icon.setIcon(QIcon(icon_path))

            # 创建托盘菜单
            menu = QMenu()

            # 添加菜单项
            add_action = menu.addAction(
                "添加文件 ({})".format(self.hotkey_manager.get_hotkey("add_to_file_manager"))
            )
            add_action.triggered.connect(self.show_file_manager)

            config_action = menu.addAction(
                "打开配置 ({})".format(self.hotkey_manager.get_hotkey("open_config"))
            )
            config_action.triggered.connect(self.show_config_editor)

            menu.addSeparator()
            quit_action = menu.addAction("退出")
            quit_action.triggered.connect(self.quit_application)

            # 设置托盘菜单
            self.tray_icon.setContextMenu(menu)
            self.tray_icon.show()

    def show_file_manager(self):
        """显示文件管理器界面。"""
        try:
            # 初始化管理器
            config, person_manager = init_managers()
            if not config or not person_manager:
                return

            # 获取用户选择
            person, file_type = get_person_and_type_from_ui(config, person_manager)
            if person and file_type:
                # 显示文件选择对话框并保持引用
                files = select_files_from_dialog(self)
                if files:
                    # 在新线程中处理文件，避免阻塞主线程
                    from PyQt5.QtCore import QThread

                    class FileProcessThread(QThread):
                        def __init__(self, files, person, file_type, config):
                            super().__init__()
                            self.files = files
                            self.person = person
                            self.file_type = file_type
                            self.config = config

                        def run(self):
                            process_files(self.files, self.person, self.file_type, self.config)

                    # 创建并启动线程
                    self.process_thread = FileProcessThread(files, person, file_type, config)
                    self.process_thread.start()

        except Exception as e:
            logger.exception(f"显示文件管理器失败：{str(e)}")

    def show_config_editor(self):
        """显示配置编辑器界面。"""
        try:
            # 如果配置编辑器已经打开，就把它带到前台
            if self.config_editor_dialog is not None and self.config_editor_dialog.isVisible():
                self.config_editor_dialog.activateWindow()
                return

            # 创建并显示编辑器，保持引用
            self.config_editor_dialog = show_config_editor_window(
                hotkey_manager=self.hotkey_manager
            )
            if self.config_editor_dialog:
                # 设置窗口关闭时的处理
                self.config_editor_dialog.setAttribute(Qt.WA_DeleteOnClose, False)

        except Exception as e:
            logger.exception(f"显示配置编辑器失败：{str(e)}")

    def quit_application(self):
        """退出应用程序。"""
        # 关闭所有打开的窗口
        if self.config_editor_dialog:
            self.config_editor_dialog.close()
        QApplication.quit()


def handle_context_menu_args():
    """
    处理从右键菜单传入的参数，显示适当的UI并执行操作。
    返回True如果处理了右键菜单参数，False如果没有。
    """
    logger.debug(f"接收到的命令行参数: {sys.argv}")

    # 检查是否有文件路径参数（不是以--开头的参数）
    file_paths = [arg for arg in sys.argv[1:] if not arg.startswith("--") and os.path.exists(arg)]
    logger.debug(f"解析出的文件路径: {file_paths}")

    if not file_paths:
        logger.debug("没有找到有效的文件路径参数")
        return False

    try:
        # 初始化管理器
        logger.info(f"准备处理 {len(file_paths)} 个文件")
        config, person_manager = init_managers()
        if not config or not person_manager:
            wait_for_user_input()
            return True

        # 获取用户选择
        person, file_type = get_person_and_type_from_ui(config, person_manager)
        if person and file_type:
            process_files(file_paths, person, file_type, config)

        wait_for_user_input()

    except Exception as e:
        logger.exception(f"处理文件时发生错误: {e}")
        wait_for_user_input()

    return True


def parse_arguments():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="轻量级人员文件管理系统")

    # 是否显示配置编辑器
    parser.add_argument("--config-editor", action="store_true", help="显示配置编辑器")

    # 是否等待用户输入
    parser.add_argument("--wait", action="store_true", help="等待用户输入后退出")
    parser.add_argument("--smoke-test", action="store_true", help="离屏创建界面并退出，不注册快捷键或执行文件操作")

    return parser.parse_args()


def main():
    """主函数。"""
    # Windows English hosts may redirect output using cp1252. The CLI's
    # Chinese help must remain usable without a locale-specific environment.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    if "--help" in sys.argv or "-h" in sys.argv:
        parse_arguments()
    smoke = "--smoke-test" in sys.argv
    if smoke:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        os.environ["FILE_MANAGER_DISABLE_HOTKEYS"] = "1"
    LogConfig()
    # 创建应用
    app = QApplication(sys.argv)
    qtPluginPath = os.path.join(os.path.dirname(__file__), "plugins")
    if os.path.isdir(qtPluginPath):
        app.addLibraryPath(qtPluginPath)

    if smoke:
        from src.windows.ui.config_editor import ConfigEditor
        editor = ConfigEditor(Config())
        selector = FileSelector()
        selector.reject()
        QTimer.singleShot(100, app.quit)
        app.exec_()
        editor.close()
        logger.info("离屏界面检查完成，未注册快捷键或执行文件操作")
        return 0

    # 首先尝试处理右键菜单参数
    if handle_context_menu_args():
        return

    # 解析命令行参数
    args = parse_arguments()

    try:
        # 检查是否需要显示配置编辑器
        if args.config_editor:
            editor = show_config_editor_window()
            if editor:
                return app.exec_()
            return

        # 关闭全部窗口后程序不退出
        app.setQuitOnLastWindowClosed(False)

        # 如果没有特殊参数，创建主窗口（用于处理快捷键和系统托盘）
        window = MainWindow()

        # 运行应用
        sys.exit(app.exec_())

    except Exception as e:
        logger.exception(f"初始化时发生错误: {e}")
        if args.wait:
            wait_for_user_input()


if __name__ == "__main__":
    main()
