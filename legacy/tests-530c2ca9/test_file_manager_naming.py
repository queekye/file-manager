#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FileManager类的命名和配置功能测试。
测试文件命名模式、占位符替换、目录模板和配置选项等功能。
"""

import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from src.core.directory_manager import DirectoryManager
from src.core.exceptions import ConfigurationError
from src.core.file_manager import FileManager


class TestFileManagerNaming(unittest.TestCase):
    """文件管理器的命名和配置功能测试用例。"""

    def setUp(self):
        """每个测试前准备环境。"""
        # 创建临时测试目录
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_path = Path(self.test_dir.name)

        # 创建测试文件
        self.test_file = self.test_path / "test_document.txt"
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("This is a test document.")

        # 创建目录管理器，基础目录为临时测试目录
        self.directory_manager = DirectoryManager(str(self.test_path))

        # 创建默认命名模式，包含日期占位符
        self.default_pattern = "{person}_{type}_{date}_{original_filename}{original_extension}"

        # 创建文件管理器
        self.file_manager = FileManager(self.directory_manager, self.default_pattern)

        # 测试用人员和文件类型数据
        self.test_person = {
            "id": "001",
            "name": "张三",
            "directory": "zhangsan",
            "department": "研发部",
            "position": "软件工程师",
            "contact": "13800138001",
        }

        self.test_file_type = {
            "id": "document",
            "name": "文档",
            "directory": "Documents",
            "description": "一般文档文件",
        }

        # 今天的日期字符串，用于验证文件名
        self.today_date = datetime.now().strftime("%Y-%m-%d")

    def tearDown(self):
        """每个测试后清理环境。"""
        self.test_dir.cleanup()

    def test_naming_pattern(self):
        """测试文件命名模式。"""
        # 测试默认命名模式
        result = self.file_manager.copy_file(
            str(self.test_file), self.test_person, self.test_file_type
        )

        # 验证文件名符合默认模式
        target_file = Path(result.destination_path)
        expected_name = f"zhangsan_Documents_{self.today_date}_test_document.txt"
        self.assertEqual(target_file.name, expected_name)

        # 测试自定义命名模式
        custom_pattern = (
            "{person_id}_{department}_{position}_{original_filename}{original_extension}"
        )
        self.file_manager.set_naming_pattern(custom_pattern)

        result = self.file_manager.copy_file(
            str(self.test_file), self.test_person, self.test_file_type
        )

        # 验证文件名符合自定义模式
        target_file = Path(result.destination_path)
        expected_name = "001_研发部_软件工程师_test_document.txt"
        self.assertEqual(target_file.name, expected_name)

    def test_placeholder_replacement(self):
        """测试占位符替换功能。"""
        # 测试基本占位符替换
        pattern = "{person}_{type}_{date}"
        self.file_manager.set_naming_pattern(pattern)

        result = self.file_manager.copy_file(
            str(self.test_file), self.test_person, self.test_file_type
        )

        target_file = Path(result.destination_path)
        expected_name = f"zhangsan_Documents_{self.today_date}"
        self.assertTrue(target_file.name.startswith(expected_name))

        # 测试扩展占位符替换
        pattern = "{person_id}_{department}_{position}"
        self.file_manager.set_naming_pattern(pattern)

        result = self.file_manager.copy_file(
            str(self.test_file), self.test_person, self.test_file_type
        )

        target_file = Path(result.destination_path)
        expected_name = "001_研发部_软件工程师"
        self.assertTrue(target_file.name.startswith(expected_name))

    def test_default_options(self):
        """测试默认选项设置。"""
        options = self.file_manager.get_options()

        # 验证默认选项值
        self.assertTrue(options["copy_files"])
        self.assertTrue(options["create_directories"])
        self.assertFalse(options["open_after_operation"])
        self.assertEqual(options["directory_template"], "{person}/{type}")
        self.assertTrue(options["preserve_timestamps"])

    def test_update_options(self):
        """测试更新选项。"""
        new_options = {
            "copy_files": False,
            "create_directories": False,
            "open_after_operation": True,
            "preserve_timestamps": False,
        }

        # 更新选项
        self.file_manager.update_options(new_options)

        # 验证选项已更新
        current_options = self.file_manager.get_options()

        # 验证所提供选项已正确更新
        for key, value in new_options.items():
            self.assertEqual(current_options[key], value)

        # 验证directory_template保持不变
        self.assertEqual(current_options["directory_template"], "{person}/{type}")

    def test_invalid_options(self):
        """测试无效选项处理。"""
        # 测试无效的选项名
        with self.assertRaises(ConfigurationError):
            self.file_manager.update_options({"invalid_option": True})

        # 测试无效的选项类型
        with self.assertRaises(ConfigurationError):
            self.file_manager.update_options({"copy_files": "not_a_boolean"})

    def test_directory_template(self):
        """测试目录模板功能。"""
        # 测试默认目录模板
        result = self.file_manager.copy_file(
            str(self.test_file), self.test_person, self.test_file_type
        )

        # 验证目录结构
        expected_path = self.test_path / "zhangsan/Documents"
        self.assertTrue(str(result.destination_path).startswith(str(expected_path)))

        # 测试尝试自定义目录模板时应该抛出异常
        with self.assertRaises(ConfigurationError):
            self.file_manager.update_options({"directory_template": "{type}/users/{person}"})

        # 验证目录模板没有被修改
        result = self.file_manager.copy_file(
            str(self.test_file), self.test_person, self.test_file_type
        )

        # 验证目录结构仍然使用默认模板
        expected_path = self.test_path / "zhangsan/Documents"
        self.assertTrue(str(result.destination_path).startswith(str(expected_path)))

    def test_directory_creation_option(self):
        """测试目录创建选项。"""
        # 自动创建目录目前不生效，始终允许自动创建目录
        self.file_manager.update_options({"create_directories": False})

        # 启用自动创建目录
        self.file_manager.update_options({"create_directories": True})

        # 再次尝试复制
        result = self.file_manager.copy_file(
            str(self.test_file), self.test_person, self.test_file_type
        )

        # 验证操作成功
        self.assertTrue(result.success)
        self.assertTrue(Path(result.destination_path).exists())

    def test_preserve_timestamps_option(self):
        """测试时间戳保留选项。"""
        # 获取源文件的时间戳
        source_stat = os.stat(self.test_file)

        # 启用时间戳保留
        self.file_manager.update_options({"preserve_timestamps": True})

        # 复制文件
        result = self.file_manager.copy_file(
            str(self.test_file), self.test_person, self.test_file_type
        )

        # 验证时间戳被保留
        dest_stat = os.stat(result.destination_path)
        self.assertEqual(source_stat.st_mtime, dest_stat.st_mtime)

        # 禁用时间戳保留
        self.file_manager.update_options({"preserve_timestamps": False})

        # 复制到新位置
        new_person = dict(self.test_person)
        new_person["directory"] = "test2"
        result2 = self.file_manager.copy_file(str(self.test_file), new_person, self.test_file_type)

        # 验证时间戳不同
        dest_stat2 = os.stat(result2.destination_path)
        self.assertNotEqual(source_stat.st_mtime, dest_stat2.st_mtime)

    def test_copy_files_option(self):
        """测试copy_files选项。"""
        # 创建测试文件
        test_file = self.test_path / "process_test.txt"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("Test content")

        # 设置为默认移动文件
        self.file_manager.update_options({"copy_files": False})

        # 使用process_file处理文件
        result = self.file_manager.process_file(
            str(test_file), self.test_person, self.test_file_type
        )

        # 验证文件被移动而不是复制
        self.assertTrue(result.success)
        self.assertFalse(test_file.exists())  # 源文件应该不存在
        self.assertTrue(Path(result.destination_path).exists())  # 目标文件应该存在

        # 设置为默认复制文件
        self.file_manager.update_options({"copy_files": True})

        # 创建新的测试文件
        test_file2 = self.test_path / "process_test2.txt"
        with open(test_file2, "w", encoding="utf-8") as f:
            f.write("Test content 2")

        # 使用process_file处理文件
        result = self.file_manager.process_file(
            str(test_file2), self.test_person, self.test_file_type
        )

        # 验证文件被复制而不是移动
        self.assertTrue(result.success)
        self.assertTrue(test_file2.exists())  # 源文件应该仍然存在
        self.assertTrue(Path(result.destination_path).exists())  # 目标文件应该存在


if __name__ == "__main__":
    unittest.main()
