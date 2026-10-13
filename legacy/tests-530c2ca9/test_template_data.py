from datetime import datetime

import pytest

from src.core.template_data import TemplateData


@pytest.fixture
def template_data():
    return TemplateData()


def test_get_template_data_basic(template_data):
    """测试基本模板数据生成"""
    result = template_data.get_template_data()
    now = datetime.now()

    assert result["date"] == now.strftime("%Y-%m-%d")
    assert result["year"] == now.strftime("%Y")
    assert result["month"] == now.strftime("%m")
    assert result["day"] == now.strftime("%d")
    assert result["hour"] == now.strftime("%H")
    assert result["minute"] == now.strftime("%M")
    assert result["second"] == now.strftime("%S")


def test_get_template_data_with_person(template_data):
    """测试包含人员信息的模板数据生成"""
    person = {"name": "张三", "id": "001", "directory": "zhangsan"}
    result = template_data.get_template_data(person=person)

    assert result["person_name"] == "张三"
    assert result["person_id"] == "001"
    assert result["person"] == "zhangsan"
    assert isinstance(result["name_pinyin"], str)
    assert isinstance(result["name_first_letters"], str)


def test_get_template_data_with_file_type(template_data):
    """测试包含文件类型的模板数据生成"""
    file_type = {"name": "发票", "directory": "invoice"}
    result = template_data.get_template_data(file_type=file_type)

    assert result["type"] == "invoice"
    assert result["type_name"] == "发票"


def test_render_template(template_data):
    """测试模板渲染功能"""
    template_string = "{name}/{type}/{date}"
    data = {"name": "zhangsan", "type": "invoice", "date": "2024-03-20"}
    result = template_data.render(template_string, **data)
    assert result == "zhangsan/invoice/2024-03-20"


def test_render_template_missing_param(template_data):
    """测试模板渲染缺少参数的情况"""
    template_string = "{name}/{type}"
    data = {"name": "zhangsan"}
    with pytest.raises(KeyError):
        template_data.render(template_string, **data)


def test_sanitize_directory_name(template_data):
    """测试目录名称清理功能"""
    dirty_name = "test/file*name?<>|"
    result = template_data._sanitize_directory_name(dirty_name)
    assert result == "testfilename"

    # 测试空名称
    empty_name = ""
    result = template_data._sanitize_directory_name(empty_name)
    assert result == "unnamed"


def test_get_pinyin(template_data):
    """测试拼音转换功能"""
    chinese_name = "张三"
    result = template_data._get_pinyin(chinese_name)
    assert isinstance(result, str)
    assert result.isascii()


def test_get_pinyin_first_letters(template_data):
    """测试获取拼音首字母功能"""
    chinese_name = "张三"
    result = template_data._get_pinyin_first_letters(chinese_name)
    assert isinstance(result, str)
    assert result.isascii()
    assert len(result) <= len(chinese_name)
