import os
import sys


def get_app_root() -> str:
    """
    获取应用程序根目录的绝对路径。

    Returns:
        str: 应用程序根目录的绝对路径
            - 如果是打包后的程序，返回环境变量RESOURCEPATH指定的目录
            - 如果是直接运行的Python脚本，返回项目根目录
    """
    # 如果是 PyInstaller 打包的程序
    if getattr(sys, "frozen", False):
        # 使用环境变量中的路径
        return os.environ.get("RESOURCEPATH", os.path.dirname(sys.executable))
    # 如果是直接运行 Python 脚本
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
