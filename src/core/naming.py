#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
命名规则引擎模块，负责根据模式生成文件名。
"""

import os
import re
import string
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from loguru import logger


class NamingEngine:
    """文件命名规则引擎，负责根据模式生成文件名。"""

    # Windows文件名长度限制
    MAX_FILENAME_LENGTH = 240

    # Windows文件名中的非法字符
    INVALID_CHARS = r'[<>:"/\\|?*]'

    # 支持的占位符列表
    PLACEHOLDERS = {
        "person": "人员目录名",
        "person_name": "人员姓名",
        "person_id": "人员ID",
        "person_department": "人员部门",
        "person_position": "人员职位",
        "person_contact": "人员联系方式",
        "department": "人员部门（简写形式）",
        "position": "人员职位（简写形式）",
        "type": "文件类型目录名",
        "type_name": "文件类型名称",
        "type_id": "文件类型ID",
        "original_filename": "原始文件名（不含扩展名）",
        "original_extension": "原始文件扩展名（含点号）",
        "original_name": "完整的原始文件名（含扩展名）",
        "date": "当前日期（格式：YYYY-MM-DD）",
        "time": "当前时间（格式：HHMMSS）",
        "datetime": "当前日期时间（格式：YYYYMMDD_HHMMSS）",
        "year": "当前年份",
        "month": "当前月份",
        "day": "当前日",
        "hour": "当前小时",
        "minute": "当前分钟",
        "second": "当前秒",
        # 注：除了上述标准占位符外，person和file_type字典中的所有字段都可以直接作为占位符使用
        # 例如，如果person中有'title'字段，可以使用{title}或{person_title}作为占位符
    }

    def __init__(self, pattern: str):
        """
        初始化命名引擎。

        Args:
            pattern: 命名模式，如"{person}_{type}_{original_filename}"
        """
        self.pattern = pattern
        self._placeholders = self._parse_pattern(pattern)

    def generate_name(
        self,
        original_filename: str,
        person: Optional[Dict[str, Any]] = None,
        file_type: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> str:
        """
        根据模式生成文件名。

        Args:
            original_filename: 原始文件名
            person: 人员信息字典
            file_type: 文件类型信息字典
            **kwargs: 其他可选参数

        Returns:
            str: 生成的文件名
        """
        # 提取变量用于替换
        variables = self._extract_variables(original_filename, person, file_type, **kwargs)

        # 检查是否所有必需的占位符都已提供
        for placeholder in self._placeholders:
            if placeholder not in variables and placeholder not in self.PLACEHOLDERS:
                logger.warning(f"命名模式中包含未找到的占位符: {placeholder}，将替换为空字符串")
                variables[placeholder] = ""
            elif placeholder not in variables:
                variables[placeholder] = ""

        # 替换占位符
        try:
            new_filename = self.pattern.format(**variables)

            # 清理文件名中的非法字符
            new_filename = self.sanitize_filename(new_filename)

            # 确保文件名不超过最大长度
            if len(new_filename) > self.MAX_FILENAME_LENGTH:
                name, ext = os.path.splitext(new_filename)
                # 截断文件名，保留扩展名
                new_filename = name[: self.MAX_FILENAME_LENGTH - len(ext)] + ext
                logger.warning(f"文件名超过最大长度，已截断: {new_filename}")

            return new_filename

        except KeyError as e:
            logger.error(f"命名模式中包含未知占位符: {e}")
            # 如果替换失败，返回原始文件名
            return os.path.basename(original_filename)

    def sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除非法字符。

        Args:
            filename: 原始文件名

        Returns:
            str: 清理后的文件名
        """
        # 移除Windows文件名中的非法字符
        clean_name = re.sub(self.INVALID_CHARS, "_", filename)

        # 移除前导和尾随空格和点
        clean_name = clean_name.strip(" .")

        # 替换连续的点为单个点
        clean_name = re.sub(r"\.+", ".", clean_name)

        # 如果文件名为空，使用默认名称
        if not clean_name:
            clean_name = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return clean_name

    def get_supported_placeholders(self) -> Dict[str, str]:
        """
        获取支持的占位符列表。

        Returns:
            Dict[str, str]: 占位符及其描述字典
        """
        return self.PLACEHOLDERS.copy()

    def get_used_placeholders(self) -> Set[str]:
        """
        获取当前模式中使用的占位符。

        Returns:
            Set[str]: 使用的占位符集合
        """
        return self._placeholders

    def _parse_pattern(self, pattern: str) -> Set[str]:
        """
        解析命名模式，提取占位符。

        Args:
            pattern: 命名模式

        Returns:
            Set[str]: 模式中使用的占位符集合
        """
        # 使用正则表达式匹配大括号中的内容
        placeholders = set(re.findall(r"\{([^{}]+)\}", pattern))

        # 验证占位符是否都是支持的
        for ph in placeholders:
            # 去除格式化部分，如{date:%Y-%m-%d}中的:%Y-%m-%d
            ph_name = ph.split(":")[0] if ":" in ph else ph

            # 只记录日志，不再返回原始文件名
            if ph_name not in self.PLACEHOLDERS:
                logger.info(f"使用了非标准占位符: {ph_name}，将从数据字典中查找")

        return placeholders

    def _extract_variables(
        self,
        original_filename: str,
        person: Optional[Dict[str, Any]] = None,
        file_type: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        提取用于替换占位符的变量。

        Args:
            original_filename: 原始文件名
            person: 人员信息字典
            file_type: 文件类型信息字典
            **kwargs: 其他可选参数

        Returns:
            Dict[str, Any]: 变量字典
        """
        variables = {}

        # 处理原始文件名相关的占位符
        path = Path(original_filename)
        stem = path.stem  # 不含扩展名的文件名
        suffix = path.suffix  # 扩展名（含点号）

        variables["original_filename"] = stem
        variables["original_extension"] = suffix
        variables["original_name"] = path.name

        # 处理人员相关的占位符
        if person:
            variables["person_id"] = person.get("id", "")
            variables["person_name"] = person.get("name", "")
            variables["person"] = person.get("directory", variables["person_name"])

            # 支持person字典中的所有字段作为占位符
            for key, value in person.items():
                # 避免与已有的标准占位符冲突
                if f"person_{key}" not in variables:
                    variables[f"person_{key}"] = value
                # 直接支持使用字段名作为占位符
                if key not in variables:
                    variables[key] = value

        # 处理文件类型相关的占位符
        if file_type:
            variables["type_id"] = file_type.get("id", "")
            variables["type_name"] = file_type.get("name", "")
            variables["type"] = file_type.get("directory", variables["type_name"])

            # 支持file_type字典中的所有字段作为占位符
            for key, value in file_type.items():
                # 避免与已有的标准占位符冲突
                if f"type_{key}" not in variables:
                    variables[f"type_{key}"] = value

        # 处理日期时间相关的占位符
        now = datetime.now()
        variables["date"] = now.strftime("%Y-%m-%d")
        variables["time"] = now.strftime("%H%M%S")
        variables["datetime"] = now.strftime("%Y%m%d_%H%M%S")
        variables["year"] = now.strftime("%Y")
        variables["month"] = now.strftime("%m")
        variables["day"] = now.strftime("%d")
        variables["hour"] = now.strftime("%H")
        variables["minute"] = now.strftime("%M")
        variables["second"] = now.strftime("%S")

        # 添加其他自定义变量
        variables.update(kwargs)

        return variables
