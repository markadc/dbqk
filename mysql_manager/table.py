from .result import ExecResult


class Table:
    """单表 CRUD 封装。

    所有方法最终都会调用 ``Database.exec()`` 执行 SQL，并直接返回
    ``ExecResult`` 对象，使用方通过属性访问获取所需信息。

    Attributes:
        name: 表名（只读属性）。
    """

    def __init__(self, db, name: str):
        """初始化表对象。

        Args:
            db: 关联的 ``Database`` 实例。
            name: 表名。
        """
        self._db = db
        self._name = name

    @property
    def name(self) -> str:
        """返回表名。"""
        return self._name

    @staticmethod
    def _build_where(where: dict | None) -> tuple[str, list]:
        """根据字典构建 WHERE 子句。

        支持后缀语法糖来表示比较操作符：

        * ``key__gt``  -> ``key > %s``
        * ``key__gte`` -> ``key >= %s``
        * ``key__lt``  -> ``key < %s``
        * ``key__lte`` -> ``key <= %s``
        * ``key__ne``  -> ``key != %s``
        * ``key__like``-> ``key LIKE %s``
        * 默认 -> ``key = %s``

        Args:
            where: WHERE 条件字典，None 或空字典表示无条件。

        Returns:
            tuple: ``(sql_clause, params_list)``。
            sql_clause 形如 ``" WHERE `a` = %s AND `b` > %s"``。
        """
        if not where:
            return "", []
        keys, values = [], []
        op_map = {
            "gt": ">", "gte": ">=", "lt": "<", "lte": "<=",
            "ne": "!=", "like": "LIKE",
        }
        for k, v in where.items():
            if "__" in k:
                col, op = k.rsplit("__", 1)
                keys.append(f"`{col}` {op_map.get(op, '=')} %s")
            else:
                keys.append(f"`{k}` = %s")
            values.append(v)
        return " WHERE " + " AND ".join(keys), values

    def insert(self, data: dict | list[dict], **kwargs) -> ExecResult:
        """插入单条或多条记录。

        Args:
            data: 单条记录传 dict；批量插入传 list[dict]，要求所有 dict 的 key 一致。
            **kwargs: 透传给 ``Database.exec``，例如 ``fetch_mode``。

        Returns:
            ExecResult: 单条插入可读 ``.lastrowid``；批量插入可读 ``.rowcount``。

        Raises:
            ValueError: 当 data 既不是 dict 也不是非空 list[dict] 时抛出。
        """
        if isinstance(data, dict):
            cols = list(data.keys())
            placeholders = ", ".join(["%s"] * len(cols))
            sql = (
                f"INSERT INTO `{self._name}` "
                f"({', '.join(f'`{c}`' for c in cols)}) "
                f"VALUES ({placeholders})"
            )
            return self._db.exec(sql, list(data.values()), **kwargs)

        if isinstance(data, list) and data:
            cols = list(data[0].keys())
            placeholders = ", ".join(["%s"] * len(cols))
            sql = (
                f"INSERT INTO `{self._name}` "
                f"({', '.join(f'`{c}`' for c in cols)}) "
                f"VALUES ({placeholders})"
            )
            params = [[row[c] for c in cols] for row in data]
            return self._db.exec(sql, params, many=True, **kwargs)

        raise ValueError("data 必须是 dict 或 list[dict]")

    def select(
        self,
        where: dict | None = None,
        columns: list[str] | tuple[str, ...] | None = None,
        order_by: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        fetch_mode: str = "dict",
    ) -> ExecResult:
        """查询记录。

        Args:
            where: WHERE 条件，支持 ``_build_where`` 的语法糖。
            columns: 要查询的列，None 表示 ``*``。
            order_by: ORDER BY 子句内容，例如 ``"id DESC"``。
            limit: LIMIT 数量。
            offset: OFFSET 偏移（仅在 limit 不为 None 时生效）。
            fetch_mode: 返回格式，``"dict"`` 或 ``"tuple"``。

        Returns:
            ExecResult: 通过 ``.rows`` / ``.first`` / ``.scalar`` 访问数据。
        """
        cols = "*" if not columns else ", ".join(f"`{c}`" for c in columns)
        sql = f"SELECT {cols} FROM `{self._name}`"
        where_sql, params = self._build_where(where)
        sql += where_sql
        if order_by:
            sql += f" ORDER BY {order_by}"
        if limit is not None:
            sql += f" LIMIT {int(limit)}"
            if offset is not None:
                sql += f" OFFSET {int(offset)}"
        return self._db.exec(sql, params, fetch_mode=fetch_mode)

    def find_one(self, where: dict | None = None, **kwargs) -> ExecResult:
        """查询符合条件的第一条记录。

        Args:
            where: WHERE 条件。
            **kwargs: 透传给 ``select``，例如 ``columns``、``fetch_mode``。

        Returns:
            ExecResult: 用 ``result.first`` 取得单行（不存在时为 None）。
        """
        return self.select(where=where, limit=1, **kwargs)

    def count(self, where: dict | None = None) -> int:
        """统计符合条件的记录数。

        Args:
            where: WHERE 条件。None 表示统计全表。

        Returns:
            int: 记录数。该方法直接返回整数，方便日常使用。
        """
        sql = f"SELECT COUNT(*) AS cnt FROM `{self._name}`"
        where_sql, params = self._build_where(where)
        sql += where_sql
        result = self._db.exec(sql, params, fetch_mode="dict")
        return result.scalar or 0

    def update(self, data: dict, where: dict | None = None) -> ExecResult:
        """更新记录。

        Args:
            data: 要更新的字段，``{column: value}``。
            where: WHERE 条件。

        Returns:
            ExecResult: 通过 ``.rowcount`` 获取受影响行数。

        Raises:
            ValueError: 当 data 为空时抛出。
        """
        if not data:
            raise ValueError("update 数据不能为空")
        set_clause = ", ".join(f"`{k}` = %s" for k in data.keys())
        sql = f"UPDATE `{self._name}` SET {set_clause}"
        params = list(data.values())
        where_sql, where_params = self._build_where(where)
        sql += where_sql
        params += where_params
        return self._db.exec(sql, params)

    def delete(self, where: dict | None = None) -> ExecResult:
        """删除记录。

        为安全起见，必须显式传入非空 ``where``，否则拒绝执行。

        Args:
            where: WHERE 条件，不可为空。

        Returns:
            ExecResult: 通过 ``.rowcount`` 获取受影响行数。

        Raises:
            ValueError: 未提供 where 时抛出（防止误删全表）。
        """
        sql = f"DELETE FROM `{self._name}`"
        where_sql, params = self._build_where(where)
        if not where_sql:
            raise ValueError("拒绝执行无 WHERE 的 DELETE，请显式传入 where={...}")
        sql += where_sql
        return self._db.exec(sql, params)

    def __repr__(self):
        return f"<Table {self._name}>"
