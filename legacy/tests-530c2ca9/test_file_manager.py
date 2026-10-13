#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FileManager类的基础功能单元测试。
测试文件的基本操作（复制、移动、重命名）、错误处理、操作历史和撤销功能。
"""

import os
import shutil
import tempfile
import unittest

from src.core.directory_manager import DirectoryManager
from src.core.exceptions import FileNotFoundError
from src.core.file_manager import FileManager


class TestFileManager(unittest.TestCase):
    """测试FileManager类的基础功能。"""

    def setUp(self):
        """测试前创建临时目录和文件。"""
        # 创建临时目录作为基础目录
        self.temp_dir = tempfile.mkdtemp()

        # 创建临时源文件
        self.source_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.source_dir, "test_file.txt")
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("测试内容")

        # 创建DirectoryManager和FileManager实例
        self.directory_manager = DirectoryManager(self.temp_dir)
        self.file_manager = FileManager(self.directory_manager)

        # 测试用的基础目录
        self.target_dir = os.path.join(self.temp_dir, "target")

        # 创建目标目录
        os.makedirs(self.target_dir, exist_ok=True)

    def tearDown(self):
        """测试后删除临时目录。"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.source_dir, ignore_errors=True)

    def test_basic_copy(self):
        """测试基本的文件复制功能。"""
        # 执行复制
        result = self.file_manager.copy_file(
            self.test_file, {"directory": "target"}, {"directory": ""}
        )

        # 验证结果
        self.assertTrue(result.success)
        self.assertEqual("copy", result.operation_type)
        self.assertTrue(os.path.exists(result.destination_path))

        # 验证源文件仍然存在
        self.assertTrue(os.path.exists(self.test_file))

        # 验证文件内容
        with open(result.destination_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual("测试内容", content)

    def test_basic_move(self):
        """测试基本的文件移动功能。"""
        # 创建用于移动的测试文件
        move_test_file = os.path.join(self.source_dir, "move_test.txt")
        with open(move_test_file, "w", encoding="utf-8") as f:
            f.write("移动测试内容")

        # 执行移动
        result = self.file_manager.move_file(
            move_test_file, {"directory": "target"}, {"directory": ""}
        )

        # 验证结果
        self.assertTrue(result.success)
        self.assertEqual("move", result.operation_type)

        # 验证源文件不存在
        self.assertFalse(os.path.exists(move_test_file))

        # 验证目标文件存在且内容正确
        self.assertTrue(os.path.exists(result.destination_path))
        with open(result.destination_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual("移动测试内容", content)

    def test_basic_rename(self):
        """测试基本的文件重命名功能。"""
        # 创建用于重命名的测试文件
        rename_test_file = os.path.join(self.source_dir, "rename_test.txt")
        with open(rename_test_file, "w", encoding="utf-8") as f:
            f.write("重命名测试内容")

        # 执行重命名
        new_name = "renamed_file.txt"
        result = self.file_manager.rename_file(rename_test_file, new_name)

        # 验证结果
        self.assertTrue(result.success)
        self.assertEqual("rename", result.operation_type)

        # 验证文件已重命名
        new_path = os.path.join(self.source_dir, new_name)
        self.assertFalse(os.path.exists(rename_test_file))
        self.assertTrue(os.path.exists(new_path))

        # 验证文件内容未变
        with open(new_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual("重命名测试内容", content)

    def test_error_handling(self):
        """测试错误处理功能。"""
        # 测试复制不存在的文件
        with self.assertRaises(FileNotFoundError):
            self.file_manager.copy_file(
                os.path.join(self.source_dir, "nonexistent.txt"),
                {"directory": "target"},
                {"directory": ""},
            )

        # 测试移动不存在的文件
        with self.assertRaises(FileNotFoundError):
            self.file_manager.move_file(
                os.path.join(self.source_dir, "nonexistent.txt"),
                {"directory": "target"},
                {"directory": ""},
            )

        # 测试重命名不存在的文件
        with self.assertRaises(FileNotFoundError):
            self.file_manager.rename_file(
                os.path.join(self.source_dir, "nonexistent.txt"), "new.txt"
            )

        # 测试重命名到已存在的文件名
        # 创建一个新的测试文件
        test_file = os.path.join(self.source_dir, "test_rename.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("测试重命名")

        # 创建一个已存在的文件
        existing_file = os.path.join(self.source_dir, "existing.txt")
        with open(existing_file, "w", encoding="utf-8") as f:
            f.write("已存在的文件")

        # 确保文件已经创建
        self.assertTrue(os.path.exists(test_file))
        self.assertTrue(os.path.exists(existing_file))

        # 测试重命名到已存在的文件名
        # 由于错误处理器会自动备份并删除已存在的文件，rename_file应该会成功
        # 不再使用 assertRaises，而是检查操作是否成功
        result = self.file_manager.rename_file(test_file, "existing.txt")

        # 验证结果
        self.assertTrue(result.success)
        self.assertEqual("rename", result.operation_type)

        # 验证源文件不再存在
        self.assertFalse(os.path.exists(test_file))

        # 验证目标文件存在
        renamed_file = os.path.join(self.source_dir, "existing.txt")
        self.assertTrue(os.path.exists(renamed_file))

        # 验证内容是否正确（应该是源文件的内容）
        with open(renamed_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual("测试重命名", content)

    def test_operation_history(self):
        """测试操作历史记录功能。"""
        # 初始应该没有历史记录
        self.assertEqual(0, len(self.file_manager.get_operation_history()))

        # 执行一系列操作
        # 复制操作
        self.file_manager.copy_file(self.test_file, {"directory": "target"}, {"directory": ""})

        # 创建移动测试文件
        move_test_file = os.path.join(self.source_dir, "move_test.txt")
        with open(move_test_file, "w", encoding="utf-8") as f:
            f.write("移动测试内容")

        # 移动操作
        self.file_manager.move_file(move_test_file, {"directory": "target"}, {"directory": ""})

        # 验证历史记录
        history = self.file_manager.get_operation_history()
        self.assertEqual(2, len(history))
        self.assertEqual("copy", history[0].operation_type)
        self.assertEqual("move", history[1].operation_type)
        self.assertTrue(all(op.success for op in history))

    def test_undo_operations(self):
        """测试操作撤销功能。"""
        # 执行复制操作
        copy_result = self.file_manager.copy_file(
            self.test_file, {"directory": "target"}, {"directory": ""}
        )
        copied_file = copy_result.destination_path

        # 撤销复制操作
        undo_result = self.file_manager.undo_last_operation()
        self.assertTrue(undo_result.success)
        self.assertEqual("undo_copy", undo_result.operation_type)
        self.assertFalse(os.path.exists(copied_file))

        # 执行移动操作
        move_test_file = os.path.join(self.source_dir, "move_test.txt")
        with open(move_test_file, "w", encoding="utf-8") as f:
            f.write("移动测试内容")

        move_result = self.file_manager.move_file(
            move_test_file, {"directory": "target"}, {"directory": ""}
        )
        moved_file = move_result.destination_path

        # 撤销移动操作
        undo_result = self.file_manager.undo_last_operation()
        self.assertTrue(undo_result.success)
        self.assertEqual("undo_move", undo_result.operation_type)
        self.assertTrue(os.path.exists(move_test_file))
        self.assertFalse(os.path.exists(moved_file))


if __name__ == "__main__":
    unittest.main()
