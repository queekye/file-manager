#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
命名规则引擎模块单元测试。
"""

import unittest
from datetime import datetime

from src.core.naming import NamingEngine


class TestNamingEngine(unittest.TestCase):
    """命名规则引擎测试用例。"""

    def setUp(self):
        """每个测试前准备环境。"""
        self.test_pattern = "{person}_{type}_{original_filename}{original_extension}"
        self.engine = NamingEngine(self.test_pattern)

        self.test_person = {"id": "001", "name": "张三", "directory": "zhangsan"}

        self.test_file_type = {"id": "contract", "name": "合同", "directory": "Contracts"}

        self.test_filename = "test_document.pdf"

    def test_init(self):
        """测试初始化。"""
        engine = NamingEngine(self.test_pattern)
        self.assertEqual(engine.pattern, self.test_pattern)

        # 测试占位符解析
        placeholders = engine.get_used_placeholders()
        self.assertIn("person", placeholders)
        self.assertIn("type", placeholders)
        self.assertIn("original_filename", placeholders)
        self.assertIn("original_extension", placeholders)

    def test_generate_name_basic(self):
        """测试基本文件名生成。"""
        # 测试基本替换
        new_name = self.engine.generate_name(
            self.test_filename, self.test_person, self.test_file_type
        )

        expected = "zhangsan_Contracts_test_document.pdf"
        self.assertEqual(new_name, expected)

    def test_generate_name_missing_data(self):
        """测试缺少数据时的文件名生成。"""
        # 测试缺少人员数据
        new_name = self.engine.generate_name(self.test_filename, None, self.test_file_type)

        # 缺少人员数据时，应当仍然替换可用的占位符
        self.assertTrue(new_name.startswith("_Contracts_"))
        self.assertTrue(new_name.endswith("test_document.pdf"))

        # 测试缺少文件类型数据
        new_name = self.engine.generate_name(self.test_filename, self.test_person, None)

        # 缺少文件类型数据时，应当仍然替换可用的占位符
        self.assertTrue(new_name.startswith("zhangsan__"))
        self.assertTrue(new_name.endswith("test_document.pdf"))

    def test_generate_name_custom_pattern(self):
        """测试自定义模式。"""
        # 测试包含日期时间的模式
        date_pattern = "{person}_{date}_{original_filename}{original_extension}"
        date_engine = NamingEngine(date_pattern)

        new_name = date_engine.generate_name(self.test_filename, self.test_person)

        # 获取当前日期用于比较
        today = datetime.now().strftime("%Y-%m-%d")
        expected = f"zhangsan_{today}_test_document.pdf"
        self.assertEqual(new_name, expected)

        # 测试完全自定义的模式
        custom_pattern = "Doc_{year}{month}{day}_{original_filename}"
        custom_engine = NamingEngine(custom_pattern)

        new_name = custom_engine.generate_name(self.test_filename)

        # 获取当前日期用于比较
        year = datetime.now().strftime("%Y")
        month = datetime.now().strftime("%m")
        day = datetime.now().strftime("%d")

        expected = f"Doc_{year}{month}{day}_test_document"
        self.assertEqual(new_name, expected)

    def test_sanitize_filename(self):
        """测试文件名清理。"""
        # 测试非法字符
        dirty_name = 'file<>:"/\|?*name.txt'
        clean_name = self.engine.sanitize_filename(dirty_name)
        expected = "file_________name.txt"
        self.assertEqual(clean_name, expected)

        # 测试前导和尾随空格和点
        dirty_name = " .file name. "
        clean_name = self.engine.sanitize_filename(dirty_name)
        expected = "file name"
        self.assertEqual(clean_name, expected)

        # 测试连续的点
        dirty_name = "file..name..txt"
        clean_name = self.engine.sanitize_filename(dirty_name)
        expected = "file.name.txt"
        self.assertEqual(clean_name, expected)

        # 测试空文件名
        dirty_name = "..."
        clean_name = self.engine.sanitize_filename(dirty_name)
        self.assertTrue(clean_name.startswith("file_"))  # 应生成默认名称

    def test_long_filename(self):
        """测试长文件名处理。"""
        # 创建一个超长的文件名
        long_filename = "a" * 300 + ".txt"

        new_name = self.engine.generate_name(long_filename, self.test_person, self.test_file_type)

        # 文件名长度应小于或等于最大长度
        self.assertLessEqual(len(new_name), NamingEngine.MAX_FILENAME_LENGTH)

        # 检查前缀和后缀是否正确
        self.assertTrue(new_name.startswith("zhangsan_Contracts_"))
        self.assertTrue(new_name.endswith(".txt"))

    def test_invalid_placeholder(self):
        """测试无效占位符。"""
        # 使用包含无效占位符的模式
        invalid_pattern = "{person}_{invalid_placeholder}_{original_filename}{original_extension}"
        invalid_engine = NamingEngine(invalid_pattern)

        # 无效占位符被替换为空''，应该返回"{person}__{original_filename}"
        new_name = invalid_engine.generate_name(self.test_filename, self.test_person)

        valid_new_name = "zhangsan__test_document.pdf"

        self.assertEqual(new_name, valid_new_name)

    def test_get_supported_placeholders(self):
        """测试获取支持的占位符列表。"""
        placeholders = self.engine.get_supported_placeholders()

        # 检查几个基本占位符是否存在
        self.assertIn("person", placeholders)
        self.assertIn("type", placeholders)
        self.assertIn("original_filename", placeholders)
        self.assertIn("date", placeholders)

        # 确保返回的是副本而非原始字典
        placeholders["test"] = "test"
        self.assertNotIn("test", self.engine.get_supported_placeholders())

    def test_get_used_placeholders(self):
        """测试获取使用的占位符列表。"""
        used = self.engine.get_used_placeholders()

        # 检查模式中使用的占位符是否被正确识别
        self.assertEqual(len(used), 4)
        self.assertIn("person", used)
        self.assertIn("type", used)
        self.assertIn("original_filename", used)
        self.assertIn("original_extension", used)

        # 测试不同的模式
        date_engine = NamingEngine("{date}_{time}_{original_name}")
        used = date_engine.get_used_placeholders()

        self.assertEqual(len(used), 3)
        self.assertIn("date", used)
        self.assertIn("time", used)
        self.assertIn("original_name", used)


if __name__ == "__main__":
    unittest.main()
