from typing import Any, Iterator


class ExecResult:
    """SQL 执行结果的统一封装对象。

    通过属性访问获取不同维度的执行信息，避免根据 SQL 类型记忆不同的返回格式。

    支持的访问方式：

    * ``result.rows``       — 结果集（仅 SELECT 类）。
    * ``result.lastrowid``  — 自增 id（INSERT 时有意义）。
    * ``result.rowcount``   — 受影响 / 返回的行数。
    * ``result.first``      — 第一行，没有则为 None。
    * ``result.one()``      — 第一行，并要求恰好 1 行。
    * ``result.scalar``     — 第一行第一列的值。
    * ``result.sql``        — 执行的 SQL（便于调试）。
    * ``result.params``     — 执行时的参数。
    * 可迭代 / 可索引 / 可 ``len()``，行为等同于 ``result.rows``。
    * ``bool(result)``      — SELECT 看是否有行；DML 看 rowcount > 0。

    Attributes:
        rows: 结果集，None 表示非查询语句。
        lastrowid: 最近一次 INSERT 的自增 id。
        rowcount: 受影响行数（DML）或返回行数（SELECT）。
        sql: 实际执行的 SQL 文本。
        params: 实际传入的参数。
        sql_kind: SQL 关键字大写形式，如 ``"SELECT"`` / ``"INSERT"``。
    """

    __slots__ = ("rows", "lastrowid", "rowcount", "sql", "params", "sql_kind")

    def __init__(
        self,
        rows: list | None = None,
        lastrowid: int | None = None,
        rowcount: int = 0,
        sql: str = "",
        params: Any = None,
        sql_kind: str = "",
    ):
        self.rows = rows
        self.lastrowid = lastrowid
        self.rowcount = rowcount
        self.sql = sql
        self.params = params
        self.sql_kind = sql_kind

    @property
    def first(self) -> Any | None:
        if self.rows:
            return self.rows[0]
        return None

    @property
    def scalar(self) -> Any:
        row = self.first
        if row is None:
            return None
        if isinstance(row, dict):
            return next(iter(row.values()))
        return row[0]

    def one(self) -> Any:
        if not self.rows:
            raise ValueError("one() 期望 1 行，实际 0 行")
        if len(self.rows) > 1:
            raise ValueError(f"one() 期望 1 行，实际 {len(self.rows)} 行")
        return self.rows[0]

    def __iter__(self) -> Iterator:
        return iter(self.rows or [])

    def __getitem__(self, index):
        if self.rows is None:
            raise IndexError("无结果集可索引")
        return self.rows[index]

    def __len__(self) -> int:
        if self.rows is not None:
            return len(self.rows)
        return self.rowcount

    def __bool__(self) -> bool:
        if self.rows is not None:
            return bool(self.rows)
        return self.rowcount > 0

    def __repr__(self) -> str:
        if self.rows is not None:
            return f"<ExecResult {self.sql_kind} rows={len(self.rows)}>"
        if self.sql_kind == "INSERT":
            return f"<ExecResult INSERT lastrowid={self.lastrowid} rowcount={self.rowcount}>"
        return f"<ExecResult {self.sql_kind} rowcount={self.rowcount}>"
