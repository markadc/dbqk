"""测试 Database 字典式访问表对象。

直接运行：
    python _tests/test_table_dict.py
"""
from _helpers import get_db, TEST_TABLE
from dbqk.mysql_manager import Table


def main() -> None:
    """演示 ``db[name]`` 自动创建、缓存、手动绑定、in/del 操作。"""
    db = get_db()
    try:
        # 自动创建并缓存
        t1 = db[TEST_TABLE]
        t2 = db[TEST_TABLE]
        print(f"t1 is t2 ? {t1 is t2}")
        assert isinstance(t1, Table) and t1 is t2

        # 手动绑定
        custom = Table(db, "placeholder")
        db[TEST_TABLE] = custom
        print(f"绑定后 db[{TEST_TABLE}] is custom ? {db[TEST_TABLE] is custom}")
        assert db[TEST_TABLE] is custom
        assert custom.name == TEST_TABLE

        # in / del
        assert TEST_TABLE in db
        del db[TEST_TABLE]
        assert TEST_TABLE not in db
        print("✓ 字典访问测试通过")
    finally:
        db.close()


if __name__ == "__main__":
    main()
