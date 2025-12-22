# pyinstaller --onefile --icon=../public/logo.ico --windowed MaaDuDuL.py

import subprocess
import platform
import os

# 根据操作系统确定可执行文件路径
if platform.system() == "Windows":
    mfa_path = "MFAAvalonia.exe"
elif platform.system() == "Darwin":  # macOS
    mfa_path = "MFAAvalonia"
elif platform.system() == "Linux":
    mfa_path = "MFAAvalonia"
else:
    raise RuntimeError(f"不支持的操作系统: {platform.system()}")

# 检查文件是否存在
if not os.path.exists(mfa_path):
    raise FileNotFoundError(f"找不到可执行文件: {mfa_path}")

subprocess.run(mfa_path)
