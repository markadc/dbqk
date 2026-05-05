"""测试公用：数据库连接配置 + 建表/清表工具。"""

import sys
from pathlib import Path

# 把项目根目录加到 sys.path，方便直接 python _tests/xxx.py 运行
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from dbqk.pgsql_manager import Database  # noqa: E402


TEST_DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "user": "wangtuo",
    "password": "admin0",
    "database": "test",
}

TEST_TABLE = "test"


def get_db() -> Database:
    """创建一个 Database 实例。

    Returns:
        新建的 Database 连接池实例。
    """
    return Database(**TEST_DB_CONFIG, mincached=1, maxconnections=5)


def reset_table(db: Database) -> None:
    """重建测试表，保证每个脚本起始状态干净。

    Args:
        db: Database 实例。
    """
    db.exec(f'DROP TABLE IF EXISTS "{TEST_TABLE}"', fetch=False)
    db.exec(
        f"""
        CREATE TABLE "{TEST_TABLE}" (
            "id"   SERIAL PRIMARY KEY,
            "name" VARCHAR(64) NOT NULL,
            "age"  INT NOT NULL DEFAULT 0
        )
        """,
        fetch=False,
    )
