#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试基于SQLite的PersonManager实现。
"""

import json
import os
import tempfile
import unittest

from src.core.person_manager import PersonManager


class TestPersonManagerSQLite(unittest.TestCase):
    """测试基于SQLite的PersonManager类。"""

    def setUp(self):
        """测试前置设置，创建临时数据库文件。"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test.db")
        self.persons_path = os.path.join(self.temp_dir.name, "persons.json")

        # 创建测试用的JSON数据
        test_data = {
            "persons": [
                {
                    "id": "001",
                    "name": "张三",
                    "directory": "zhangsan",
                    "department": "研发部",
                    "position": "工程师",
                    "contact": "zhangsan@example.com",
                    "created_at": "2023-01-01T09:00:00",
                    "last_modified": "2023-01-01T09:00:00",
                    "custom_field": "自定义字段",
                }
            ],
            "last_id": 1,
        }

        with open(self.persons_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)

        # 初始化PersonManager
        self.person_manager = PersonManager(db_path=self.db_path)

    def tearDown(self):
        """测试后置清理，关闭数据库连接，删除临时文件。"""
        self.person_manager.close()
        self.temp_dir.cleanup()

    def test_add_person(self):
        """测试添加人员。"""
        # 添加新人员
        person = self.person_manager.add_person(
            name="李四",
            directory="lisi",
            department="市场部",
            position="经理",
            contact="lisi@example.com",
            custom_field="自定义值",
        )

        # 验证返回的人员数据
        self.assertEqual(person["name"], "李四")
        self.assertEqual(person["directory"], "lisi")
        self.assertEqual(person["department"], "市场部")
        self.assertEqual(person["position"], "经理")
        self.assertEqual(person["contact"], "lisi@example.com")
        self.assertEqual(person["custom_field"], "自定义值")

        # 验证可以通过ID获取
        retrieved = self.person_manager.get_person(person["id"])
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["name"], "李四")
        self.assertEqual(retrieved["custom_field"], "自定义值")

    def test_get_person_by_name(self):
        """测试通过姓名获取人员。"""
        # 添加测试人员
        self.person_manager.add_person(name="王五", directory="wangwu")

        # 通过姓名获取
        person = self.person_manager.get_person_by_name("王五")

        # 验证
        self.assertIsNotNone(person)
        self.assertEqual(person["name"], "王五")
        self.assertEqual(person["directory"], "wangwu")

    def test_get_person_by_directory(self):
        """测试通过目录名获取人员。"""
        # 添加测试人员
        self.person_manager.add_person(name="赵六", directory="zhaoliu")

        # 通过目录名获取
        person = self.person_manager.get_person_by_directory("zhaoliu")

        # 验证
        self.assertIsNotNone(person)
        self.assertEqual(person["name"], "赵六")
        self.assertEqual(person["directory"], "zhaoliu")

    def test_update_person(self):
        """测试更新人员信息。"""
        # 添加测试人员
        person = self.person_manager.add_person(name="孙七", directory="sunqi")

        # 更新信息
        result = self.person_manager.update_person(
            person["id"], {"name": "孙七改", "department": "财务部", "custom_field": "新的自定义值"}
        )

        # 验证更新结果
        self.assertTrue(result)

        # 获取更新后的人员
        updated = self.person_manager.get_person(person["id"])

        # 验证字段已更新
        self.assertEqual(updated["name"], "孙七改")
        self.assertEqual(updated["department"], "财务部")
        self.assertEqual(updated["custom_field"], "新的自定义值")

        # 验证未更新的字段保持不变
        self.assertEqual(updated["directory"], "sunqi")

    def test_delete_person(self):
        """测试删除人员。"""
        # 添加测试人员
        person = self.person_manager.add_person(name="周八", directory="zhouba")

        # 验证人员已添加
        self.assertIsNotNone(self.person_manager.get_person(person["id"]))

        # 删除人员
        result = self.person_manager.delete_person(person["id"])

        # 验证删除结果
        self.assertTrue(result)

        # 验证人员已删除
        self.assertIsNone(self.person_manager.get_person(person["id"]))

    def test_get_all_persons(self):
        """测试获取所有人员。"""
        # 添加多个测试人员
        self.person_manager.add_person(name="吴九", directory="wujiu")
        self.person_manager.add_person(name="郑十", directory="zhengshi")

        # 获取所有人员
        persons = self.person_manager.get_all_persons()

        # 验证人员数量（注意可能包含其他测试添加的人员）
        self.assertGreaterEqual(len(persons), 2)

        # 验证包含刚添加的人员
        names = [p["name"] for p in persons]
        self.assertIn("吴九", names)
        self.assertIn("郑十", names)

    def test_migrate_from_json(self):
        """测试从JSON迁移数据。"""
        # 创建新的PersonManager实例，确保使用空数据库
        new_db_path = os.path.join(self.temp_dir.name, "migrate_test.db")
        person_manager = PersonManager(db_path=new_db_path)

        # 执行迁移
        success_count, fail_count = person_manager.migrate_from_json(self.persons_path)

        # 验证迁移结果
        self.assertEqual(success_count, 1)
        self.assertEqual(fail_count, 0)

        # 验证数据已迁移
        person = person_manager.get_person("001")
        self.assertIsNotNone(person)
        self.assertEqual(person["name"], "张三")
        self.assertEqual(person["custom_field"], "自定义字段")

        # 关闭连接
        person_manager.close()

    def test_export_to_json(self):
        """测试导出数据到JSON。"""
        # 添加测试人员
        self.person_manager.add_person(
            name="测试导出", directory="export_test", custom_field="导出测试字段"
        )

        # 导出路径
        export_path = os.path.join(self.temp_dir.name, "export_test.json")

        # 执行导出
        result = self.person_manager.export_to_json(export_path)

        # 验证导出结果
        self.assertTrue(result)
        self.assertTrue(os.path.exists(export_path))

        # 读取导出的JSON
        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 验证数据结构
        self.assertIn("persons", data)
        self.assertIn("last_id", data)

        # 验证导出的人员数据
        found = False
        for person in data["persons"]:
            if person["name"] == "测试导出":
                found = True
                self.assertEqual(person["directory"], "export_test")
                self.assertEqual(person["custom_field"], "导出测试字段")
                break

        self.assertTrue(found, "导出的数据中未找到测试人员")


if __name__ == "__main__":
    unittest.main()
