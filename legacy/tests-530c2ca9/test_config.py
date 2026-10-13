#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置管理模块单元测试。
"""

import json
import os
import tempfile
import unittest

import yaml

from src.core.config import Config, PersonManager
from src.core.exceptions import ConfigurationError


class TestConfig(unittest.TestCase):
    """配置管理类测试用例。"""

    def setUp(self):
        """每个测试前准备环境。"""
        # 创建临时测试目录
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_path = self.test_dir.name

        # 创建测试配置文件路径
        self.config_path = os.path.join(self.test_path, "config.yaml")

        # 创建测试配置内容
        self.test_config = {
            "base_directory": os.path.join(self.test_path, "files"),
            "naming_pattern": "{person}_{type}_{date}_{original_filename}",
            "options": {
                "copy_files": True,
                "create_directories": True,
                "directory_template": "{person}/{type}",
                "auto_rename_duplicates": True,
                "preserve_timestamps": True,
            },
            "file_types": [
                {"id": "test", "name": "测试", "directory": "Tests", "description": "测试文件类型"}
            ],
        }

    def tearDown(self):
        """每个测试后清理环境。"""
        # 清理临时目录
        self.test_dir.cleanup()

    def test_init_with_existing_config(self):
        """测试使用已存在的配置文件初始化。"""
        # 创建配置文件
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(self.test_config, f, allow_unicode=True)

        # 初始化配置对象
        config = Config(config_path=self.config_path)

        # 验证配置已正确加载
        self.assertEqual(config.base_directory, self.test_config["base_directory"])
        self.assertEqual(config.naming_pattern, self.test_config["naming_pattern"])
        self.assertEqual(config.options, self.test_config["options"])
        self.assertEqual(config.file_types, self.test_config["file_types"])

    def test_init_without_existing_config(self):
        """测试在配置文件不存在时初始化。"""
        # 确保配置文件不存在
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

        # 初始化配置对象
        config = Config(config_path=self.config_path)

        # 验证配置已从默认配置创建
        self.assertTrue(os.path.exists(self.config_path))
        self.assertEqual(config.base_directory, "D:/PersonnelFiles")
        self.assertEqual(len(config.person_fields), 1)
        self.assertEqual(config.person_fields[0]["id"], "contact")
        self.assertEqual(len(config.file_types), 1)
        self.assertEqual(config.file_types[0]["id"], "photo")

    def test_load_invalid_config(self):
        """测试加载格式不正确的配置文件。"""
        # 创建无效的配置文件
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write("invalid: yaml: content: - not properly formatted")

        # 尝试加载应抛出异常
        with self.assertRaises(ConfigurationError):
            Config(config_path=self.config_path)

    def test_load_missing_required_fields(self):
        """测试加载缺少必要字段的配置文件。"""
        # 创建缺少必要字段的配置文件
        invalid_config = {"options": {"copy_files": True}}
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(invalid_config, f)

        # 尝试加载应抛出异常
        with self.assertRaises(ConfigurationError):
            Config(config_path=self.config_path)

    def test_save_config(self):
        """测试保存配置文件。"""
        # 初始化配置对象
        config = Config(config_path=self.config_path)

        # 修改配置
        config.base_directory = "/new/path"
        config.naming_pattern = "{new_pattern}"
        config.options = {"new_option": True}
        config.file_types = [{"id": "new", "name": "新类型", "directory": "New"}]

        # 保存配置
        config.save()

        # 重新加载配置验证保存是否成功
        new_config = Config(config_path=self.config_path)
        self.assertEqual(new_config.base_directory, "/new/path")
        self.assertEqual(new_config.naming_pattern, "{new_pattern}")
        self.assertEqual(
            new_config.options, {"new_option": True, "directory_template": "{person}/{type}"}
        )
        self.assertEqual(new_config.file_types[0]["id"], "new")

    def test_validate_valid_config(self):
        """测试验证有效配置。"""
        config = Config(config_path=self.config_path)
        self.assertTrue(config.validate())

    def test_validate_invalid_config(self):
        """测试验证无效配置。"""
        config = Config(config_path=self.config_path)

        # 设置无效配置
        config.base_directory = ""
        self.assertFalse(config.validate())

        config.base_directory = "/valid/path"
        config.naming_pattern = ""
        self.assertFalse(config.validate())

        config.naming_pattern = "{valid}"
        config.file_types = [{"name": "缺少ID", "directory": "Missing"}]
        self.assertFalse(config.validate())

    def test_get_file_type(self):
        """测试获取文件类型定义。"""
        config = Config(config_path=self.config_path)

        # 测试获取存在的文件类型
        file_type = config.get_file_type("test")
        self.assertIsNotNone(file_type)
        self.assertEqual(file_type["name"], "测试")

        # 测试获取不存在的文件类型
        file_type = config.get_file_type("nonexistent")
        self.assertIsNone(file_type)

    def test_add_file_type(self):
        """测试添加文件类型定义。"""
        config = Config(config_path=self.config_path)

        # 测试添加有效文件类型
        new_type = {"id": "new", "name": "新类型", "directory": "New"}
        result = config.add_file_type(new_type)
        self.assertTrue(result)

        # 验证文件类型已添加
        file_type = config.get_file_type("new")
        self.assertIsNotNone(file_type)
        self.assertEqual(file_type["name"], "新类型")

        # 测试添加ID重复的文件类型
        duplicate_type = {"id": "new", "name": "重复", "directory": "Duplicate"}
        with self.assertRaises(ConfigurationError):
            config.add_file_type(duplicate_type)

        # 测试添加缺少必要字段的文件类型
        invalid_type = {"id": "invalid", "name": "无效"}
        with self.assertRaises(ConfigurationError):
            config.add_file_type(invalid_type)

    def test_delete_file_type(self):
        """测试删除文件类型定义。"""
        config = Config(config_path=self.config_path)

        # 测试删除存在的文件类型
        result = config.delete_file_type("test")
        self.assertTrue(result)
        self.assertIsNone(config.get_file_type("test"))

        # 测试删除不存在的文件类型
        result = config.delete_file_type("nonexistent")
        self.assertFalse(result)

    def test_update_file_type(self):
        """测试更新文件类型定义。"""
        config = Config(config_path=self.config_path)

        # 测试更新存在的文件类型
        new_data = {"name": "已更新"}
        result = config.update_file_type("test", new_data)
        self.assertTrue(result)

        # 验证更新是否成功
        file_type = config.get_file_type("test")
        self.assertEqual(file_type["name"], "已更新")

        # 测试更新不存在的文件类型
        result = config.update_file_type("nonexistent", {"name": "不存在"})
        self.assertFalse(result)

        # 测试尝试更改ID
        result = config.update_file_type("test", {"id": "new_id"})
        self.assertTrue(result)
        # ID不应被更改
        self.assertIsNotNone(config.get_file_type("test"))
        self.assertIsNone(config.get_file_type("new_id"))

    def test_validate_config_data(self):
        """测试配置数据验证方法。"""
        config = Config(config_path=self.config_path)

        # 测试有效配置
        valid_data = {
            "base_directory": "/valid/path",
            "naming_pattern": "{valid_pattern}",
            "options": {"copy_files": True, "directory_template": "{person}/{type}"},
            "file_types": [],
        }
        self.assertTrue(config._validate_config_data(valid_data))

        # 测试缺少基本目录
        invalid_data1 = {"naming_pattern": "{valid_pattern}", "options": {}, "file_types": []}
        self.assertFalse(config._validate_config_data(invalid_data1))

        # 测试缺少命名模式
        invalid_data2 = {"base_directory": "/valid/path", "options": {}, "file_types": []}
        self.assertFalse(config._validate_config_data(invalid_data2))

        # 测试options不是字典
        invalid_data3 = {
            "base_directory": "/valid/path",
            "naming_pattern": "{valid_pattern}",
            "options": "not_a_dict",
            "file_types": [],
        }
        self.assertFalse(config._validate_config_data(invalid_data3))

        # 测试file_types不是列表
        invalid_data4 = {
            "base_directory": "/valid/path",
            "naming_pattern": "{valid_pattern}",
            "options": {},
            "file_types": "not_a_list",
        }
        self.assertFalse(config._validate_config_data(invalid_data4))

        # 测试自动添加默认目录模板
        data_without_template = {
            "base_directory": "/valid/path",
            "naming_pattern": "{valid_pattern}",
            "options": {},
            "file_types": [],
        }
        self.assertTrue(config._validate_config_data(data_without_template))
        self.assertEqual("{person}/{type}", data_without_template["options"]["directory_template"])

    def test_default_options(self):
        """测试默认选项设置。"""
        # 创建带有最小选项的配置
        minimal_config = {
            "base_directory": os.path.join(self.test_path, "files"),
            "naming_pattern": "{person}_{type}_{original_filename}",
            "options": {},
            "file_types": [],
        }

        # 保存配置文件
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(minimal_config, f, allow_unicode=True)

        # 加载配置
        config = Config(config_path=self.config_path)

        # 验证默认选项
        self.assertEqual("{person}/{type}", config.options.get("directory_template"))
        self.assertFalse(config.options.get("copy_files", False))
        self.assertFalse(config.options.get("create_directories", False))

    def test_multi_directory_support(self):
        """测试多目录支持功能。"""
        # 创建测试配置
        test_config = {
            "base_directories": [
                os.path.join(self.test_path, "files1"),
                os.path.join(self.test_path, "files2"),
            ],
            "current_base_directory": os.path.join(self.test_path, "files1"),
            "naming_pattern": "{person}_{type}_{date}",
            "options": {},
            "file_types": [],
        }

        # 保存测试配置
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(test_config, f)

        # 加载配置
        config = Config(config_path=self.config_path)

        # 验证目录列表
        self.assertEqual(len(config.base_directories), 2)
        self.assertEqual(config.base_directories[0], os.path.join(self.test_path, "files1"))
        self.assertEqual(config.base_directories[1], os.path.join(self.test_path, "files2"))

        # 验证当前目录
        self.assertEqual(config.current_base_directory, os.path.join(self.test_path, "files1"))

        # 测试添加新目录
        new_dir = os.path.join(self.test_path, "files3")
        self.assertTrue(config.add_base_directory(new_dir))
        self.assertEqual(len(config.base_directories), 3)
        self.assertIn(new_dir, config.base_directories)

        # 测试重复添加目录
        self.assertFalse(config.add_base_directory(new_dir))
        self.assertEqual(len(config.base_directories), 3)

        # 测试切换当前目录
        self.assertTrue(config.set_base_directory(os.path.join(self.test_path, "files2")))
        self.assertEqual(config.current_base_directory, os.path.join(self.test_path, "files2"))

        # 测试切换到不存在的目录
        self.assertFalse(config.set_base_directory(os.path.join(self.test_path, "nonexistent")))
        self.assertEqual(config.current_base_directory, os.path.join(self.test_path, "files2"))

        # 测试移除目录
        self.assertTrue(config.remove_base_directory(new_dir))
        self.assertEqual(len(config.base_directories), 2)
        self.assertNotIn(new_dir, config.base_directories)

        # 测试移除当前目录
        current_dir = config.current_base_directory
        self.assertTrue(config.remove_base_directory(current_dir))
        self.assertNotEqual(config.current_base_directory, current_dir)
        self.assertEqual(len(config.base_directories), 1)

        # 测试移除最后一个目录
        last_dir = config.base_directories[0]
        self.assertFalse(config.remove_base_directory(last_dir))
        self.assertEqual(len(config.base_directories), 1)
        self.assertEqual(config.current_base_directory, last_dir)

    def test_directory_manager_with_config(self):
        """测试目录管理器与配置对象的集成。"""
        from src.core.directory_manager import DirectoryManager

        # 创建测试配置
        test_config = {
            "base_directories": [
                os.path.join(self.test_path, "files1"),
                os.path.join(self.test_path, "files2"),
            ],
            "current_base_directory": os.path.join(self.test_path, "files1"),
            "naming_pattern": "{person}_{type}_{date}",
            "options": {},
            "file_types": [],
        }

        # 保存测试配置
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(test_config, f)

        # 加载配置
        config = Config(config_path=self.config_path)

        # 创建目录管理器
        manager = DirectoryManager(config.get_base_directory(), config=config)

        # 验证初始目录
        self.assertEqual(str(manager.base_directory), os.path.join(self.test_path, "files1"))

        # 切换当前目录
        config.set_base_directory(os.path.join(self.test_path, "files2"))
        manager.update_base_directory()

        # 验证目录已更新
        self.assertEqual(str(manager.base_directory), os.path.join(self.test_path, "files2"))


class TestPersonManager(unittest.TestCase):
    """人员管理类测试用例。"""

    def setUp(self):
        """每个测试前准备环境。"""
        # 创建临时测试目录
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_path = self.test_dir.name

        # 创建测试人员数据文件路径
        self.persons_path = os.path.join(self.test_path, "persons.json")
        self.default_persons_path = os.path.join(self.test_path, "default_persons.json")

        # 创建测试人员数据内容
        self.test_persons = {
            "persons": [
                {
                    "id": "001",
                    "name": "测试人员1",
                    "directory": "test1",
                    "created_at": "2023-01-01T00:00:00",
                    "last_modified": "2023-01-01T00:00:00",
                    "department": "测试部门",
                    "position": "测试职位",
                    "contact": "13800138000",
                }
            ],
            "last_id": 1,
        }

        # 创建默认人员数据文件
        os.makedirs(os.path.dirname(self.default_persons_path), exist_ok=True)
        with open(self.default_persons_path, "w", encoding="utf-8") as f:
            json.dump(self.test_persons, f, ensure_ascii=False)

    def tearDown(self):
        """每个测试后清理环境。"""
        # 清理临时目录
        self.test_dir.cleanup()

    def test_init_with_existing_persons(self):
        """测试使用已存在的人员数据文件初始化。"""
        # 创建人员数据文件
        with open(self.persons_path, "w", encoding="utf-8") as f:
            json.dump(self.test_persons, f, ensure_ascii=False)

        # 初始化人员管理对象
        person_manager = PersonManager(
            persons_path=self.persons_path, default_persons_path=self.default_persons_path
        )

        # 验证人员数据已正确加载
        self.assertEqual(len(person_manager.get_all_persons()), 1)
        self.assertEqual(person_manager.get_all_persons()[0]["name"], "测试人员1")
        self.assertEqual(person_manager.last_id, 1)

    def test_init_without_existing_persons(self):
        """测试在人员数据文件不存在时初始化。"""
        # 确保人员数据文件不存在
        if os.path.exists(self.persons_path):
            os.remove(self.persons_path)

        # 初始化人员管理对象
        person_manager = PersonManager(
            persons_path=self.persons_path, default_persons_path=self.default_persons_path
        )

        # 验证人员数据已从默认数据创建
        self.assertEqual(len(person_manager.get_all_persons()), 1)
        self.assertEqual(person_manager.get_all_persons()[0]["name"], "测试人员1")
        self.assertEqual(person_manager.last_id, 1)

        # 验证人员数据文件已创建
        self.assertTrue(os.path.exists(self.persons_path))

    def test_get_person(self):
        """测试根据ID获取人员。"""
        person_manager = PersonManager(
            persons_path=self.persons_path, default_persons_path=self.default_persons_path
        )

        # 测试获取存在的人员
        person = person_manager.get_person("001")
        self.assertIsNotNone(person)
        self.assertEqual(person["name"], "测试人员1")

        # 测试获取不存在的人员
        person = person_manager.get_person("999")
        self.assertIsNone(person)

    def test_get_person_by_name(self):
        """测试根据姓名获取人员。"""
        person_manager = PersonManager(
            persons_path=self.persons_path, default_persons_path=self.default_persons_path
        )

        # 测试获取存在的人员
        person = person_manager.get_person_by_name("测试人员1")
        self.assertIsNotNone(person)
        self.assertEqual(person["id"], "001")

        # 测试获取不存在的人员
        person = person_manager.get_person_by_name("不存在")
        self.assertIsNone(person)

    def test_get_person_by_directory(self):
        """测试根据目录名获取人员。"""
        person_manager = PersonManager(
            persons_path=self.persons_path, default_persons_path=self.default_persons_path
        )

        # 测试获取存在的人员
        person = person_manager.get_person_by_directory("test1")
        self.assertIsNotNone(person)
        self.assertEqual(person["name"], "测试人员1")

        # 测试获取不存在的人员
        person = person_manager.get_person_by_directory("nonexistent")
        self.assertIsNone(person)

    def test_add_person(self):
        """测试添加新人员。"""
        person_manager = PersonManager(
            persons_path=self.persons_path, default_persons_path=self.default_persons_path
        )

        # 测试添加新人员
        person = person_manager.add_person("李四", "lisi")
        self.assertEqual(person["name"], "李四")
        self.assertEqual(person["directory"], "lisi")
        self.assertEqual(person["id"], "002")

        # 验证人员已添加到列表
        self.assertEqual(len(person_manager.get_all_persons()), 2)
        self.assertEqual(person_manager.last_id, 2)

        # 测试添加同名目录的人员
        with self.assertRaises(ConfigurationError):
            person_manager.add_person("王五", "lisi")

        # 测试添加空姓名的人员
        with self.assertRaises(ConfigurationError):
            person_manager.add_person("")

        # 测试自动生成目录名
        person = person_manager.add_person("王五")
        self.assertEqual(person["directory"], "王五")

    def test_update_person(self):
        """测试更新人员信息。"""
        person_manager = PersonManager(
            persons_path=self.persons_path, default_persons_path=self.default_persons_path
        )

        # 测试更新存在的人员
        new_data = {"name": "张三更新"}
        result = person_manager.update_person("001", new_data)
        self.assertTrue(result)

        # 验证更新是否成功
        person = person_manager.get_person("001")
        self.assertEqual(person["name"], "张三更新")

        # 测试更新不存在的人员
        result = person_manager.update_person("999", {"name": "不存在"})
        self.assertFalse(result)

        # 测试尝试更改ID
        result = person_manager.update_person("001", {"id": "999"})
        self.assertTrue(result)
        # ID不应被更改
        self.assertIsNotNone(person_manager.get_person("001"))
        self.assertIsNone(person_manager.get_person("999"))

        # 测试更新目录名与现有人员冲突
        person_manager.add_person("李四", "lisi")
        result = person_manager.update_person("001", {"directory": "lisi"})
        self.assertFalse(result)

    def test_delete_person(self):
        """测试删除人员。"""
        person_manager = PersonManager(
            persons_path=self.persons_path, default_persons_path=self.default_persons_path
        )

        # 测试删除存在的人员
        result = person_manager.delete_person("001")
        self.assertTrue(result)
        self.assertEqual(len(person_manager.get_all_persons()), 0)

        # 测试删除不存在的人员
        result = person_manager.delete_person("999")
        self.assertFalse(result)

    def test_save_persons(self):
        """测试保存人员数据。"""
        person_manager = PersonManager(
            persons_path=self.persons_path, default_persons_path=self.default_persons_path
        )

        # 添加新人员
        person_manager.add_person("李四", "lisi")

        # 保存人员数据
        person_manager.save()

        # 重新加载人员数据验证保存是否成功
        new_person_manager = PersonManager(
            persons_path=self.persons_path, default_persons_path=self.default_persons_path
        )
        self.assertEqual(len(new_person_manager.get_all_persons()), 2)
        self.assertEqual(new_person_manager.last_id, 2)
        self.assertIsNotNone(new_person_manager.get_person_by_name("李四"))


if __name__ == "__main__":
    unittest.main()
