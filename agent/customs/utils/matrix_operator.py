class MatrixOperator:
    """矩阵位置计算器

    用于计算矩阵布局中各元素的实际坐标位置。
    通过指定起始位置和步长，可以快速获取矩阵中任意元素的坐标。
    """

    def __init__(
        self,
        origin_x: int,
        origin_y: int,
        step_x: int,
        step_y: int,
        width: int = None,
        height: int = None,
    ):
        """初始化矩阵操作器

        参数：
            origin_x：矩阵起始位置的 X 坐标
            origin_y：矩阵起始位置的 Y 坐标
            step_x：矩阵元素之间的 X 轴步长
            step_y：矩阵元素之间的 Y 轴步长
            width：矩阵元素的宽度（可选）
            height：矩阵元素的高度（可选）
        """
        self.start_pos = (origin_x, origin_y)
        self.step = (step_x, step_y)
        self.width = width
        self.height = height

    def get_pos(self, row: int, column: int) -> tuple[int, int]:
        """获取矩阵中指定位置的坐标

        参数：
            row：矩阵中的行索引（从 1 开始，负数时从底部倒数）
            column：矩阵中的列索引（从 1 开始，负数时从右边倒数）

        返回：
            tuple：包含 (x, y) 坐标的元组

        异常：
            ValueError：当 row 或 column 为负数但未提供 height 或 width 时抛出
        """
        # 处理负数索引
        if row < 0:
            if self.height is None:
                raise ValueError("使用负数索引时必须提供 height 参数")
            row = self.height + row + 1
        if column < 0:
            if self.width is None:
                raise ValueError("使用负数索引时必须提供 width 参数")
            column = self.width + column + 1

        x = self.start_pos[0] + (column - 1) * self.step[0]
        y = self.start_pos[1] + (row - 1) * self.step[1]
        return (x, y)
