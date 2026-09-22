"""Agent lifecycle, shared by desktop, Android and local entrypoints."""

import sys


def run_agent() -> int:
    from maa.agent.agent_server import AgentServer

    from agent import customs  # noqa: F401: importing registers project callbacks
    from agent.customs.utils import Prompter
    from agent.preprocess import clear

    if len(sys.argv) < 2:
        Prompter.log("缺少 Agent socket ID，请通过客户端或 yarn agent 启动。")
        return 2

    try:
        clear()
        AgentServer.start_up(sys.argv[-1])
        try:
            AgentServer.join()
        finally:
            AgentServer.shut_down()
    except Exception as error:
        Prompter.log(f"Agent 启动失败：{error}")
        return 1
    return 0
