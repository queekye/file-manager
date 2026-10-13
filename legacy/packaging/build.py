import os
import shutil
import sys
import time
import site
from pathlib import Path

import PyInstaller.__main__


def wait_for_directory_unlock(path, timeout=30):
    """等待目录解锁。

    Args:
        path: 目录路径
        timeout: 超时时间（秒）

    Returns:
        bool: 是否成功解锁
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            if os.path.exists(path):
                # 尝试重命名目录（这会失败如果目录被锁定）
                temp_path = str(path) + "_temp"
                os.rename(path, temp_path)
                os.rename(temp_path, path)
            return True
        except (OSError, PermissionError):
            print(f"等待目录 {path} 解锁...")
            time.sleep(1)
    return False


def create_runtime_hook():
    """创建运行时钩子文件"""
    hook_dir = Path("src/hooks")
    hook_dir.mkdir(parents=True, exist_ok=True)

    hook_content = '''
import os
import sys

def configure_environment():
    """配置运行环境"""
    if hasattr(sys, '_MEIPASS'):
        os.environ['RESOURCEPATH'] = sys._MEIPASS
        os.environ['LOGPATH'] = os.path.join(sys._MEIPASS, 'logs')
        os.environ['CONFIGPATH'] = os.path.join(sys._MEIPASS, 'resources')
        
        # 添加PyQt5插件路径
        if os.path.exists(os.path.join(sys._MEIPASS, 'PyQt5', 'plugins')):
            os.environ['QT_PLUGIN_PATH'] = os.path.join(sys._MEIPASS, 'PyQt5', 'plugins')

configure_environment()
    '''.strip()

    with open(hook_dir / "runtime_hook.py", "w", encoding="utf-8") as f:
        f.write(hook_content)


def copy_resources(src_dir: Path, dst_dir: Path, patterns: list):
    """优化的资源复制函数"""
    dst_dir.mkdir(parents=True, exist_ok=True)

    for pattern in patterns:
        for src_file in src_dir.glob(pattern):
            if src_file.is_file():
                dst_file = dst_dir / src_file.name
                if not dst_file.exists() or src_file.stat().st_mtime > dst_file.stat().st_mtime:
                    shutil.copy2(src_file, dst_file)


def find_pyqt5_plugins():
    """查找PyQt5插件目录"""
    for path in site.getsitepackages():
        plugins_path = Path(path) / "PyQt5" / "plugins"
        if plugins_path.exists():
            return str(plugins_path)
    return None


def build_app():
    """
    使用 PyInstaller 打包应用程序，并处理资源文件。
    """
    # 获取项目根目录
    root_dir = Path(__file__).parent

    # 定义资源目录
    resources_dir = root_dir / "resources"
    dist_dir = root_dir / "dist" / "FileM"

    # 等待输出目录解锁
    if not wait_for_directory_unlock(dist_dir):
        print("错误：无法访问输出目录，请确保没有其他程序正在使用该目录。")
        return

    # 创建运行时钩子
    create_runtime_hook()

    # 获取图标的绝对路径
    icon_path = str(resources_dir / "app.ico")
    
    # 查找PyQt5插件目录
    pyqt5_plugins = find_pyqt5_plugins()
    
    # PyInstaller 打包参数
    pyinstaller_args = [
        "src/main.py",  # 主程序入口
        "--name=FileM",  # 可执行文件名改为 FileM
        "--noconfirm",  # 覆盖已存在的打包目录
        "--noconsole",  # 不显示控制台窗口
        "--clean",  # 清理临时文件
        "--onedir",  # 生成目录形式的可执行程序
        "--optimize=2",
        "--noupx",
        "--exclude-module=pytest",
        "--exclude-module=unittest",
        "--exclude-module=tkinter",
        "--runtime-hook=src/hooks/runtime_hook.py",
        f"--icon={icon_path}",  # 使用绝对路径
        f"--distpath={dist_dir.parent}",  # 指定输出目录
        f"--add-data={resources_dir};resources",  # 使用完整的资源目录路径
        f'--workpath={root_dir / "build"}',  # 指定工作目录
        "--specpath=build",  # 指定spec文件目录
    ]
    
    # 添加PyQt5插件目录
    if pyqt5_plugins:
        pyinstaller_args.append(f"--add-data={pyqt5_plugins};PyQt5/plugins")
        print(f"已添加PyQt5插件目录: {pyqt5_plugins}")

    try:
        # 执行 PyInstaller 打包
        PyInstaller.__main__.run(pyinstaller_args)

        print("打包完成！")
        print(f"可执行文件位置: {dist_dir}")

    except Exception as e:
        print(f"打包过程中出错: {e}")
        raise


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    build_app()
