from typing import Any, Iterator


class ExecResult:
    """SQL 执行结果的统一封装对象。"""

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
