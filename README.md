# File Manager

Windows 人员文件整理工具，使用 PyQt5、SQLite 和本地配置。当前公开维护版本为 **1.8.0 beta**，由原私有 `fileManager` 当前源码整理而来；旧分支和标签继续私人保存，新仓是后续开发主线。

功能包括人员及拼音搜索、目录/文件命名模板、多归档根目录、文件和目录复制/移动、单文件重命名与本次会话的撤销。默认复制文件；相同文件名通过后缀区分，显式重命名冲突会拒绝覆盖。没有网络服务、模型权重、内置真实人员名单或 API 凭据。

## 配置与启动

已验证 Windows x64、Python 3.12。先使用独立虚拟环境：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-windows-py312.lock
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
.\.venv\Scripts\file-manager.exe --help
.\.venv\Scripts\file-manager.exe --config-editor
```

首次配置会在 `%LOCALAPPDATA%\FileManager` 创建 `config.yaml`，人员数据保存在 `persons.db`，日志在 `logs`，恢复资料在 `backups`。也可先设置 `FILE_MANAGER_HOME` 为自己可写的独立状态目录；`CONFIGPATH` 为兼容旧部署保留。该目录应私人保存，不要加入 Git。

在配置编辑器中选择实际归档根目录、文件类型、命名模板和复制/移动选项。默认归档目录位于状态目录的 `archive` 下，不再依赖固定 D 盘。启动普通主程序后，可通过托盘选择文件、添加人员与执行整理；人员数据库初始为空。传入文件路径也会进入交互选择：

```powershell
.\.venv\Scripts\python.exe -m src.main --config-editor
.\.venv\Scripts\python.exe -m src.main "C:\Example\sample.txt"
```

全局快捷键需要运行 Windows 桌面会话；设置 `FILE_MANAGER_DISABLE_HOTKEYS=1` 可完全禁用键盘监听和注册。源码和本轮验证不会自动注册右键菜单、开机启动或安装器。

## 检查与构建

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m src.main --smoke-test
.\.venv\Scripts\python.exe -m build --wheel --sdist
.\.venv\Scripts\python.exe scripts\build_windows.py
```

`--smoke-test` 离屏创建配置编辑器和文件选择器后退出，禁用全局快捷键，不执行文件操作。PyInstaller 本地构建输出 `dist\FileM\FileM.exe`；该构建不安装软件。公开仓当前主要分发源码，冻结程序公开分发还需满足 Qt/PyQt 等依赖的完整源码与许可义务。

本轮 77 项维护测试通过，覆盖临时文件真实操作、冲突保留、撤销、模板越界保护、权限失败、保留外部修改的回滚及界面取消。旧测试含已移除的 JSON/Tk 接口，保留在 `legacy`，不视为当前通过的套件。环境、资源位置、验证范围和未来计划见 [HANDOFF.md](HANDOFF.md)。

## 使用边界

- 单文件撤销只保存在当前进程的历史中；目标文件被修改后会拒绝自动撤销。目录操作没有完整撤销支持。
- 取消选择不会开始操作；复制/移动执行过程中尚无通用中断和跨文件批次事务。
- 文件系统操作不是跨进程事务，不承诺断电、网络盘掉线或并发修改下的完整恢复。先在小规模样本上确认配置。
- Windows 托盘、真实快捷键、资源管理器集成及完整安装/卸载没有经过本轮交互验收。历史安装器仅作参考，不是现行发布入口。

## 许可与来源

本人代码、文档、合成测试和新图标采用 **GPL-3.0-only**，完整文本见 [LICENSE](LICENSE)。PyQt5 使用 GPLv3 或商业许可；本项目采用 GPLv3 兼容发布方式，未声称持有商业 PyQt 许可。[Riverbank 官方说明](https://en.riverbankcomputing.com/software/pyqt)。

第三方依赖维持各自许可；完整说明、来源和许可证副本见 [NOTICE](NOTICE)、`THIRD_PARTY_LICENSES.json` 和 `LICENSES/`。旧图标未沿用，新图标由 `scripts/generate_icons.py` 原创几何图案生成。原私有仓的历史及排除项不随本次公开而改变许可或可见性。
