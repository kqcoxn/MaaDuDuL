"""MaaDuDuL Agent 主入口。

负责初始化环境并启动 Agent 服务器；发布包在构建时安装依赖。
"""

import os
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# MFAAvalonia Android exposes the APK's native libraries through this directory.
android_native_dir = os.environ.get("MAA_LIBRARY_DIR")
if android_native_dir:
    os.environ.setdefault("MAAFW_BINARY_PATH", android_native_dir)


# 设置默认编码为 UTF-8
import locale

os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.platform == "win32":
    # Windows
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")
    # 设置默认文件系统编码
    if hasattr(sys, "_enablelegacywindowsfsencoding"):
        sys._enablelegacywindowsfsencoding()
else:
    # macOS、Linux
    try:
        locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, "C.UTF-8")
        except locale.Error:
            pass

    # 确保标准输出使用 UTF-8
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")

os.chdir(PROJECT_ROOT)


def main():
    """启动 MaaDuDuL Agent 服务。"""
    from agent.agent_runtime import run_agent

    sys.exit(run_agent())


if __name__ == "__main__":
    main()
