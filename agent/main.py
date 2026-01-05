"""MaaDuDuL Agent 主入口。

负责初始化环境、检查依赖、启动 Agent 服务器。
"""

import os
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


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

from agent.preprocess import check_and_install_dependencies


def main():
    """启动 MaaDuDuL Agent 服务"""
    from maa.agent.agent_server import AgentServer
    from maa.toolkit import Toolkit
    from agent import customs
    from agent.preprocess import clear
    from agent.devops import punch_in

    try:
        # 清理调试文件
        clear()
        # 初始化 MaaFW 工具包
        Toolkit.init_option("./")
        # 获取 socket ID 并启动服务
        socket_id = sys.argv[-1]
        AgentServer.start_up(socket_id)
        # devops
        punch_in()
        # 等待服务结束
        AgentServer.join()
        AgentServer.shut_down()

    except Exception as e:
        print(f"info:Agent 启动失败：{e}")
        sys.exit(1)


if __name__ == "__main__":
    if not os.getenv("MDDL_DEV_MODE"):
        check_and_install_dependencies()
    main()
