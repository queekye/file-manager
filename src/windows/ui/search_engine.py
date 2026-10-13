#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
人员搜索引擎模块，支持全名、拼音全拼和拼音首字母搜索。
"""

import re
from typing import Any, Dict, List, Optional, Set

from loguru import logger
from pypinyin import Style, lazy_pinyin


class PersonSearchEngine:
    """人员搜索引擎，支持全名、拼音全拼和拼音首字母搜索。"""

    def __init__(self, persons: List[Dict[str, Any]]):
        """
        初始化搜索引擎。

        Args:
            persons: 人员列表，每个人员为包含id和name的字典
        """
        self.persons = persons
        self.name_index = {}
        self.pinyin_index = {}
        self.pinyin_first_letter_index = {}
        self._build_indices()

    def log_info(self, message: str) -> None:
        """记录信息日志。"""
        logger.info(message)

    def log_error(self, message: str, exc_info: Optional[Exception] = None) -> None:
        """记录错误日志。"""
        if exc_info:
            logger.error(f"{message}: {exc_info}", exc_info=True)
        else:
            logger.error(message)

    def update_persons(self, persons: List[Dict[str, Any]]) -> None:
        """
        更新人员列表并重建索引。

        Args:
            persons: 新的人员列表
        """
        try:
            # 直接更新人员列表并完全重建索引
            self.persons = persons

            # 清空所有索引
            self.name_index = {}
            self.pinyin_index = {}
            self.pinyin_first_letter_index = {}

            # 重建索引
            self._build_indices()

            self.log_info(f"已完全更新人员列表和索引，当前共有 {len(self.persons)} 个人员")
        except Exception as e:
            self.log_error("更新人员列表时发生错误", e)

    def add_person(self, person: Dict[str, Any]) -> None:
        """
        添加单个人员到索引中。

        Args:
            person: 要添加的人员信息
        """
        try:
            if person not in self.persons:
                self.persons.append(person)

            # 添加到索引
            name = person["name"]

            # 全名索引
            self.name_index[name] = person

            # 拼音全拼索引
            pinyin = self._get_pinyin(name)
            if pinyin not in self.pinyin_index:
                self.pinyin_index[pinyin] = []
            self.pinyin_index[pinyin].append(person)

            # 拼音首字母索引
            first_letters = self._get_pinyin_first_letters(name)
            if first_letters not in self.pinyin_first_letter_index:
                self.pinyin_first_letter_index[first_letters] = []
            self.pinyin_first_letter_index[first_letters].append(person)

            # 为名字的每个字也建立索引
            if len(name) > 1:
                for char in name:
                    char_pinyin = self._get_pinyin(char)
                    if char_pinyin not in self.pinyin_index:
                        self.pinyin_index[char_pinyin] = []
                    self.pinyin_index[char_pinyin].append(person)

                    char_first_letter = self._get_pinyin_first_letters(char)
                    if char_first_letter not in self.pinyin_first_letter_index:
                        self.pinyin_first_letter_index[char_first_letter] = []
                    self.pinyin_first_letter_index[char_first_letter].append(person)

            self.log_info(f"已添加人员到索引: {name} (ID: {person['id']})")
        except Exception as e:
            self.log_error("添加人员到索引时发生错误", e)

    def _build_indices(self) -> None:
        """构建搜索索引。"""
        try:
            for person in self.persons:
                self.add_person(person)

            self.log_info(f"已为 {len(self.persons)} 个人员构建搜索索引")
        except Exception as e:
            self.log_error("构建搜索索引时发生错误", e)

    def _get_pinyin(self, text: str) -> str:
        """
        获取文本的拼音全拼。

        Args:
            text: 要处理的文本

        Returns:
            拼音全拼
        """
        try:
            # 获取文本拼音
            pinyin_list = lazy_pinyin(text)
            return "".join(pinyin_list).lower()
        except Exception as e:
            self.log_error(f"获取文本拼音时发生错误: {text}", e)
            return text.lower()  # 失败时返回原文本小写形式

    def _get_pinyin_first_letters(self, text: str) -> str:
        """
        获取文本拼音的首字母。

        Args:
            text: 要处理的文本

        Returns:
            拼音首字母
        """
        try:
            # 获取文本拼音首字母
            pinyin_list = lazy_pinyin(text, style=Style.FIRST_LETTER)
            return "".join(pinyin_list).lower()
        except Exception as e:
            self.log_error(f"获取文本拼音首字母时发生错误: {text}", e)
            return text.lower()  # 失败时返回原文本小写形式

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        搜索人员。

        Args:
            query: 搜索关键词

        Returns:
            匹配的人员列表
        """
        if not query:
            return self.persons.copy()

        try:
            # 转换为小写
            query = query.lower()
            self.log_info(f"搜索人员: {query}")

            # 结果列表
            results = []

            # 判断查询类型
            is_chinese = self._is_chinese(query)
            is_pinyin = self._is_pinyin(query)

            # 1. 全中文查询 - 优先精确匹配
            if is_chinese:
                # 全名精确匹配
                if query in self.name_index:
                    results.append(self.name_index[query])

                # 如果没有精确匹配，尝试包含匹配（例如搜索"张三"可以找到"张三丰"）
                contain_matches = []
                for name in self.name_index.keys():
                    if query in name.lower():
                        contain_matches.append(self.name_index[name])
                results.extend(contain_matches)

            # 2. 拼音全拼查询
            elif is_pinyin:
                # 拼音首字母精确匹配
                if query in self.pinyin_first_letter_index:
                    results.extend(self.pinyin_first_letter_index[query])

                # 拼音首字母前缀匹配
                for first_letters, persons in self.pinyin_first_letter_index.items():
                    if query in first_letters:
                        results.extend(persons)

                # 拼音全拼精确匹配
                if query in self.pinyin_index:
                    results.extend(self.pinyin_index[query])

                # 拼音全拼前缀匹配
                for pinyin, persons in self.pinyin_index.items():
                    if query in pinyin:
                        results.extend(persons)

            # 4. 其他查询（混合字符）- 使用所有策略
            else:
                # 全名匹配
                if query in self.name_index:
                    results.append(self.name_index[query])

                # 转换查询为拼音和首字母
                query_pinyin = self._get_pinyin(query)
                query_first_letters = self._get_pinyin_first_letters(query)

                # 拼音全拼匹配
                if query_pinyin in self.pinyin_index:
                    results.extend(self.pinyin_index[query_pinyin])

                # 拼音首字母匹配
                if query_first_letters in self.pinyin_first_letter_index:
                    results.extend(self.pinyin_first_letter_index[query_first_letters])

                # 前缀匹配
                for pinyin, persons in self.pinyin_index.items():
                    if pinyin.startswith(query_pinyin):
                        results.extend(persons)

                for first_letters, persons in self.pinyin_first_letter_index.items():
                    if first_letters.startswith(query_first_letters):
                        results.extend(persons)

                # 包含匹配
                if len(query) >= 2:
                    for person in self.persons:
                        name = person["name"]
                        if (
                            query in name.lower()
                            or query_pinyin in self._get_pinyin(name)
                            or query_first_letters in self._get_pinyin_first_letters(name)
                        ):
                            results.append(person)

            # 去重
            unique_results = []
            seen_ids = set()
            for person in results:
                if person["id"] not in seen_ids:
                    unique_results.append(person)
                    seen_ids.add(person["id"])

            self.log_info(f"搜索结果: {len(unique_results)} 个人员")
            return unique_results

        except Exception as e:
            self.log_error("搜索人员时发生错误", e)
            return []

    def _is_chinese(self, text: str) -> bool:
        """
        判断文本是否是中文。

        Args:
            text: 要判断的文本

        Returns:
            是否为中文
        """
        # 使用正则表达式判断是否包含中文字符
        return bool(re.search(r"[\u4e00-\u9fff]", text))

    def _is_pinyin(self, text: str) -> bool:
        """
        判断文本是否是拼音。

        Args:
            text: 要判断的文本

        Returns:
            是否为拼音
        """
        # 简单判断是否只包含拼音字符（字母）
        return bool(re.match(r"^[a-z]+$", text))

    def _is_first_letter(self, text: str) -> bool:
        """
        判断文本是否是拼音首字母。

        Args:
            text: 要判断的文本

        Returns:
            是否为拼音首字母
        """
        # 简单判断是否只包含字母且长度较短
        return bool(re.match(r"^[a-z]+$", text)) and len(text) <= 5

    def remove_person(self, person_id: str) -> None:
        """
        从索引中移除人员。

        Args:
            person_id: 要移除的人员ID
        """
        try:
            # 找到要移除的人员
            person_to_remove = None
            for person in self.persons:
                if person["id"] == person_id:
                    person_to_remove = person
                    break

            if not person_to_remove:
                self.log_info(f"未找到要移除的人员: {person_id}")
                return

            # 从人员列表中移除
            self.persons.remove(person_to_remove)

            # 从全名索引中移除
            name = person_to_remove["name"]
            if name in self.name_index:
                del self.name_index[name]

            # 从拼音全拼索引中移除
            pinyin = self._get_pinyin(name)
            if pinyin in self.pinyin_index:
                self.pinyin_index[pinyin] = [
                    p for p in self.pinyin_index[pinyin] if p["id"] != person_id
                ]
                if not self.pinyin_index[pinyin]:
                    del self.pinyin_index[pinyin]

            # 从拼音首字母索引中移除
            first_letters = self._get_pinyin_first_letters(name)
            if first_letters in self.pinyin_first_letter_index:
                self.pinyin_first_letter_index[first_letters] = [
                    p for p in self.pinyin_first_letter_index[first_letters] if p["id"] != person_id
                ]
                if not self.pinyin_first_letter_index[first_letters]:
                    del self.pinyin_first_letter_index[first_letters]

            # 为名字的每个字也移除索引
            if len(name) > 1:
                for char in name:
                    char_pinyin = self._get_pinyin(char)
                    if char_pinyin in self.pinyin_index:
                        self.pinyin_index[char_pinyin] = [
                            p for p in self.pinyin_index[char_pinyin] if p["id"] != person_id
                        ]
                        if not self.pinyin_index[char_pinyin]:
                            del self.pinyin_index[char_pinyin]

                    char_first_letter = self._get_pinyin_first_letters(char)
                    if char_first_letter in self.pinyin_first_letter_index:
                        self.pinyin_first_letter_index[char_first_letter] = [
                            p
                            for p in self.pinyin_first_letter_index[char_first_letter]
                            if p["id"] != person_id
                        ]
                        if not self.pinyin_first_letter_index[char_first_letter]:
                            del self.pinyin_first_letter_index[char_first_letter]

            self.log_info(f"已从索引中移除人员: {name} (ID: {person_id})")
        except Exception as e:
            self.log_error("从索引中移除人员时发生错误", e)
