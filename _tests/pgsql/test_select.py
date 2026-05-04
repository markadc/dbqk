"""测试查询数据。

直接运行：
    python _tests/pgsql/test_select.py
"""
from _helpers import get_db, reset_table, TEST_TABLE


def main() -> None:
    """演示 select / find_one 以及 dict 与 tuple 两种返回格式。"""
    db = get_db()
    try:
        reset_table(db)
        users = db[TEST_TABLE]
        users.insert([
            {"name": "A", "age": 10},
            {"name": "B", "age": 20},
            {"name": "C", "age": 30},
        ])

        # 全部查询（dict 模式）
        r = users.select()
        print("全部记录:", r)
        print("  rows   =", r.rows)
        print("  len(r) =", len(r))
        assert len(r) == 3
        assert isinstance(r.first, dict)

        # 迭代行
        print("迭代:")
        for row in r:
            print("  -", row)

        # 条件查询 + 操作符语法糖
        r = users.select(where={"age__gte": 20}, order_by='"age" DESC')
        print("age>=20:", r.rows)
        assert len(r) == 2

        # tuple 返回
        r = users.select(fetch_mode="tuple")
        print("tuple 模式 first =", r.first)
        assert isinstance(r.first, tuple)

        # find_one：返回 ExecResult，用 .first 取行
        r = users.find_one(where={"name": "B"})
        print("find_one(name=B).first =", r.first)
        assert r.first["age"] == 20

        # 找不到时 .first 为 None
        r = users.find_one(where={"name": "NotExist"})
        print("不存在时 first =", r.first)
        assert r.first is None

        print("✓ 查询测试通过")
    finally:
        db.close()


if __name__ == "__main__":
    main()
