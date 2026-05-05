import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dbqk._core import BaseDatabase, BaseTable, ExecResult as CoreExecResult
from dbqk.mysql_manager import Database as MySQLDatabase
from dbqk.mysql_manager import ExecResult as MySQLExecResult
from dbqk.mysql_manager import Table as MySQLTable
from dbqk.pgsql_manager import Database as PgSQLDatabase
from dbqk.pgsql_manager import ExecResult as PgSQLExecResult
from dbqk.pgsql_manager import Table as PgSQLTable


class CaptureDB:
    def __init__(self):
        self.calls = []

    def exec(self, sql, params=None, **kwargs):
        self.calls.append((sql, params, kwargs))
        if sql.startswith("SELECT COUNT"):
            return CoreExecResult(rows=[{"cnt": 3}], rowcount=1, sql=sql, params=params, sql_kind="SELECT")
        return CoreExecResult(rowcount=1, sql=sql, params=params, sql_kind=sql.split()[0].upper())


class DummyTable(BaseTable):
    identifier_quote = "`"


class DummyPool:
    def close(self):
        self.closed = True


class DummyDatabase(BaseDatabase):
    table_cls = DummyTable

    def __init__(self):
        self._init_core(DummyPool())

    def _make_cursor(self, conn, fetch_mode):
        raise NotImplementedError


class FakeCursor:
    def __init__(self):
        self.rowcount = 0
        self.lastrowid = 0
        self.execute_calls = []
        self.executemany_calls = []
        self.fetchone_row = {"lastval": 9}

    def execute(self, sql, params=None):
        self.execute_calls.append((sql, params))
        self.rowcount = 1

    def executemany(self, sql, params=None):
        self.executemany_calls.append((sql, params))
        self.rowcount = len(params or [])

    def fetchone(self):
        return self.fetchone_row


def check_public_import_paths_stay_compatible():
    assert MySQLExecResult is CoreExecResult
    assert PgSQLExecResult is CoreExecResult
    assert issubclass(MySQLDatabase, BaseDatabase)
    assert issubclass(PgSQLDatabase, BaseDatabase)
    assert issubclass(MySQLTable, BaseTable)
    assert issubclass(PgSQLTable, BaseTable)


def check_exec_result_behavior_is_shared():
    result = CoreExecResult(rows=[{"id": 1}, {"id": 2}], rowcount=2, sql_kind="SELECT")
    assert result.first == {"id": 1}
    assert result.scalar == 1
    assert len(result) == 2
    assert result
    assert list(result) == [{"id": 1}, {"id": 2}]
    assert "rows=2" in repr(result)


def check_table_sql_uses_backend_identifier_quotes():
    mysql_db = CaptureDB()
    MySQLTable(mysql_db, "users").select(
        where={"age__gte": 18},
        columns=["id", "name"],
        order_by="age DESC",
        limit=10,
        offset=5,
    )
    assert mysql_db.calls[-1] == (
        "SELECT `id`, `name` FROM `users` WHERE `age` >= %s ORDER BY age DESC LIMIT 10 OFFSET 5",
        [18],
        {"fetch_mode": "dict"},
    )

    pgsql_db = CaptureDB()
    PgSQLTable(pgsql_db, "users").insert({"name": "Tom", "age": 18})
    assert pgsql_db.calls[-1] == (
        'INSERT INTO "users" ("name", "age") VALUES (%s, %s)',
        ["Tom", 18],
        {},
    )


def check_table_cache_behavior_is_shared():
    db = DummyDatabase()
    first = db["users"]
    second = db["users"]
    assert first is second
    assert "users" in db

    custom = DummyTable(db, "placeholder")
    db["users"] = custom
    assert db["users"] is custom
    assert custom.name == "users"

    del db["users"]
    assert "users" not in db


def check_many_execution_keeps_backend_differences():
    mysql_cursor = FakeCursor()
    mysql_db = object.__new__(MySQLDatabase)
    rowcount = mysql_db._execute_many(mysql_cursor, "INSERT", [(1,), (2,)])
    assert rowcount == 2
    assert mysql_cursor.executemany_calls == [("INSERT", [(1,), (2,)])]
    assert mysql_cursor.execute_calls == []

    pgsql_cursor = FakeCursor()
    pgsql_db = object.__new__(PgSQLDatabase)
    rowcount = pgsql_db._execute_many(pgsql_cursor, "INSERT", [(1,), (2,)])
    assert rowcount == 2
    assert pgsql_cursor.execute_calls == [("INSERT", (1,)), ("INSERT", (2,))]
    assert pgsql_cursor.executemany_calls == []


def check_pgsql_lastrowid_fallback_is_preserved():
    cursor = FakeCursor()
    pgsql_db = object.__new__(PgSQLDatabase)
    assert pgsql_db._get_lastrowid(cursor, "INSERT") == 9
    assert cursor.execute_calls == [("SELECT lastval()", None)]


def main():
    checks = [
        ("公开导入路径兼容", check_public_import_paths_stay_compatible),
        ("ExecResult 共享行为", check_exec_result_behavior_is_shared),
        ("Table SQL 引号差异", check_table_sql_uses_backend_identifier_quotes),
        ("表缓存共享行为", check_table_cache_behavior_is_shared),
        ("many=True 后端差异", check_many_execution_keeps_backend_differences),
        ("PostgreSQL lastrowid 兜底", check_pgsql_lastrowid_fallback_is_preserved),
    ]
    for name, check in checks:
        check()
        print(f"✓ {name}")
    print("✓ 全部结构检查通过")


if __name__ == "__main__":
    main()
