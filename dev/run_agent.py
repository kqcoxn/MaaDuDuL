"""Agent 调试启动脚本。

用于在开发模式下快速启动 Agent 服务，自动配置环境变量。
"""

import os
import sys
import subprocess
from pathlib import Path

# 切换到项目根目录
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
os.chdir(project_root)

# 添加项目根目录到 Python 路径
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def run_agent_debug():
    """以调试模式启动 Agent 服务"""
    # 设置开发模式环境变量
    env = os.environ.copy()
    env["MDDL_DEV_MODE"] = "1"

    # 从环境变量获取模拟的 socket ID，若未设置则使用默认值
    socket_id = env.get("MDDL_SOCKET_ID", "debug")

    print(f"🚀 开发模式启动 Agent...")
    print(f"📡 Socket ID: {socket_id}")
    print(f"📁 工作目录: {project_root}")
    print(f"🔧 MDDL_DEV_MODE: {env.get('MDDL_DEV_MODE')}")
    print("-" * 50)

    # 启动 Agent
    cmd = [sys.executable, "agent/main.py", socket_id]

    try:
        subprocess.run(cmd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Agent 启动失败: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  用户中断")
        sys.exit(0)


if __name__ == "__main__":
    run_agent_debug()
