"""测试底层 exec 直接执行原生 SQL，并展示 ExecResult 各种属性。

直接运行：
    python _tests/test_exec.py
"""
from _helpers import get_db, reset_table, TEST_TABLE


def main() -> None:
    """直接调用 ``db.exec``，观察 ExecResult 的统一属性。"""
    db = get_db()
    try:
        reset_table(db)

        # INSERT
        r = db.exec(
            f"INSERT INTO `{TEST_TABLE}` (name, age) VALUES (%s, %s)",
            ("Tom", 18),
        )
        print("INSERT:", r)
        print("  sql_kind  =", r.sql_kind)
        print("  lastrowid =", r.lastrowid)
        print("  rowcount  =", r.rowcount)
        assert r.lastrowid > 0
        assert r.rowcount == 1

        # 批量 INSERT
        r = db.exec(
            f"INSERT INTO `{TEST_TABLE}` (name, age) VALUES (%s, %s)",
            [("A", 1), ("B", 2), ("C", 3)],
            many=True,
        )
        print("INSERT many:", r)
        assert r.rowcount == 3

        # SELECT dict
        r = db.exec(f"SELECT * FROM `{TEST_TABLE}`", fetch_mode="dict")
        print("SELECT dict:", r)
        print("  rows  =", r.rows)
        print("  first =", r.first)
        print("  len   =", len(r))
        assert isinstance(r.first, dict)

        # SELECT tuple
        r = db.exec(f"SELECT * FROM `{TEST_TABLE}`", fetch_mode="tuple")
        print("SELECT tuple first =", r.first)
        assert isinstance(r.first, tuple)

        # SELECT scalar
        r = db.exec(f"SELECT COUNT(*) AS cnt FROM `{TEST_TABLE}`")
        print("COUNT scalar =", r.scalar)
        assert r.scalar == 4

        # UPDATE
        r = db.exec(
            f"UPDATE `{TEST_TABLE}` SET age = %s WHERE name = %s",
            (99, "Tom"),
        )
        print("UPDATE rowcount =", r.rowcount)
        assert r.rowcount == 1

        # DELETE
        r = db.exec(f"DELETE FROM `{TEST_TABLE}` WHERE name = %s", ("Tom",))
        print("DELETE rowcount =", r.rowcount)
        assert r.rowcount == 1

        # bool 测试
        r = db.exec(f"SELECT * FROM `{TEST_TABLE}` WHERE name = %s", ("NoBody",))
        print("空结果 bool =", bool(r))
        assert not r

        print("✓ exec 测试通过")
    finally:
        db.close()


if __name__ == "__main__":
    main()
