#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FileOperationResult类的单元测试。
"""

import unittest
from datetime import datetime

from src.core.operation_result import FileOperationResult


class TestFileOperationResult(unittest.TestCase):
    """测试FileOperationResult类的功能。"""

    def test_init(self):
        """测试FileOperationResult初始化。"""
        # 基本初始化
        result = FileOperationResult(
            success=True,
            message="测试消息",
            source_path="/path/to/source",
            destination_path="/path/to/destination",
            operation_type="copy",
        )

        # 验证属性
        self.assertTrue(result.success)
        self.assertEqual("测试消息", result.message)
        self.assertEqual("/path/to/source", result.source_path)
        self.assertEqual("/path/to/destination", result.destination_path)
        self.assertEqual("copy", result.operation_type)
        self.assertIsNone(result.error)
        self.assertIsInstance(result.timestamp, datetime)

        # 测试带异常的初始化
        test_error = ValueError("测试错误")
        result = FileOperationResult(
            success=False, message="错误消息", source_path="/path/to/source", error=test_error
        )

        # 验证属性
        self.assertFalse(result.success)
        self.assertEqual("错误消息", result.message)
        self.assertEqual("/path/to/source", result.source_path)
        self.assertIsNone(result.destination_path)
        self.assertEqual("", result.operation_type)
        self.assertEqual(test_error, result.error)

    def test_str(self):
        """测试FileOperationResult的字符串表示。"""
        # 成功结果
        result = FileOperationResult(
            success=True, message="成功消息", source_path="/path/to/source", operation_type="copy"
        )

        # 验证字符串表示包含正确信息
        str_representation = str(result)
        self.assertIn("copy", str_representation)
        self.assertIn("成功", str_representation)
        self.assertIn("成功消息", str_representation)

        # 失败结果
        result = FileOperationResult(
            success=False, message="失败消息", source_path="/path/to/source", operation_type="move"
        )

        # 验证字符串表示包含正确信息
        str_representation = str(result)
        self.assertIn("move", str_representation)
        self.assertIn("失败", str_representation)
        self.assertIn("失败消息", str_representation)

    def test_as_dict(self):
        """测试将FileOperationResult转换为字典。"""
        test_error = ValueError("测试错误")
        result = FileOperationResult(
            success=True,
            message="测试消息",
            source_path="/path/to/source",
            destination_path="/path/to/destination",
            operation_type="rename",
            error=test_error,
        )

        # 转换为字典
        result_dict = result.as_dict()

        # 验证字典内容
        self.assertTrue(result_dict["success"])
        self.assertEqual("测试消息", result_dict["message"])
        self.assertEqual("/path/to/source", result_dict["source_path"])
        self.assertEqual("/path/to/destination", result_dict["destination_path"])
        self.assertEqual("rename", result_dict["operation_type"])
        self.assertEqual("测试错误", result_dict["error"])
        self.assertIsInstance(result_dict["timestamp"], str)

        # 无错误的情况
        result = FileOperationResult(success=True, message="无错误", source_path="/path/to/source")

        result_dict = result.as_dict()
        self.assertIsNone(result_dict["error"])


if __name__ == "__main__":
    unittest.main()
