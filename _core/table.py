from dbqk._core.result import ExecResult


class BaseTable:
    """单表 CRUD 公共实现。"""

    identifier_quote = ""

    def __init__(self, db, name: str):
        self._db = db
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @classmethod
    def _quote_identifier(cls, name: str) -> str:
        return f"{cls.identifier_quote}{name}{cls.identifier_quote}"

    @classmethod
    def _build_where(cls, where: dict | None) -> tuple[str, list]:
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
                keys.append(f"{cls._quote_identifier(col)} {op_map.get(op, '=')} %s")
            else:
                keys.append(f"{cls._quote_identifier(k)} = %s")
            values.append(v)
        return " WHERE " + " AND ".join(keys), values

    def insert(self, data: dict | list[dict], **kwargs) -> ExecResult:
        if isinstance(data, dict):
            cols = list(data.keys())
            cols_str = ", ".join(self._quote_identifier(c) for c in cols)
            placeholders = ", ".join(["%s"] * len(cols))
            sql = (
                f"INSERT INTO {self._quote_identifier(self._name)} "
                f"({cols_str}) "
                f"VALUES ({placeholders})"
            )
            return self._db.exec(sql, list(data.values()), **kwargs)

        if isinstance(data, list) and data:
            cols = list(data[0].keys())
            cols_str = ", ".join(self._quote_identifier(c) for c in cols)
            placeholders = ", ".join(["%s"] * len(cols))
            sql = (
                f"INSERT INTO {self._quote_identifier(self._name)} "
                f"({cols_str}) "
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
        cols = "*" if not columns else ", ".join(self._quote_identifier(c) for c in columns)
        sql = f"SELECT {cols} FROM {self._quote_identifier(self._name)}"
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
        return self.select(where=where, limit=1, **kwargs)

    def count(self, where: dict | None = None) -> int:
        sql = f"SELECT COUNT(*) AS cnt FROM {self._quote_identifier(self._name)}"
        where_sql, params = self._build_where(where)
        sql += where_sql
        result = self._db.exec(sql, params, fetch_mode="dict")
        return result.scalar or 0

    def update(self, data: dict, where: dict | None = None) -> ExecResult:
        if not data:
            raise ValueError("update 数据不能为空")
        set_clause = ", ".join(f"{self._quote_identifier(k)} = %s" for k in data.keys())
        sql = f"UPDATE {self._quote_identifier(self._name)} SET {set_clause}"
        params = list(data.values())
        where_sql, where_params = self._build_where(where)
        sql += where_sql
        params += where_params
        return self._db.exec(sql, params)

    def delete(self, where: dict | None = None) -> ExecResult:
        sql = f"DELETE FROM {self._quote_identifier(self._name)}"
        where_sql, params = self._build_where(where)
        if not where_sql:
            raise ValueError("拒绝执行无 WHERE 的 DELETE，请显式传入 where={...}")
        sql += where_sql
        return self._db.exec(sql, params)

    def __repr__(self):
        return f"<Table {self._name}>"
