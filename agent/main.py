"""MaaDuDuL Agent 主入口。

负责初始化环境、检查依赖、启动 Agent 服务器。
"""

import os
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agent.preprocess import check_and_install_dependencies

# 设置控制台编码
sys.stdout.reconfigure(encoding="gbk")
sys.stderr.reconfigure(encoding="gbk")


def main():
    """启动 MaaDuDuL Agent 服务"""
    from agent.preprocess import clear
    from maa.agent.agent_server import AgentServer
    from maa.toolkit import Toolkit
    import customs

    try:
        # 清理调试文件
        clear()
        # 初始化 MaaFW 工具包
        Toolkit.init_option("./")
        # 获取 socket ID 并启动服务
        socket_id = sys.argv[-1]
        AgentServer.start_up(socket_id)
        AgentServer.join()
        AgentServer.shut_down()

    except Exception as e:
        print(f"info:Agent 启动失败：{e}")
        sys.exit(1)


if __name__ == "__main__":
    if not os.getenv("MDDL_DEV_MODE"):
        check_and_install_dependencies()
    main()
