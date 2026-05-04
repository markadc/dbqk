"""测试删除数据。

直接运行：
    python _tests/pgsql/test_delete.py
"""
from _helpers import get_db, reset_table, TEST_TABLE


def main() -> None:
    """演示按条件删除，并验证空 where 会被拒绝。"""
    db = get_db()
    try:
        reset_table(db)
        users = db[TEST_TABLE]
        users.insert([
            {"name": "A", "age": 1},
            {"name": "B", "age": 2},
        ])

        r = users.delete(where={"name": "A"})
        print("删除结果:", r)
        print("  rowcount =", r.rowcount)
        assert r.rowcount == 1
        assert users.count() == 1

        # 不带 where 应该报错（防止误删全表）
        try:
            users.delete()
        except ValueError as e:
            print(f"无 where 被拒绝（符合预期）: {e}")
        else:
            raise AssertionError("delete() 没传 where 应该报错")

        print("✓ 删除测试通过")
    finally:
        db.close()


if __name__ == "__main__":
    main()
