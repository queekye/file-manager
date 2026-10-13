#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
错误处理机制的测试模块。
"""

import os
import shutil
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.core.error_handling import (
    ErrorHandler,
    ErrorHandlingResult,
    ErrorLogger,
    ErrorRecord,
    FileOperationErrorHandler,
    RecoveryManager,
    retry_operation,
    with_error_handling,
)
from src.core.exceptions import (
    DirectoryNotFoundError,
    FileExistsError,
    FileNotFoundError,
    FileOperationError,
)


class ErrorRecordTests(unittest.TestCase):
    """ErrorRecord类的测试。"""

    def test_error_record_creation(self):
        """测试创建错误记录。"""
        record = ErrorRecord(
            error_code="TEST-001",
            error_type="TestError",
            message="测试错误消息",
            operation="test_operation",
            file_path="/path/to/file",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            stack_trace="测试堆栈跟踪",
            recovery_attempts=0,
            resolved=False,
        )

        self.assertEqual(record.error_code, "TEST-001")
        self.assertEqual(record.error_type, "TestError")
        self.assertEqual(record.message, "测试错误消息")
        self.assertEqual(record.operation, "test_operation")
        self.assertEqual(record.file_path, "/path/to/file")
        self.assertEqual(record.timestamp, datetime(2023, 1, 1, 12, 0, 0))
        self.assertEqual(record.stack_trace, "测试堆栈跟踪")
        self.assertEqual(record.recovery_attempts, 0)
        self.assertFalse(record.resolved)

    def test_to_dict(self):
        """测试转换为字典。"""
        record = ErrorRecord(
            error_code="TEST-001",
            error_type="TestError",
            message="测试错误消息",
            operation="test_operation",
            file_path="/path/to/file",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            stack_trace="测试堆栈跟踪",
            recovery_attempts=0,
            resolved=False,
        )

        record_dict = record.to_dict()

        self.assertEqual(record_dict["error_code"], "TEST-001")
        self.assertEqual(record_dict["error_type"], "TestError")
        self.assertEqual(record_dict["message"], "测试错误消息")
        self.assertEqual(record_dict["operation"], "test_operation")
        self.assertEqual(record_dict["file_path"], "/path/to/file")
        self.assertEqual(record_dict["timestamp"], "2023-01-01T12:00:00")
        self.assertEqual(record_dict["stack_trace"], "测试堆栈跟踪")
        self.assertEqual(record_dict["recovery_attempts"], 0)
        self.assertFalse(record_dict["resolved"])

    def test_from_dict(self):
        """测试从字典创建。"""
        record_dict = {
            "error_code": "TEST-001",
            "error_type": "TestError",
            "message": "测试错误消息",
            "operation": "test_operation",
            "file_path": "/path/to/file",
            "timestamp": "2023-01-01T12:00:00",
            "stack_trace": "测试堆栈跟踪",
            "recovery_attempts": 0,
            "resolved": False,
        }

        record = ErrorRecord.from_dict(record_dict)

        self.assertEqual(record.error_code, "TEST-001")
        self.assertEqual(record.error_type, "TestError")
        self.assertEqual(record.message, "测试错误消息")
        self.assertEqual(record.operation, "test_operation")
        self.assertEqual(record.file_path, "/path/to/file")
        self.assertEqual(record.timestamp, datetime(2023, 1, 1, 12, 0, 0))
        self.assertEqual(record.stack_trace, "测试堆栈跟踪")
        self.assertEqual(record.recovery_attempts, 0)
        self.assertFalse(record.resolved)

    def test_increment_recovery_attempts(self):
        """测试增加恢复尝试次数。"""
        record = ErrorRecord(
            error_code="TEST-001",
            error_type="TestError",
            message="测试错误消息",
            operation="test_operation",
            file_path="/path/to/file",
        )

        self.assertEqual(record.recovery_attempts, 0)
        record.increment_recovery_attempts()
        self.assertEqual(record.recovery_attempts, 1)
        record.increment_recovery_attempts()
        self.assertEqual(record.recovery_attempts, 2)

    def test_mark_as_resolved(self):
        """测试标记为已解决。"""
        record = ErrorRecord(
            error_code="TEST-001",
            error_type="TestError",
            message="测试错误消息",
            operation="test_operation",
            file_path="/path/to/file",
        )

        self.assertFalse(record.resolved)
        record.mark_as_resolved()
        self.assertTrue(record.resolved)


class ErrorLoggerTests(unittest.TestCase):
    """ErrorLogger类的测试。"""

    def setUp(self):
        """测试前准备。"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = os.path.join(self.temp_dir, "logs")
        self.logger = ErrorLogger(log_dir=self.log_dir)

    def tearDown(self):
        """测试后清理。"""
        shutil.rmtree(self.temp_dir)

    def test_log_error(self):
        """测试记录错误。"""
        record = ErrorRecord(
            error_code="TEST-001",
            error_type="TestError",
            message="测试错误消息",
            operation="test_operation",
            file_path="/path/to/file",
        )

        self.logger.log_error(record)

        # 验证错误被记录
        self.assertEqual(len(self.logger.error_records), 1)
        self.assertEqual(self.logger.error_records[0].error_code, "TEST-001")

        # 验证日志文件被创建
        self.assertTrue(os.path.exists(os.path.join(self.log_dir, "error.log")))

        # 验证JSON文件被创建
        self.assertTrue(os.path.exists(os.path.join(self.log_dir, "errors.json")))

    def test_get_recent_errors(self):
        """测试获取最近的错误。"""
        # 添加5个错误记录
        for i in range(5):
            record = ErrorRecord(
                error_code=f"TEST-{i:03d}",
                error_type="TestError",
                message=f"测试错误消息 {i}",
                operation="test_operation",
                file_path="/path/to/file",
                timestamp=datetime(2023, 1, 1, 12, i, 0),
            )
            self.logger.log_error(record)

        # 获取最近的3个错误
        recent_errors = self.logger.get_recent_errors(3)

        self.assertEqual(len(recent_errors), 3)
        # 由于是按时间倒序排列，所以最新的在前面
        self.assertEqual(recent_errors[0].error_code, "TEST-004")
        self.assertEqual(recent_errors[1].error_code, "TEST-003")
        self.assertEqual(recent_errors[2].error_code, "TEST-002")


class RecoveryManagerTests(unittest.TestCase):
    """RecoveryManager类的测试。"""

    def setUp(self):
        """测试前准备。"""
        self.temp_dir = tempfile.mkdtemp()
        self.backup_dir = os.path.join(self.temp_dir, "backups")
        self.test_file_path = os.path.join(self.temp_dir, "test_file.txt")

        # 创建测试文件
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write("测试内容")

        self.recovery_manager = RecoveryManager(backup_dir=self.backup_dir)

    def tearDown(self):
        """测试后清理。"""
        shutil.rmtree(self.temp_dir)

    def test_create_backup(self):
        """测试创建备份。"""
        backup_path = self.recovery_manager.create_backup(self.test_file_path)

        # 验证备份文件存在
        self.assertIsNotNone(backup_path)
        self.assertTrue(os.path.exists(backup_path))

        # 验证备份文件内容正确
        with open(backup_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertEqual(content, "测试内容")

    def test_restore_from_backup(self):
        """测试从备份恢复。"""
        # 创建备份
        backup_path = self.recovery_manager.create_backup(self.test_file_path)

        # 删除原文件并创建新内容
        os.remove(self.test_file_path)
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write("新内容")

        # 从备份恢复
        result = self.recovery_manager.restore_from_backup(backup_path, self.test_file_path)

        # 验证恢复成功
        self.assertTrue(result)

        # 验证文件内容被恢复
        with open(self.test_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertEqual(content, "测试内容")

    def test_find_latest_backup(self):
        """测试查找最新的备份。"""
        # 创建第一个备份
        self.recovery_manager.create_backup(self.test_file_path)

        # 修改文件并创建第二个备份
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write("新内容")
        backup_path = self.recovery_manager.create_backup(self.test_file_path)

        # 查找最新的备份
        latest_backup = self.recovery_manager.find_latest_backup(
            os.path.basename(self.test_file_path)
        )

        # 验证找到了最新的备份
        self.assertIsNotNone(latest_backup)
        self.assertTrue(os.path.exists(latest_backup))

        # 验证备份文件内容正确
        with open(latest_backup, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertEqual(content, "新内容")


class RetryOperationTests(unittest.TestCase):
    """retry_operation函数的测试。"""

    def test_retry_operation_success(self):
        """测试重试成功的情况。"""
        # 模拟函数，第一次调用抛出异常，第二次成功
        mock_func = MagicMock(side_effect=[ValueError("测试异常"), "成功"])

        result = retry_operation(mock_func, max_attempts=3, delay=0.1)

        # 验证结果
        self.assertEqual(result, "成功")
        # 验证函数被调用了两次
        self.assertEqual(mock_func.call_count, 2)

    def test_retry_operation_max_attempts(self):
        """测试达到最大尝试次数的情况。"""
        # 模拟函数，总是抛出异常
        mock_func = MagicMock(side_effect=ValueError("测试异常"))

        # 应该抛出异常
        with self.assertRaises(ValueError):
            retry_operation(mock_func, max_attempts=3, delay=0.1)

        # 验证函数被调用了3次
        self.assertEqual(mock_func.call_count, 3)


class ErrorHandlerTests(unittest.TestCase):
    """ErrorHandler类的测试。"""

    def setUp(self):
        """测试前准备。"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = os.path.join(self.temp_dir, "logs")
        self.backup_dir = os.path.join(self.temp_dir, "backups")
        self.error_handler = ErrorHandler(log_dir=self.log_dir, backup_dir=self.backup_dir)

    def tearDown(self):
        """测试后清理。"""
        shutil.rmtree(self.temp_dir)

    def test_handle_error(self):
        """测试处理错误。"""
        # 创建异常
        exception = FileNotFoundError("测试文件未找到")

        # 处理错误
        result = self.error_handler.handle_error(
            exception=exception, operation="test_operation", file_path="/path/to/file"
        )

        # 验证结果
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_record)
        self.assertEqual(result.error_record.error_type, "FileNotFoundError")
        self.assertEqual(result.error_record.message, "测试文件未找到")

        # 验证建议
        self.assertTrue(len(result.suggestions) > 0)

    def test_generate_error_code(self):
        """测试生成错误代码。"""
        # 不同类型的异常
        exceptions = [
            FileNotFoundError("文件未找到"),
            DirectoryNotFoundError("目录未找到"),
            FileExistsError("文件已存在"),
            Exception("通用异常"),
        ]

        codes = [self.error_handler._generate_error_code(e) for e in exceptions]

        # 验证错误代码格式正确
        self.assertTrue(codes[0].startswith("FNF-"))
        self.assertTrue(codes[1].startswith("DNF-"))
        self.assertTrue(codes[2].startswith("FEX-"))
        self.assertTrue(codes[3].startswith("GEN-"))

        # 验证错误计数递增
        self.assertEqual(int(codes[0].split("-")[1]), 1)
        self.assertEqual(int(codes[1].split("-")[1]), 2)
        self.assertEqual(int(codes[2].split("-")[1]), 3)
        self.assertEqual(int(codes[3].split("-")[1]), 4)


class FileOperationErrorHandlerTests(unittest.TestCase):
    """FileOperationErrorHandler类的测试。"""

    def setUp(self):
        """测试前准备。"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = os.path.join(self.temp_dir, "logs")
        self.backup_dir = os.path.join(self.temp_dir, "backups")
        self.test_file_path = os.path.join(self.temp_dir, "test_file.txt")

        # 创建测试文件
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write("测试内容")

        self.error_handler = FileOperationErrorHandler(
            log_dir=self.log_dir, backup_dir=self.backup_dir
        )

    def tearDown(self):
        """测试后清理。"""
        shutil.rmtree(self.temp_dir)

    def test_handle_directory_not_found(self):
        """测试处理目录未找到错误。"""
        # 创建异常
        exception = DirectoryNotFoundError("测试目录未找到")

        # 处理错误
        non_existent_dir = os.path.join(self.temp_dir, "non_existent")
        non_existent_file = os.path.join(non_existent_dir, "test.txt")

        # 直接调用_attempt_recovery进行测试，因为handle_error方法依赖_should_attempt_recovery
        error_record = ErrorRecord(
            error_code="DNF-001",
            error_type="DirectoryNotFoundError",
            message="测试目录未找到",
            operation="test_operation",
            file_path=non_existent_file,
        )

        result = self.error_handler._attempt_recovery(error_record)

        # 验证结果
        self.assertTrue(result)
        # 验证目录已创建
        self.assertTrue(os.path.exists(non_existent_dir))

    def test_handle_file_exists_error(self):
        """测试处理文件已存在错误。"""
        # 创建异常
        exception = FileExistsError("测试文件已存在")

        # 处理错误
        result = self.error_handler.handle_error(
            exception=exception, operation="test_operation", file_path=self.test_file_path
        )

        # 验证结果
        self.assertTrue(result.recovery_attempted)
        # 验证已创建备份
        backups = os.listdir(self.backup_dir)
        self.assertTrue(len(backups) > 0)


class WithErrorHandlingTests(unittest.TestCase):
    """with_error_handling装饰器的测试。"""

    def setUp(self):
        """测试前准备。"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = os.path.join(self.temp_dir, "logs")
        self.backup_dir = os.path.join(self.temp_dir, "backups")

    def tearDown(self):
        """测试后清理。"""
        shutil.rmtree(self.temp_dir)

    def test_with_error_handling(self):
        """测试错误处理装饰器。"""
        log_dir = self.log_dir
        backup_dir = self.backup_dir

        # 创建一个测试类
        class TestClass:
            def __init__(self):
                self.error_handler = FileOperationErrorHandler(
                    log_dir=log_dir, backup_dir=backup_dir
                )
                self.call_count = 0

            @with_error_handling("test_operation")
            def test_method(self, file_path):
                self.call_count += 1
                if self.call_count == 1:
                    raise FileNotFoundError("测试文件未找到")
                return "成功"

        # 创建测试实例
        test_instance = TestClass()

        # 第一次调用应该抛出异常
        with self.assertRaises(FileNotFoundError):
            test_instance.test_method("/path/to/file")

        # 验证方法被调用了1次
        self.assertEqual(test_instance.call_count, 1)


if __name__ == "__main__":
    unittest.main()
