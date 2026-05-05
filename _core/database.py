from contextlib import contextmanager

from dbqk._core.fetch_mode import FetchMode
from dbqk._core.result import ExecResult


class BaseDatabase:
    """数据库连接池和执行流程公共实现。"""

    table_cls = None
    exec_error_cls = Exception
    query_sql_heads = ("SELECT", "SHOW", "DESC", "DESCRIBE", "EXPLAIN")

    def _init_core(self, pool):
        self._pool = pool
        self._tables = {}

    @contextmanager
    def _cursor(self, fetch_mode: FetchMode = FetchMode.DICT):
        conn = self._pool.connection()
        cursor = self._make_cursor(conn, fetch_mode)
        try:
            yield conn, cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise self.exec_error_cls(f"SQL 执行失败: {e}") from e
        finally:
            cursor.close()
            conn.close()

    def _make_cursor(self, conn, fetch_mode: FetchMode):
        raise NotImplementedError

    def _execute_many(self, cursor, sql: str, params) -> int:
        cursor.executemany(sql, params or [])
        return cursor.rowcount

    def _execute_one(self, cursor, sql: str, params) -> int:
        cursor.execute(sql, params or ())
        return cursor.rowcount

    def _get_lastrowid(self, cursor, sql_head: str):
        return cursor.lastrowid

    def exec(
        self,
        sql: str,
        params: list | tuple | dict | None = None,
        *,
        fetch_mode: FetchMode | str = FetchMode.DICT,
        many: bool = False,
        fetch: bool = True,
    ) -> ExecResult:
        if isinstance(fetch_mode, str):
            fetch_mode = FetchMode(fetch_mode.lower())

        sql_head = sql.strip().split(maxsplit=1)[0].upper()

        with self._cursor(fetch_mode) as (conn, cursor):
            if many:
                rowcount = self._execute_many(cursor, sql, params)
            else:
                rowcount = self._execute_one(cursor, sql, params)

            rows = None
            if sql_head in self.query_sql_heads and fetch:
                rows = list(cursor.fetchall())

            return ExecResult(
                rows=rows,
                lastrowid=self._get_lastrowid(cursor, sql_head),
                rowcount=rowcount,
                sql=sql,
                params=params,
                sql_kind=sql_head,
            )

    def __getitem__(self, table_name: str):
        if table_name not in self._tables:
            self._tables[table_name] = self.table_cls(self, table_name)
        return self._tables[table_name]

    def __setitem__(self, table_name: str, table):
        if not isinstance(table, self.table_cls):
            raise TypeError("必须是 Table 对象")
        table._db = self
        table._name = table_name
        self._tables[table_name] = table

    def __contains__(self, table_name: str) -> bool:
        return table_name in self._tables

    def __delitem__(self, table_name: str):
        self._tables.pop(table_name, None)

    def close(self):
        self._pool.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
