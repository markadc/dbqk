"""测试更新数据。

直接运行：
    python _tests/test_update.py
"""
from _helpers import get_db, reset_table, TEST_TABLE


def main() -> None:
    """演示按条件更新数据，并通过 ExecResult.rowcount 验证。"""
    db = get_db()
    try:
        reset_table(db)
        users = db[TEST_TABLE]
        users.insert({"name": "Tom", "age": 18})

        r = users.update({"age": 20}, where={"name": "Tom"})
        print("更新结果:", r)
        print("  rowcount =", r.rowcount)
        assert r.rowcount == 1

        row = users.find_one(where={"name": "Tom"}).first
        print("更新后:", row)
        assert row["age"] == 20

        print("✓ 更新测试通过")
    finally:
        db.close()


if __name__ == "__main__":
    main()
