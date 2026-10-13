"""Build a local source-verifiable Windows onedir package, without installing it."""
from pathlib import Path
import sys, subprocess

root = Path(__file__).resolve().parents[1]
args = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir',
        '--console', '--name', 'FileM', '--paths', str(root),
        '--icon', str(root/'resources/app.ico'),
        '--runtime-hook', str(root/'src/hooks/runtime_hook.py')]
for source, destination in [('resources','resources'),('LICENSE','.'),('NOTICE','.'),('LICENSES','LICENSES')]:
    args.extend(['--add-data', str(root/source)+';'+destination])
args.append(str(root/'src/main.py'))
subprocess.run(args, cwd=root, check=True)
