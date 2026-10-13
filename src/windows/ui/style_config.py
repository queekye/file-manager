#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
UI样式配置模块，集中管理所有UI相关的样式参数。
"""

from loguru import logger
from PyQt5.QtCore import QPoint, QRect
from PyQt5.QtWidgets import QApplication


def get_screen_info():
    """获取主屏幕信息。"""
    app = QApplication.instance()
    screen = app.primaryScreen()
    dpi = screen.logicalDotsPerInch()
    geometry = screen.geometry()
    scale_factor = dpi / 96.0  # 96 DPI是Windows的标准DPI
    # logger.info(f"屏幕DPI: {dpi}, 屏幕尺寸: {geometry.width()}x{geometry.height()}, 缩放因子: {scale_factor}")

    return {
        "dpi": dpi,
        "width": geometry.width(),
        "height": geometry.height(),
        "scale_factor": scale_factor,
    }


def scale_size(size, min_size=None):
    """
    根据DPI缩放尺寸。

    Args:
        size: (width, height) 元组
        min_size: (min_width, min_height) 最小尺寸元组，默认为None

    Returns:
        缩放后的 (width, height) 元组
    """
    try:
        # 获取缩放因子
        scale_factor = get_screen_info()["scale_factor"]

        # 计算缩放后的尺寸
        scaled_width = int(size[0] * scale_factor)
        scaled_height = int(size[1] * scale_factor)

        # 如果指定了最小尺寸，确保不小于最小尺寸
        if min_size:
            scaled_width = max(scaled_width, min_size[0])
            scaled_height = max(scaled_height, min_size[1])

        return (scaled_width, scaled_height)
    except Exception:
        # 如果获取缩放信息失败，返回原始尺寸
        return size


# 基准窗口尺寸（按1080p，100%缩放设计）
BASE_WINDOW_SIZES = {
    "config_editor": (800, 600),
    "file_type_selector": (400, 500),
    "person_selector": (500, 600),
}

# 最小窗口尺寸
MIN_WINDOW_SIZES = {
    "config_editor": (600, 400),
    "file_type_selector": (300, 400),
    "person_selector": (400, 500),
}


def get_window_size(window_type):
    """
    获取指定窗口类型的缩放后尺寸。

    Args:
        window_type: 窗口类型名称

    Returns:
        缩放后的 (width, height) 元组
    """
    base_size = BASE_WINDOW_SIZES.get(window_type)
    min_size = MIN_WINDOW_SIZES.get(window_type)
    if base_size:
        return scale_size(base_size, min_size)
    return base_size


# 字体设置
def get_font_size(base_size):
    """根据DPI缩放获取字体大小。"""
    try:
        scale_factor = get_screen_info()["scale_factor"]
        return max(int(base_size * scale_factor), base_size)
    except Exception:
        return base_size


# 基准字体大小
BASE_FONT_SIZES = {"default": 9, "large": 10, "small": 8}


def get_font_config():
    """获取缩放后的字体配置。"""
    return {
        "default": {"family": "Microsoft YaHei", "size": get_font_size(BASE_FONT_SIZES["default"])},
        "large": {"family": "Microsoft YaHei", "size": get_font_size(BASE_FONT_SIZES["large"])},
        "small": {"family": "Microsoft YaHei", "size": get_font_size(BASE_FONT_SIZES["small"])},
    }


# 表格列宽
def get_column_width(base_width):
    """根据DPI缩放获取列宽。"""
    try:
        scale_factor = get_screen_info()["scale_factor"]
        return int(base_width * scale_factor)
    except Exception:
        return base_width


# 基准列宽
BASE_COLUMN_WIDTHS = {
    "file_types": {
        "name": 180,  # 名称列
        "id": 100,  # ID列
        "directory": 180,  # 目录列
        "description": 300,  # 描述列
    },
    "person_fields": {
        "name": 150,  # 名称列
        "id": 100,  # ID列
        "description": 200,  # 描述列
        "required": 80,  # 必填列
        "default": 150,  # 默认值列
    },
}


def get_column_widths():
    """获取缩放后的列宽配置。"""
    return {
        "file_types": {k: get_column_width(v) for k, v in BASE_COLUMN_WIDTHS["file_types"].items()},
        "person_fields": {
            k: get_column_width(v) for k, v in BASE_COLUMN_WIDTHS["person_fields"].items()
        },
    }


def get_style_sheets():
    """获取根据DPI缩放调整后的样式表。"""
    fonts = get_font_config()
    return {
        "main_window": f"""
            QWidget {{
                font-family: "{fonts['default']['family']}";
                font-size: {fonts['default']['size']}pt;
            }}
            QLabel {{
                font-size: {fonts['default']['size']}pt;
            }}
            QPushButton {{
                min-width: {get_column_width(80)}px;
                min-height: {get_column_width(25)}px;
                padding: {get_font_size(5)}px;
            }}
            QTreeWidget {{
                font-size: {fonts['default']['size']}pt;
            }}
            QLineEdit {{
                min-height: {get_column_width(25)}px;
                padding: {get_font_size(2)}px {get_font_size(5)}px;
            }}
        """,
        "tip_label": f"""
            color: gray;
            font-style: italic;
            font-size: {fonts['small']['size']}pt;
            margin: {get_font_size(5)}px;
        """,
        "group_box": f"""
            QGroupBox {{
                font-size: {fonts['default']['size']}pt;
                font-weight: bold;
                margin-top: {get_font_size(10)}px;
                padding-top: {get_font_size(15)}px;
            }}
        """,
    }
