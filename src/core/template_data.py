import re
import string
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

try:
    from pypinyin import Style, lazy_pinyin

    PINYIN_SUPPORT = True
except ImportError:
    PINYIN_SUPPORT = False


class TemplateData:

    # 处理模板数据
    def get_template_data(
        self, person: Dict[str, Any] = None, file_type: Dict[str, Any] = None, **kwargs
    ):
        # 获取当前日期和时间
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H%M%S")
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        hour = now.strftime("%H")
        minute = now.strftime("%M")
        second = now.strftime("%S")

        template_data = {
            "date": today,
            "time": time_str,
            "year": year,
            "month": month,
            "day": day,
            "hour": hour,
            "minute": minute,
            "second": second,
        }
        if person:
            name = str(person.get("name") or person.get("directory") or "fixture")
            template_data["person_name"] = name
            template_data["name"] = self._sanitize_directory_name(name.lower())
            template_data["person_id"] = person.get("id", "")
            template_data["id"] = person.get("id", "")
            template_data["name_pinyin"] = self._get_pinyin(name)
            template_data["name_first_letter"] = self._get_pinyin_first_letters(name)
            template_data["name_first_letters"] = template_data["name_first_letter"]
            template_data["person"] = (
                person.get("directory") or name.lower()
            )
        if file_type:
            template_data["type"] = (
                file_type.get("directory") or file_type.get("name", "")
            )
            template_data["type_name"] = file_type.get("name", "")
        template_data.update(kwargs)
        return template_data

    @staticmethod
    def render(template_string: str, **kwargs) -> str:
        """
        使用提供的参数渲染目录模板。

        Args:
            template_string: 模板字符串
            **kwargs: 用于替换模板中占位符的参数

        Returns:
            str: 渲染后的目录路径

        Raises:
            KeyError: 如果模板中包含未提供值的占位符
        """
        try:
            # 使用string.Formatter处理自定义格式化选项
            formatter = string.Formatter()
            result = ""

            # 逐段处理模板
            for literal_text, field_name, format_spec, _ in formatter.parse(template_string):
                result += literal_text

                if field_name is not None:
                    # 获取字段值
                    value = kwargs[field_name]

                    # 应用格式化规范（如果有）
                    if format_spec:
                        value = formatter.format_field(value, format_spec)

                    result += str(value)

            return result
        except KeyError as e:
            logger.error(f"目录模板渲染失败，缺少必要参数: {str(e)}")
            raise KeyError(f"目录模板缺少必要参数: {str(e)}")

    def _get_pinyin(self, text: str) -> str:
        """
        获取文本的拼音全拼。

        Args:
            text: 要转换的文本

        Returns:
            str: 拼音字符串
        """
        if PINYIN_SUPPORT:
            try:
                # 使用pypinyin获取拼音
                pinyin_list = lazy_pinyin(text)
                return "".join(pinyin_list).lower()
            except Exception as e:
                logger.warning(f"获取拼音失败: {str(e)}")

        # 如果没有pypinyin或者出错，简单处理非ASCII字符
        return self._sanitize_directory_name(text.lower())

    def _get_pinyin_first_letters(self, text: str) -> str:
        """
        获取文本的拼音首字母。

        Args:
            text: 要转换的文本

        Returns:
            str: 拼音首字母字符串
        """
        if PINYIN_SUPPORT:
            try:
                # 使用pypinyin获取拼音首字母
                first_letters = lazy_pinyin(text, style=Style.FIRST_LETTER)
                return "".join(first_letters).lower()
            except Exception as e:
                logger.warning(f"获取拼音首字母失败: {str(e)}")

        # 如果没有pypinyin或者出错，返回第一个字符
        return text[0].lower() if text else ""

    def _sanitize_directory_name(self, name: str) -> str:
        """
        清理目录名称，移除不允许用于文件名的字符。

        Args:
            name: 原始名称

        Returns:
            str: 清理后的名称
        """
        # 移除不允许用于文件名的字符
        # Windows文件名不能包含: \/:*?"<>|
        sanitized = re.sub(r'[\\/:*?"<>|]', "", name)

        # 替换空格为下划线
        sanitized = sanitized.replace(" ", "_")

        # 确保名称不为空
        if not sanitized:
            sanitized = "unnamed"

        return sanitized
