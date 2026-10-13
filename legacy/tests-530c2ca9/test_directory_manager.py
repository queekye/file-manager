#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DirectoryManager类的单元测试。
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.core.directory_manager import DirectoryManager, DirectoryTemplate
from src.core.exceptions import DirectoryCreationError, DirectoryNotFoundError


class TestDirectoryTemplate(unittest.TestCase):
    """测试DirectoryTemplate类的功能。"""

    def test_init(self):
        """测试DirectoryTemplate初始化。"""
        template_string = "{person}/{type}/files"
        template = DirectoryTemplate(template_string)
        self.assertEqual(template_string, template.template_string)

    def test_render(self):
        """测试模板渲染功能。"""
        template = DirectoryTemplate("{person}/{type}/files")
        result = template.render(person="zhang", type="id")
        self.assertEqual("zhang/id/files", result)

        # 测试复杂模板
        template = DirectoryTemplate("{base}/{person}/{type}_{year}")
        result = template.render(base="/data", person="zhang", type="id", year=2023)
        self.assertEqual("/data/zhang/id_2023", result)

    def test_render_missing_param(self):
        """测试缺少参数时的错误处理。"""
        template = DirectoryTemplate("{person}/{type}")
        with self.assertRaises(KeyError):
            template.render(person="zhang")  # 缺少type参数


class TestDirectoryManager(unittest.TestCase):
    """测试DirectoryManager类的功能。"""

    def setUp(self):
        """测试前创建临时目录。"""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_config = MagicMock()
        self.mock_config.options = {"directory_template": "{person}/{type}"}
        self.mock_config.file_types = [
            {"id": "id", "name": "身份证", "directory": "ID_Cards"},
            {"id": "contract", "name": "合同", "directory": "Contracts"},
        ]
        self.mock_config.get_all_persons = MagicMock(
            return_value=[
                {"id": "001", "name": "张三", "directory": "zhangsan"},
                {"id": "002", "name": "李四", "directory": "lisi"},
            ]
        )

        self.directory_manager = DirectoryManager(self.temp_dir, self.mock_config)

    def tearDown(self):
        """测试后删除临时目录。"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """测试DirectoryManager初始化。"""
        self.assertEqual(Path(self.temp_dir), self.directory_manager.base_directory)
        self.assertEqual(self.mock_config, self.directory_manager.config)
        self.assertEqual(260, self.directory_manager.MAX_PATH_LENGTH)

    def test_ensure_directory(self):
        """测试确保目录存在功能。"""
        test_dir = os.path.join(self.temp_dir, "test_dir")

        # 测试创建新目录
        result = self.directory_manager.ensure_directory(test_dir)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(test_dir))
        self.assertTrue(os.path.isdir(test_dir))

        # 测试已存在的目录
        result = self.directory_manager.ensure_directory(test_dir)
        self.assertTrue(result)

    def test_ensure_directory_error(self):
        """测试确保目录存在时的错误处理。"""
        # 创建一个文件
        test_file = os.path.join(self.temp_dir, "test_file")
        with open(test_file, "w") as f:
            f.write("test")

        # 尝试将文件作为目录确保存在，应该抛出异常
        with self.assertRaises(DirectoryCreationError):
            self.directory_manager.ensure_directory(test_file)

    def test_get_target_path(self):
        """测试获取目标路径功能。"""
        person_dir = "test_person"
        file_type_dir = "test_type"

        expected_path = Path(self.temp_dir) / person_dir / file_type_dir
        result_path = self.directory_manager.get_target_path(person_dir, file_type_dir)

        self.assertEqual(expected_path, result_path)
        self.assertTrue(os.path.exists(str(result_path)))
        self.assertTrue(os.path.isdir(str(result_path)))

        # 测试使用字典参数
        person_dict = {"directory": "dict_person"}
        file_type_dict = {"directory": "dict_type"}

        expected_path = Path(self.temp_dir) / "dict_person" / "dict_type"
        result_path = self.directory_manager.get_target_path(person_dict, file_type_dict)

        self.assertEqual(expected_path, result_path)
        self.assertTrue(os.path.exists(str(result_path)))
        self.assertTrue(os.path.isdir(str(result_path)))

    def test_directory_exists(self):
        """测试目录存在检查功能。"""
        test_dir = os.path.join(self.temp_dir, "test_exists")

        # 测试不存在的目录
        self.assertFalse(self.directory_manager.directory_exists(test_dir))

        # 创建目录并测试
        os.mkdir(test_dir)
        self.assertTrue(self.directory_manager.directory_exists(test_dir))

        # 测试存在但是文件的情况
        test_file = os.path.join(self.temp_dir, "test_file")
        with open(test_file, "w") as f:
            f.write("test")
        self.assertFalse(self.directory_manager.directory_exists(test_file))

    def test_list_subdirectories(self):
        """测试列出子目录功能。"""
        # 创建测试目录结构
        dirs = ["dir1", "dir2", "dir3"]
        for d in dirs:
            os.mkdir(os.path.join(self.temp_dir, d))

        # 创建一个文件，确保它不会被列为目录
        with open(os.path.join(self.temp_dir, "test_file"), "w") as f:
            f.write("test")

        # 测试列出子目录
        result = self.directory_manager.list_subdirectories()
        self.assertEqual(set(dirs), set(result))

        # 测试不存在的目录
        with self.assertRaises(DirectoryNotFoundError):
            self.directory_manager.list_subdirectories("non_existent_dir")

    def test_get_person_file_type_directories(self):
        """测试获取人员文件类型目录功能。"""
        # 创建测试目录结构
        person_dir = "test_person"
        file_types = ["type1", "type2", "type3"]

        os.mkdir(os.path.join(self.temp_dir, person_dir))
        for ft in file_types:
            os.mkdir(os.path.join(self.temp_dir, person_dir, ft))

        # 创建一个文件，确保它不会被列为目录
        with open(os.path.join(self.temp_dir, person_dir, "test_file"), "w") as f:
            f.write("test")

        # 测试获取文件类型目录
        result = self.directory_manager.get_person_file_type_directories(person_dir)
        self.assertEqual(set(file_types), set(result))

        # 测试不存在的人员目录
        with self.assertRaises(DirectoryNotFoundError):
            self.directory_manager.get_person_file_type_directories("non_existent_person")

    def test_ensure_directory_structure(self):
        """测试确保目录结构存在功能。"""
        person = {"name": "张三", "directory": "zhangsan", "id": "001"}
        file_type = {"name": "身份证", "directory": "ID_Cards", "id": "id"}

        # 测试创建目录结构
        result_path = self.directory_manager.ensure_directory_structure(person, file_type)
        expected_path = str(Path(self.temp_dir) / "zhangsan" / "ID_Cards")

        self.assertEqual(expected_path, result_path)
        self.assertTrue(os.path.exists(result_path))
        self.assertTrue(os.path.isdir(result_path))

        # 测试不提供文件类型
        result_path = self.directory_manager.ensure_directory_structure(person)
        expected_path = str(Path(self.temp_dir) / "zhangsan" / "")

        self.assertEqual(expected_path, result_path)
        self.assertTrue(os.path.exists(result_path))
        self.assertTrue(os.path.isdir(result_path))

    def test_create_directory_from_template(self):
        """测试从模板创建目录结构功能。"""
        # 测试简单模板
        template = "{person}/{type}"
        result_path = self.directory_manager.create_directory_from_template(
            template, person="zhangsan", type="ID_Cards"
        )
        expected_path = str(Path(self.temp_dir) / "zhangsan" / "ID_Cards")

        self.assertEqual(expected_path, result_path)
        self.assertTrue(os.path.exists(result_path))
        self.assertTrue(os.path.isdir(result_path))

        # 测试复杂模板
        template = "{person}/{year}/{type}"
        result_path = self.directory_manager.create_directory_from_template(
            template, person="lisi", year=2023, type="Contracts"
        )
        expected_path = str(Path(self.temp_dir) / "lisi" / "2023" / "Contracts")

        self.assertEqual(expected_path, result_path)
        self.assertTrue(os.path.exists(result_path))
        self.assertTrue(os.path.isdir(result_path))

        # 测试缺少参数
        with self.assertRaises(DirectoryCreationError):
            self.directory_manager.create_directory_from_template(
                template, person="wangwu"  # 缺少year和type参数
            )

    def test_validate_directory_structure(self):
        """测试验证目录结构功能。"""
        # 创建基本目录结构
        os.makedirs(os.path.join(self.temp_dir, "zhangsan", "ID_Cards"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "zhangsan", "Contracts"), exist_ok=True)
        # 故意不创建lisi的目录，测试检测缺失目录

        # 执行验证
        issues = self.directory_manager.validate_directory_structure()

        # 应该检测到两个问题：lisi目录不存在，lisi下的文件类型目录不存在
        self.assertTrue(
            any(issue["type"] == "missing" and "lisi" in issue["path"] for issue in issues)
        )

        # 创建缺失的目录
        os.makedirs(os.path.join(self.temp_dir, "lisi", "ID_Cards"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "lisi", "Contracts"), exist_ok=True)

        # 再次执行验证，应该没有问题了
        issues = self.directory_manager.validate_directory_structure()
        missing_issues = [issue for issue in issues if issue["type"] == "missing"]
        self.assertEqual(0, len(missing_issues))

    def test_repair_directory_structure(self):
        """测试修复目录结构功能。"""
        # 准备要修复的问题列表
        issues = [
            {
                "type": "missing",
                "path": os.path.join(self.temp_dir, "repair_test", "ID_Cards"),
                "description": "测试缺失目录",
            }
        ]

        # 执行修复
        results = self.directory_manager.repair_directory_structure(issues)

        # 验证修复结果
        self.assertEqual(1, results["success"])
        self.assertEqual(0, results["failed"])
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "repair_test", "ID_Cards")))

    @patch("os.access")
    def test_check_directory_permissions(self, mock_access):
        """测试检查目录权限功能。"""
        # 模拟目录权限
        test_dir = os.path.join(self.temp_dir, "perm_test")
        os.makedirs(test_dir, exist_ok=True)

        # 模拟权限充足
        mock_access.return_value = True
        self.assertTrue(self.directory_manager._check_directory_permissions(Path(test_dir)))

        # 模拟权限不足
        mock_access.return_value = False
        self.assertFalse(self.directory_manager._check_directory_permissions(Path(test_dir)))

    def test_resolve_conflict(self):
        """测试解决目录名冲突功能。"""
        # 创建一个已存在的目录
        test_dir = os.path.join(self.temp_dir, "conflict_test")
        os.makedirs(test_dir, exist_ok=True)

        # 解决冲突
        resolved_path = self.directory_manager._resolve_conflict(Path(test_dir))

        # 验证结果
        self.assertEqual(str(Path(self.temp_dir) / "conflict_test_1"), str(resolved_path))
        self.assertFalse(os.path.exists(str(resolved_path)))

        # 创建解决冲突后的目录，再次测试
        os.makedirs(str(resolved_path), exist_ok=True)
        resolved_path2 = self.directory_manager._resolve_conflict(Path(test_dir))

        # 验证结果
        self.assertEqual(str(Path(self.temp_dir) / "conflict_test_2"), str(resolved_path2))
        self.assertFalse(os.path.exists(str(resolved_path2)))

    def test_transaction_operations(self):
        """测试事务操作功能。"""
        # 记录一些操作
        self.directory_manager._log_operation("create", "/test/path1")
        self.directory_manager._log_operation("create", "/test/path2")

        # 验证日志记录
        self.assertEqual(2, len(self.directory_manager._operation_log))

        # 提交事务，应清空日志
        self.directory_manager._commit_transaction()
        self.assertEqual(0, len(self.directory_manager._operation_log))

        # 开始新事务
        self.directory_manager._begin_transaction()
        self.assertEqual(0, len(self.directory_manager._operation_log))

        # 记录新操作
        self.directory_manager._log_operation("create", "/test/path3")
        self.assertEqual(1, len(self.directory_manager._operation_log))

        # 回滚事务，应清空日志
        self.directory_manager._rollback_transaction()
        self.assertEqual(0, len(self.directory_manager._operation_log))


if __name__ == "__main__":
    unittest.main()
