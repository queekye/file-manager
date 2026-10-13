import os
import pytest


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv('FILE_MANAGER_HOME', str(tmp_path/'state'))
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')
    monkeypatch.setenv('FILE_MANAGER_DISABLE_HOTKEYS', '1')
    monkeypatch.delenv('CONFIGPATH', raising=False)


@pytest.fixture(scope='session')
def qapp():
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    yield app
