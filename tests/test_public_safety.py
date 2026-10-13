from pathlib import Path
from types import SimpleNamespace
import pytest

from src.core.config import Config
from src.core.directory_manager import DirectoryManager
from src.core.file_manager import FileManager
from src.core.exceptions import FileExistsError, FileOperationError, DirectoryCreationError
from src.core.person_manager import PersonManager
from src.utils.state_paths import get_state_root


PERSON = {'id':'fixture-001','name':'测试人员甲','directory':'fixture-person'}
TYPE = {'id':'fixture-document','name':'测试文档','directory':'documents'}


def manager(tmp_path, **kwargs):
    return FileManager(DirectoryManager(str(tmp_path/'archive')),
        naming_pattern='{original_filename}{original_extension}',
        log_dir=str(tmp_path/'logs'), backup_dir=str(tmp_path/'backups'), **kwargs)


@pytest.mark.parametrize('operation', ['copy_file','move_file'])
def test_real_copy_and_move_preserve_bytes(tmp_path, operation):
    source = tmp_path/'input.bin'
    source.write_bytes(b'\0synthetic\xffpayload')
    fm = manager(tmp_path)
    result = getattr(fm, operation)(str(source), PERSON, TYPE)
    assert result.success
    assert Path(result.destination_path).read_bytes() == b'\0synthetic\xffpayload'
    assert source.exists() == (operation == 'copy_file')
    undone = fm.undo_last_operation()
    assert undone.success
    assert source.read_bytes() == b'\0synthetic\xffpayload'
    assert not Path(result.destination_path).exists()


def test_duplicate_copy_retains_both_existing_and_new_content(tmp_path):
    source = tmp_path/'input.txt'
    source.write_text('first', encoding='utf8')
    fm = manager(tmp_path)
    first = fm.copy_file(str(source), PERSON, TYPE)
    source.write_text('second', encoding='utf8')
    second = fm.copy_file(str(source), PERSON, TYPE)
    assert first.destination_path != second.destination_path
    assert Path(first.destination_path).read_text() == 'first'
    assert Path(second.destination_path).read_text() == 'second'


def test_rename_conflict_never_deletes_existing_target(tmp_path):
    source, destination = tmp_path/'a.txt', tmp_path/'b.txt'
    source.write_text('a'); destination.write_text('b')
    fm = manager(tmp_path)
    with pytest.raises(FileExistsError):
        fm.rename_file(str(source), destination.name)
    assert source.read_text() == 'a'
    assert destination.read_text() == 'b'
    assert fm.get_operation_history() == []


def test_real_rename_and_undo(tmp_path):
    source = tmp_path/'a.txt'; source.write_text('fixture')
    fm = manager(tmp_path)
    result = fm.rename_file(str(source), 'renamed.txt')
    assert result.success and not source.exists()
    assert fm.undo_last_operation().success
    assert source.read_text() == 'fixture'


@pytest.mark.parametrize('new_name', ['../outside.txt', '..\\outside.txt', '.'])
def test_rename_rejects_directory_paths(tmp_path, new_name):
    source = tmp_path/'a.txt'; source.write_text('fixture')
    with pytest.raises(FileOperationError):
        manager(tmp_path).rename_file(str(source), new_name)
    assert source.read_text() == 'fixture'


def test_undo_keeps_a_destination_modified_after_copy(tmp_path):
    source = tmp_path/'a.txt'; source.write_text('fixture')
    fm = manager(tmp_path)
    result = fm.copy_file(str(source), PERSON, TYPE)
    destination = Path(result.destination_path)
    destination.write_text('independent update')
    assert fm.undo_last_operation().success is False
    assert destination.read_text() == 'independent update'
    assert source.read_text() == 'fixture'


def test_permission_failure_keeps_source_and_does_not_report_success(tmp_path, monkeypatch):
    source = tmp_path/'a.txt'; source.write_text('fixture')
    fm = manager(tmp_path)
    def denied(*args, **kwargs):
        raise PermissionError('synthetic permission failure')
    monkeypatch.setattr('src.core.file_manager.shutil.copy2', denied)
    with pytest.raises(FileOperationError):
        fm.move_file(str(source), PERSON, TYPE)
    assert source.read_text() == 'fixture'
    assert fm.get_operation_history() == []
    assert list((tmp_path/'archive').rglob('*.txt')) == []


def test_template_cannot_escape_selected_root(tmp_path):
    fm = manager(tmp_path)
    source = tmp_path/'a.txt'; source.write_text('fixture')
    with pytest.raises(FileOperationError):
        fm.copy_file(str(source), {**PERSON,'directory':'../../outside'}, TYPE)
    assert not (tmp_path.parent/'outside').exists()
    assert source.read_text() == 'fixture'


def test_directory_rollback_keeps_new_external_content(tmp_path):
    dm = DirectoryManager(str(tmp_path/'archive'))
    dm._begin_transaction()
    created = tmp_path/'archive/new'
    dm.ensure_directory(str(created))
    marker = created/'independent.txt'; marker.write_text('keep')
    dm._rollback_transaction()
    assert marker.read_text() == 'keep'


def test_directory_rollback_removes_only_empty_created_folder(tmp_path):
    dm = DirectoryManager(str(tmp_path/'archive'))
    dm._begin_transaction()
    created = tmp_path/'archive/new'
    dm.ensure_directory(str(created))
    dm._rollback_transaction()
    assert not created.exists()


def test_permission_repair_does_not_broaden_acl(tmp_path, monkeypatch):
    dm = DirectoryManager(str(tmp_path/'archive'))
    called = []
    monkeypatch.setattr('subprocess.run', lambda *args, **kwargs: called.append(args))
    assert dm._fix_directory_permissions(tmp_path) is False
    assert called == []


def test_default_configuration_and_database_are_inside_explicit_state(tmp_path):
    config = Config()
    assert Path(config.config_path).is_relative_to(get_state_root())
    assert Path(config.get_base_directory()).is_relative_to(get_state_root())
    people = PersonManager(config=config)
    assert Path(people.db.db_path).is_relative_to(get_state_root())
    assert people.get_all_persons() == []
    people.db.close()


def test_offscreen_widget_setup_and_cancel_perform_no_file_operation(tmp_path, qapp, monkeypatch):
    from PyQt5.QtWidgets import QDialog
    from src.windows.ui.file_selector import FileSelector
    from src.windows.ui.config_editor import ConfigEditor
    config = Config(str(tmp_path/'config.yaml'))
    def forbidden(*args, **kwargs):
        raise AssertionError('offscreen test must not hook the keyboard')
    monkeypatch.setattr('keyboard.wait', forbidden)
    monkeypatch.setattr('keyboard.add_hotkey', forbidden)
    editor = ConfigEditor(config)
    assert editor.hotkey_manager._keyboard_thread is None
    selector = FileSelector()
    source = tmp_path/'cancelled.txt'; source.write_text('keep')
    selector.selected_files = [str(source)]
    selector.reject()
    assert selector.result() == QDialog.Rejected
    assert source.read_text() == 'keep'
    assert not Path(config.get_base_directory()).exists()
    editor.close(); selector.close()
