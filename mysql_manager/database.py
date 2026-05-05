import pymysql
from dbutils.pooled_db import PooledDB

from dbqk._core.database import BaseDatabase
from dbqk._core.fetch_mode import FetchMode
from dbqk.mysql_manager.exceptions import ExecError
from dbqk.mysql_manager.table import Table


class Database(BaseDatabase):
    """MySQL 数据库管理类（基于 dbutils 连接池）。"""

    table_cls = Table
    exec_error_cls = ExecError
    query_sql_heads = ("SELECT", "SHOW", "DESC", "DESCRIBE", "EXPLAIN")

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: str = "",
        charset: str = "utf8mb4",
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
            "charset": charset,
        }
        pool = PooledDB(
            creator=pymysql,
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
        cursor_cls = (
            pymysql.cursors.DictCursor
            if fetch_mode == FetchMode.DICT
            else pymysql.cursors.Cursor
        )
        return conn.cursor(cursor_cls)
