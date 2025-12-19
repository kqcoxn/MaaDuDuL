class Counter:
    """计数器类。

    用于管理计数操作，支持设置最大计数限制和重置功能。

    Attributes:
        _count: 当前计数值。
        _max: 最大计数限制，-1 表示无限制。
    """

    def __init__(self, initial_count=0, max=-1):
        """初始化计数器。

        Args:
            initial_count: 初始计数值，默认为 0。
            max: 最大计数限制，默认为 -1（无限制）。
        """
        self._count = initial_count
        self._max = max

    def count(self):
        """执行计数操作。

        计数值加 1，如果超过最大限制则返回 -1。

        Returns:
            int: 当前计数值，如果超过最大限制则返回 -1。
        """
        self._count += 1
        if self._max > 0 and self._count > self._max:
            return -1
        return self._count

    def get_count(self):
        """获取当前计数值。

        Returns:
            int: 当前计数值。
        """
        return self._count

    def reset(self):
        """重置计数器。

        将计数值重置为 0。

        Returns:
            Counter: 返回自身实例，支持链式调用。
        """
        self._count = 0
        return self


class CounterManager:
    """计数器管理器类。

    用于集中管理多个计数器实例，提供创建、获取、删除和清空计数器的功能。
    使用字典存储多个命名的计数器，支持按键名访问和管理。

    Attributes:
        counters: 存储所有计数器实例的字典，键为计数器名称，值为 Counter 实例。
    """

    counters = {}

    @classmethod
    def get(cls, key: str = "default", initial_count=0, max=-1) -> Counter:
        """获取或创建计数器实例。

        如果指定键名的计数器不存在，则创建新的计数器实例；
        如果已存在，则直接返回该实例。

        Args:
            key: 计数器的唯一标识键名，默认为 "default"。
            initial_count: 初始计数值，默认为 0。仅在创建新计数器时使用。
            max: 最大计数限制，默认为 -1（无限制）。仅在创建新计数器时使用。

        Returns:
            Counter: 指定键名对应的计数器实例。
        """
        if key not in cls.counters:
            cls.counters[key] = Counter(initial_count, max)
        return cls.counters[key]

    @classmethod
    def remove(cls, key: str):
        """删除指定的计数器实例。

        如果指定键名的计数器存在，则从管理器中删除该计数器。

        Args:
            key: 要删除的计数器的键名。

        Returns:
            CounterManager: 返回类自身，支持链式调用。
        """
        if key in cls.counters:
            del cls.counters[key]
        return cls

    @classmethod
    def clear_all(cls):
        """清空所有计数器实例。

        删除管理器中存储的所有计数器实例。

        Returns:
            CounterManager: 返回类自身，支持链式调用。
        """
        cls.counters.clear()
        return cls
