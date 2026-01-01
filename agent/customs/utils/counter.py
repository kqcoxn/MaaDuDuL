class Counter:
    """计数器类。

    用于管理计数操作，支持设置最大计数限制和重置功能。

    Attributes:
        _count: 当前计数值。
        _max: 最大计数限制，-1 表示无限制。
    """

    def __init__(self, max_count=-1, initial_count=0):
        """初始化计数器。

        Args:
            max_count: 最大计数限制，默认为 -1（无限制）。
            initial_count: 初始计数值，默认为 0。
        """
        self._count = initial_count
        self._max = max_count

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

    @property
    def cur_count(self):
        """获取当前计数值。

        Returns:
            int: 当前计数值。
        """
        return self._count

    @property
    def max_count(self):
        """获取最大计数值。

        Returns:
            int: 最大计数值。
        """
        return self._max

    @property
    def is_max(self):
        """判断是否达到最大计数值。

        Returns:
            bool: 如果达到最大计数值则返回 True，否则返回 False。
        """
        if self._max < 0:
            return False
        return self._count >= self._max

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
    def get(
        cls, key: str = "default", max_count=-1, initial_count=0, strict=False
    ) -> Counter:
        """获取或创建计数器实例。

        如果指定键名的计数器不存在，则创建新的计数器实例；
        如果已存在，则直接返回该实例。

        Args:
            key: 计数器的唯一标识键名，默认为 "default"。
            max_count: 最大计数限制，默认为 -1（无限制）。仅在创建新计数器时使用。
            initial_count: 初始计数值，默认为 0。仅在创建新计数器时使用。
            strict: 严格模式，默认为 False。为 True 时若计数器不存在则抛出 KeyError。

        Returns:
            Counter: 指定键名对应的计数器实例。

        Raises:
            KeyError: 当 strict=True 且指定键名的计数器不存在时抛出。
        """
        if key not in cls.counters:
            if strict:
                raise KeyError(f"Counter with key '{key}' does not exist")
            cls.counters[key] = Counter(max_count, initial_count)
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
