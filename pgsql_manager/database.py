import psycopg2
import psycopg2.extras
from dbutils.pooled_db import PooledDB
from contextlib import contextmanager
from enum import Enum

from dbqk.pgsql_manager.exceptions import ExecError
from dbqk.pgsql_manager.result import ExecResult
from dbqk.pgsql_manager.table import Table


class FetchMode(Enum):
    """查询结果返回格式。

    Attributes:
        DICT: 每行返回为 dict。
        TUPLE: 每行返回为 tuple。
    """

    DICT = "dict"
    TUPLE = "tuple"


class Database:
    """PostgreSQL 数据库管理类（基于 dbutils 连接池）。

    所有 CRUD 操作底层都通过 ``exec`` 方法执行，统一返回 ``ExecResult``。
    表对象通过字典式访问获得：``db["users"]`` 自动创建并缓存对应的 ``Table``。

    Example:
        >>> db = Database(host="127.0.0.1", user="postgres",
        ...               password="xxx", database="test")
        >>> r = db.exec("SELECT * FROM users")
        >>> r.rows           # 结果集
        >>> r.first          # 第一行
        >>> r.rowcount       # 行数
        >>> users = db["users"]
        >>> users.insert({"name": "Tom", "age": 18}).lastrowid
    """

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
        """初始化数据库连接池。

        Args:
            host: PostgreSQL 主机地址。
            port: PostgreSQL 端口。
            user: 用户名。
            password: 密码。
            database: 数据库名。
            client_encoding: 客户端编码。
            mincached: 连接池启动时创建的最小空闲连接数。
            maxcached: 连接池最多保留的空闲连接数。
            maxconnections: 连接池允许的最大连接数。
            blocking: 连接数达上限时是否阻塞等待。
            **kwargs: 其他传递给底层 psycopg2 的参数。
        """
        self._config = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
            "client_encoding": client_encoding,
        }
        self._pool = PooledDB(
            creator=psycopg2,
            mincached=mincached,
            maxcached=maxcached,
            maxconnections=maxconnections,
            blocking=blocking,
            ping=1,
            **self._config,
            **kwargs,
        )
        self._tables: dict[str, Table] = {}

    @contextmanager
    def _cursor(self, fetch_mode: FetchMode = FetchMode.DICT):
        """获取连接和游标的上下文管理器。

        自动从连接池取连接、提交事务、回滚异常，并在结束时归还连接到池。

        Args:
            fetch_mode: 决定使用 RealDictCursor 还是普通 Cursor。

        Yields:
            tuple: ``(connection, cursor)`` 二元组。

        Raises:
            ExecError: SQL 执行出现异常时抛出。
        """
        conn = self._pool.connection()
        cursor_factory = (
            psycopg2.extras.RealDictCursor
            if fetch_mode == FetchMode.DICT
            else None
        )
        cursor = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield conn, cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise ExecError(f"SQL 执行失败: {e}") from e
        finally:
            cursor.close()
            conn.close()

    def exec(
        self,
        sql: str,
        params: list | tuple | dict | None = None,
        *,
        fetch_mode: FetchMode | str = FetchMode.DICT,
        many: bool = False,
        fetch: bool = True,
    ) -> ExecResult:
        """执行 SQL 的统一入口（CRUD 底层都调用此方法）。

        Args:
            sql: SQL 语句，参数占位符使用 ``%s``。
            params: 参数。普通模式下传单条参数（list/tuple/dict），
                ``many=True`` 时传参数列表。
            fetch_mode: 返回格式，``"dict"`` 或 ``"tuple"``，
                也可传入 ``FetchMode`` 枚举。
            many: 是否调用 ``executemany`` 进行批量执行。
            fetch: SELECT 类语句是否取出结果集。

        Returns:
            ExecResult: 统一封装的结果对象，可通过属性访问：

            * ``.rows`` — 结果集（仅 SELECT 类）。
            * ``.lastrowid`` — 自增 id（INSERT）。
            * ``.rowcount`` — 受影响 / 返回的行数。
            * ``.first`` / ``.scalar`` / ``.one()`` 便捷访问。

        Raises:
            ExecError: SQL 执行失败时抛出。
        """
        if isinstance(fetch_mode, str):
            fetch_mode = FetchMode(fetch_mode.lower())

        sql_head = sql.strip().split(maxsplit=1)[0].upper()

        with self._cursor(fetch_mode) as (conn, cursor):
            if many:
                total_rowcount = 0
                for p in (params or []):
                    cursor.execute(sql, p)
                    total_rowcount += cursor.rowcount
                rowcount = total_rowcount
            else:
                cursor.execute(sql, params or ())
                rowcount = cursor.rowcount

            rows = None
            if sql_head in ("SELECT", "SHOW", "EXPLAIN", "WITH", "TABLE") and fetch:
                rows = list(cursor.fetchall())

            lastrowid = cursor.lastrowid
            # psycopg2 的 lastrowid 返回 OID（无 OID 表永远是 0），
            # 需通过 lastval() 获取 SERIAL/IDENTITY 自增值。
            if sql_head == "INSERT" and lastrowid == 0:
                try:
                    cursor.execute("SELECT lastval()")
                    row = cursor.fetchone()
                    if row is not None:
                        lastrowid = next(iter(row.values())) if isinstance(row, dict) else row[0]
                except Exception:
                    pass

            return ExecResult(
                rows=rows,
                lastrowid=lastrowid,
                rowcount=rowcount,
                sql=sql,
                params=params,
                sql_kind=sql_head,
            )

    def __getitem__(self, table_name: str) -> Table:
        if table_name not in self._tables:
            self._tables[table_name] = Table(self, table_name)
        return self._tables[table_name]

    def __setitem__(self, table_name: str, table: Table):
        if not isinstance(table, Table):
            raise TypeError("必须是 Table 对象")
        table._db = self
        table._name = table_name
        self._tables[table_name] = table

    def __contains__(self, table_name: str) -> bool:
        return table_name in self._tables

    def __delitem__(self, table_name: str):
        self._tables.pop(table_name, None)

    def close(self):
        """关闭连接池，释放所有连接资源。"""
        self._pool.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
