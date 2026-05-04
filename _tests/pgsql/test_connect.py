"""测试连接：能 ping 通即视为通过。

直接运行：
    python _tests/pgsql/test_connect.py
"""
from _helpers import get_db


def main() -> None:
    """连接数据库并执行 ``SELECT 1`` 验证连接池工作正常。"""
    db = get_db()
    try:
        result = db.exec("SELECT 1 AS ok")
        print("结果对象:", result)
        print("rows  =", result.rows)
        print("first =", result.first)
        print("scalar=", result.scalar)
        assert result.scalar == 1
        print("✓ 连接成功")
    finally:
        db.close()


if __name__ == "__main__":
    main()
