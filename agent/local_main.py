"""MaaDuDuL Agent 本地运行入口。

这是 ``agent/main.py`` 的本地环境启动器。服务初始化和 AgentServer
生命周期均由正式入口实现，避免本地运行和打包运行出现行为差异。

用法::

    python agent/local_main.py [socket_id]
    python agent/local_main.py --socket-id [socket_id]
"""

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 本地环境使用当前 Python 环境，不触发打包环境的依赖安装流程。
os.environ.setdefault("MDDL_DEV_MODE", "1")


def _socket_id(arguments: list[str]) -> str:
    """从命令行参数中取得 socket 标识，未提供时使用本地默认值。"""
    if arguments and arguments[0] in {"-s", "--socket-id"}:
        arguments = arguments[1:]
    return arguments[0] if arguments else os.environ.get("MDDL_SOCKET_ID", "local")


def main() -> None:
    """使用正式 Agent 入口启动本地服务。"""
    socket_id = _socket_id(sys.argv[1:])

    # agent.main.main() 从 sys.argv[-1] 读取 socket_id，保持其原有入口契约。
    sys.argv = [str(PROJECT_ROOT / "agent" / "main.py"), socket_id]
    from agent.main import main as run_agent

    run_agent()


if __name__ == "__main__":
    main()
