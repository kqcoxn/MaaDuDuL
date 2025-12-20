"""本地存储模块。

提供基于 JSON 文件的键值存储功能，用于持久化配置和状态数据。
"""

import os
import json


class LocalStorage:
    """本地存储类。

    提供简单的键值对存储功能，数据以 JSON 格式保存到本地文件。
    所有方法均为类方法，可直接通过类名调用。
    """

    # 存储文件路径配置
    agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_dir = os.path.join(agent_dir, "..", "config", "mddl")
    storage_path = os.path.join(config_dir, "local_storage.json")

    @classmethod
    def _ensure_storage_file(cls):
        """检查并确保存储文件存在。

        如果配置目录或存储文件不存在，则自动创建。
        存储文件初始化为空 JSON 对象。
        """
        # 确保配置目录存在
        if not os.path.exists(cls.config_dir):
            os.makedirs(cls.config_dir)

        # 确保存储文件存在
        if not os.path.exists(cls.storage_path):
            with open(cls.storage_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    @classmethod
    def _read(cls) -> dict:
        """读取存储数据。

        从存储文件中读取所有数据。如果文件不存在或格式错误，
        会自动创建或重置为空对象。

        Returns:
            dict: 存储的所有键值对数据。
        """
        cls._ensure_storage_file()
        try:
            with open(cls.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # 存储文件格式错误时重置为空对象
            with open(cls.storage_path, "w", encoding="utf-8") as f:
                json.dump({}, f)
            return {}

    @classmethod
    def _write(cls, storage: dict) -> bool:
        """写入存储数据到文件。

        将数据写入到存储文件中，覆盖原有内容。

        Args:
            storage: 要写入的存储数据字典。

        Returns:
            bool: 写入成功返回 True，失败返回 False。
        """
        try:
            with open(cls.storage_path, "w", encoding="utf-8") as f:
                json.dump(storage, f)
            return True
        except Exception as e:
            print(f"存储数据时出错：{e}")
            return False

    @classmethod
    def get(cls, key: str):
        """获取存储值。

        根据键名获取对应的存储值。

        Args:
            key: 存储项的键名。

        Returns:
            存储的值，如果键不存在则返回 None。
        """
        storage = cls._read()
        return storage.get(key)

    @classmethod
    def set(cls, key: str, value) -> bool:
        """设置存储值。

        设置或更新指定键的值，并保存到文件。

        Args:
            key: 存储项的键名。
            value: 要存储的值，可以是任何可 JSON 序列化的对象。

        Returns:
            bool: 设置成功返回 True，失败返回 False。
        """
        storage = cls._read()
        storage[key] = value
        return cls._write(storage)
