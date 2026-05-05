import psycopg2
import psycopg2.extras
from dbutils.pooled_db import PooledDB

from dbqk._core.database import BaseDatabase
from dbqk._core.fetch_mode import FetchMode
from dbqk.pgsql_manager.exceptions import ExecError
from dbqk.pgsql_manager.table import Table


class Database(BaseDatabase):
    """PostgreSQL 数据库管理类（基于 dbutils 连接池）。"""

    table_cls = Table
    exec_error_cls = ExecError
    query_sql_heads = ("SELECT", "SHOW", "EXPLAIN", "WITH", "TABLE")

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5432,
        user: str = "postgres",
        password: str = "",
        database: str = "",
        client_encoding: str = "UTF8",
        mincached: int = 2,
        maxcached: int = 5,
        maxconnections: int = 20,
        blocking: bool = True,
        **kwargs,
    ):
        self._config = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
            "client_encoding": client_encoding,
        }
        pool = PooledDB(
            creator=psycopg2,
            mincached=mincached,
            maxcached=maxcached,
            maxconnections=maxconnections,
            blocking=blocking,
            ping=1,
            **self._config,
            **kwargs,
        )
        self._init_core(pool)

    def _make_cursor(self, conn, fetch_mode: FetchMode):
        cursor_factory = (
            psycopg2.extras.RealDictCursor
            if fetch_mode == FetchMode.DICT
            else None
        )
        return conn.cursor(cursor_factory=cursor_factory)

    def _execute_many(self, cursor, sql: str, params) -> int:
        total_rowcount = 0
        for p in (params or []):
            cursor.execute(sql, p)
            total_rowcount += cursor.rowcount
        return total_rowcount

    def _get_lastrowid(self, cursor, sql_head: str):
        lastrowid = cursor.lastrowid
        if sql_head == "INSERT" and lastrowid == 0:
            try:
                cursor.execute("SELECT lastval()")
                row = cursor.fetchone()
                if row is not None:
                    lastrowid = next(iter(row.values())) if isinstance(row, dict) else row[0]
            except Exception:
                pass
        return lastrowid
