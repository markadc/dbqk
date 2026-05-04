"""测试插入数据。

直接运行：
    python _tests/test_insert.py
"""
from _helpers import get_db, reset_table, TEST_TABLE


def main() -> None:
    """演示单条插入和批量插入，验证 ExecResult 属性。"""
    db = get_db()
    try:
        reset_table(db)
        users = db[TEST_TABLE]

        # 单条插入：用 .lastrowid 拿到自增 id
        r1 = users.insert({"name": "Tom", "age": 18})
        print("单条:", r1)
        print("  lastrowid =", r1.lastrowid)
        print("  rowcount  =", r1.rowcount)
        assert r1.lastrowid > 0
        assert r1.rowcount == 1

        # 批量插入：用 .rowcount 拿到受影响行数
        r2 = users.insert([
            {"name": "A", "age": 1},
            {"name": "B", "age": 2},
            {"name": "C", "age": 3},
        ])
        print("批量:", r2)
        print("  rowcount  =", r2.rowcount)
        assert r2.rowcount == 3

        print("当前总记录数 =", users.count())
        assert users.count() == 4
        print("✓ 插入测试通过")
    finally:
        db.close()


if __name__ == "__main__":
    main()
