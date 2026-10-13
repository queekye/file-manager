#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Windows集成测试脚本，用于测试Windows右键菜单集成功能。
"""

import logging
import sys

import pytest

from src.windows.command_handler import CommandArgs, CommandProcessor
from src.windows.pywin_handler import PyWinHandler
from src.windows.ui.file_type_selector_qt import FileTypeSelector
from src.windows.ui.person_selector_qt import PersonSelector
from src.windows.ui.search_engine import PersonSearchEngine


@pytest.fixture
def logger():
    """设置并返回测试用的日志器。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)


@pytest.fixture
def pywin_handler(logger):
    """返回PyWinHandler实例"""
    # 获取当前可执行文件路径
    app_path = sys.executable

    # 创建PyWinHandler实例
    return PyWinHandler(app_path, "测试应用", logger)


@pytest.fixture
def command_processor(logger):
    """返回CommandProcessor实例"""
    return CommandProcessor(logger)


@pytest.fixture
def test_persons():
    """返回测试用的人员数据"""
    return [
        {"id": "p001", "name": "张三"},
        {"id": "p002", "name": "李四"},
        {"id": "p003", "name": "王五"},
        {"id": "p004", "name": "赵六"},
        {"id": "p005", "name": "陈七"},
        {"id": "p006", "name": "杨八"},
        {"id": "p007", "name": "周九"},
        {"id": "p008", "name": "吴十"},
        {"id": "p009", "name": "郑十一"},
        {"id": "p010", "name": "钱十二"},
    ]


@pytest.fixture
def test_file_types():
    """返回测试用的文件类型数据"""
    return [
        {"id": "t001", "name": "文档"},
        {"id": "t002", "name": "图片"},
        {"id": "t003", "name": "视频"},
        {"id": "t004", "name": "音频"},
        {"id": "t005", "name": "压缩文件"},
        {"id": "t006", "name": "其他"},
    ]


@pytest.fixture
def search_engine(test_persons):
    """返回PersonSearchEngine实例"""
    return PersonSearchEngine(test_persons)


def test_pywin_handler_logging(pywin_handler):
    """测试PyWinHandler的日志记录功能。"""
    # 测试日志记录
    pywin_handler.log_info("这是一条信息日志")
    pywin_handler.log_error("这是一条错误日志")
    # 由于日志操作不返回值，这里只是确保方法调用不抛出异常
    assert True


def test_pywin_handler_command(pywin_handler):
    """测试PyWinHandler的命令字符串创建功能。"""
    # 测试命令字符串创建
    cmd_str = pywin_handler.create_command_string()
    assert isinstance(cmd_str, str)
    assert len(cmd_str) > 0


def test_command_processor_parse(command_processor, monkeypatch):
    """测试CommandProcessor的参数解析功能。"""
    # 模拟os.path.exists始终返回True
    monkeypatch.setattr("os.path.exists", lambda x: True)

    # 测试参数解析
    test_args = [
        "file1.txt",
        "file2.txt",
        "--person_id",
        "p001",
        "--file_type_id",
        "t001",
        "--operation",
        "move",
        "--show_ui",
        "false",
    ]

    cmd_args = command_processor.parse_args(test_args)
    assert isinstance(cmd_args, CommandArgs)
    assert len(cmd_args.file_paths) == 2
    assert cmd_args.file_paths[0] == "file1.txt"
    assert cmd_args.file_paths[1] == "file2.txt"
    assert cmd_args.person_id == "p001"
    assert cmd_args.file_type_id == "t001"
    assert cmd_args.operation == "move"
    assert cmd_args.show_ui is False


def test_command_processor_to_command_line(command_processor, monkeypatch):
    """测试CommandProcessor的命令行生成功能。"""
    # 模拟os.path.exists始终返回True
    monkeypatch.setattr("os.path.exists", lambda x: True)

    # 创建一个CommandArgs对象
    cmd_args = CommandArgs(
        file_paths=["file1.txt", "file2.txt"],
        person_id="p001",
        file_type_id="t001",
        operation="move",
        show_ui=False,
    )

    # 测试命令行生成
    cmd_line = command_processor.to_command_line(cmd_args)
    assert isinstance(cmd_line, str)
    assert "file1.txt" in cmd_line
    assert "file2.txt" in cmd_line
    assert "--person_id" in cmd_line
    assert "p001" in cmd_line
    assert "--file_type_id" in cmd_line
    assert "t001" in cmd_line
    assert "--operation move" in cmd_line
    assert "--show_ui false" in cmd_line


@pytest.mark.parametrize(
    "query,expected_count",
    [
        ("张三", 1),
        ("zhangsan", 1),
        ("zs", 2),  # 张三和郑十一
        ("z", 4),  # 张三、赵六、周九、郑十一
    ],
)
def test_person_search_engine(search_engine, query, expected_count):
    """测试PersonSearchEngine的搜索功能。"""
    search_results = search_engine.search(query)
    assert len(search_results) == expected_count

    # 验证结果包含查询字符串（对于中文查询）
    if query == "张三":
        assert any(person["name"] == "张三" for person in search_results)


@pytest.mark.skipif(sys.platform != "win32", reason="仅在Windows平台上运行")
@pytest.mark.ui
def test_person_selector(test_persons, logger, monkeypatch):
    """测试人员选择界面。"""
    # 模拟tk.Tk以避免创建实际窗口
    mock_tk = pytest.importorskip("unittest.mock").MagicMock()
    monkeypatch.setattr("tkinter.Tk", mock_tk)

    # 模拟PersonSelectorDialog
    mock_dialog = pytest.importorskip("unittest.mock").MagicMock()
    mock_dialog.return_value.result = "p001"  # 设置模拟的选择结果
    monkeypatch.setattr("src.windows.ui.person_selector.PersonSelectorDialog", mock_dialog)

    person_selector = PersonSelector(test_persons)
    person_id = person_selector.show()
    assert person_id == "p001"


@pytest.mark.skipif(sys.platform != "win32", reason="仅在Windows平台上运行")
@pytest.mark.ui
def test_file_type_selector(test_file_types, logger, monkeypatch):
    """测试文件类型选择界面。"""
    # 模拟tk.Tk以避免创建实际窗口
    mock_tk = pytest.importorskip("unittest.mock").MagicMock()
    monkeypatch.setattr("tkinter.Tk", mock_tk)

    # 模拟FileTypeSelectorDialog
    mock_dialog = pytest.importorskip("unittest.mock").MagicMock()
    mock_dialog.return_value.result = "t001"  # 设置模拟的选择结果
    monkeypatch.setattr("src.windows.ui.file_type_selector.FileTypeSelectorDialog", mock_dialog)

    file_type_selector = FileTypeSelector(test_file_types)
    file_type_id = file_type_selector.show()
    assert file_type_id == "t001"


@pytest.mark.skipif(sys.platform != "win32", reason="仅在Windows平台上运行")
@pytest.mark.ui
def test_person_selector_cancel(test_persons, logger, monkeypatch):
    """测试人员选择界面-用户取消选择。"""
    # 模拟tk.Tk以避免创建实际窗口
    mock_tk = pytest.importorskip("unittest.mock").MagicMock()
    monkeypatch.setattr("tkinter.Tk", mock_tk)

    # 模拟PersonSelectorDialog - 用户取消
    mock_dialog = pytest.importorskip("unittest.mock").MagicMock()
    mock_dialog.return_value.result = None  # 设置为None表示用户取消
    monkeypatch.setattr("src.windows.ui.person_selector.PersonSelectorDialog", mock_dialog)

    person_selector = PersonSelector(test_persons)
    person_id = person_selector.show()
    assert person_id is None


@pytest.mark.skipif(sys.platform != "win32", reason="仅在Windows平台上运行")
@pytest.mark.ui
def test_person_selector_error(test_persons, logger, monkeypatch):
    """测试人员选择界面-发生异常。"""

    # 模拟tk.Tk引发异常
    def mock_tk_error(*args, **kwargs):
        raise Exception("模拟的Tk错误")

    monkeypatch.setattr("tkinter.Tk", mock_tk_error)

    person_selector = PersonSelector(test_persons)
    person_id = person_selector.show()
    assert person_id is None  # 异常情况下应返回None


@pytest.mark.skipif(sys.platform != "win32", reason="仅在Windows平台上运行")
@pytest.mark.ui
def test_file_type_selector_cancel(test_file_types, logger, monkeypatch):
    """测试文件类型选择界面-用户取消选择。"""
    # 模拟tk.Tk以避免创建实际窗口
    mock_tk = pytest.importorskip("unittest.mock").MagicMock()
    monkeypatch.setattr("tkinter.Tk", mock_tk)

    # 模拟FileTypeSelectorDialog - 用户取消
    mock_dialog = pytest.importorskip("unittest.mock").MagicMock()
    mock_dialog.return_value.result = None  # 设置为None表示用户取消
    monkeypatch.setattr("src.windows.ui.file_type_selector.FileTypeSelectorDialog", mock_dialog)

    file_type_selector = FileTypeSelector(test_file_types)
    file_type_id = file_type_selector.show()
    assert file_type_id is None


@pytest.mark.skipif(sys.platform != "win32", reason="仅在Windows平台上运行")
@pytest.mark.ui
def test_file_type_selector_error(test_file_types, logger, monkeypatch):
    """测试文件类型选择界面-发生异常。"""

    # 模拟tk.Tk引发异常
    def mock_tk_error(*args, **kwargs):
        raise Exception("模拟的Tk错误")

    monkeypatch.setattr("tkinter.Tk", mock_tk_error)

    file_type_selector = FileTypeSelector(test_file_types)
    file_type_id = file_type_selector.show()
    assert file_type_id is None  # 异常情况下应返回None
