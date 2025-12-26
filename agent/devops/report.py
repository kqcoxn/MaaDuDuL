"""数据上报模块。

该模块负责向远程服务器发送使用统计信息。
"""

import requests


def punch_in():
    """发送打卡数据到远程服务器。

    向指定的统计服务器发送项目使用信息，包括来源标识和版本号。

    Returns:
        dict: 服务器返回的 JSON 响应数据。
        Exception: 当请求失败时返回异常对象。

    Note:
        请求超时时间设置为 3 秒，失败时不会中断程序执行。
    """
    try:
        # 发送 POST 请求到统计服务器
        response = requests.post(
            "http://ts.codax.site/repo",
            json={"from": "mddl", "version": "v0.0.8"},
            headers={"Content-Type": "application/json"},
            timeout=3,
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        return e
