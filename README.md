# dbqk

一个轻量级的 MySQL / PostgreSQL 连接管理 + CRUD 封装库，基于 [`DBUtils`](https://pypi.org/project/dbutils/) 连接池，底层驱动为 [`PyMySQL`](https://pypi.org/project/PyMySQL/) 和 [`psycopg2`](https://pypi.org/project/psycopg2/)。

## 特性

- 🚀 **连接池**：基于 `DBUtils.PooledDB`，自动 ping 重连，连接复用
- 🎯 **统一入口**：所有 CRUD 底层都走 `exec()` 方法
- 📦 **统一返回**：所有 SQL 执行返回 `ExecResult` 对象，通过 `.xxx` 属性访问
- 🗂️ **字典式表访问**：`db["users"]` 自动获取/创建表对象
- 🧰 **类 Django 语法糖**：`where={"age__gte": 18}` 即 `age >= 18`
- 🔄 **双格式返回**：`fetch_mode="dict"` 或 `"tuple"`
- 🛡️ **安全护栏**：`DELETE` 强制要求 `where`，参数化查询防注入
- 🐍 **现代类型注解**：Python 3.10+，使用 `X | None` 替代 `Optional`

---

## 目录结构

```
dbqk/
├── __init__.py                   # 转发入口（默认导出 MySQL 管理器）
├── mysql_manager/                # MySQL 子包
│   ├── __init__.py
│   ├── database.py               # Database 连接池主类
│   ├── table.py                  # Table 表对象
│   ├── result.py                 # ExecResult 结果统一封装
│   └── exceptions.py             # 自定义异常
├── pgsql_manager/                # PostgreSQL 子包
│   ├── __init__.py
│   ├── database.py
│   ├── table.py
│   ├── result.py
│   └── exceptions.py
├── _tests/
│   ├── mysql/                    # MySQL 测试脚本（直接运行）
│   │   ├── _helpers.py
│   │   ├── test_connect.py
│   │   ├── test_insert.py
│   │   ├── test_select.py
│   │   ├── test_update.py
│   │   ├── test_delete.py
│   │   ├── test_exec.py
│   │   └── test_table_dict.py
│   └── pgsql/                    # PostgreSQL 测试脚本
│       ├── _helpers.py
│       ├── test_connect.py
│       ├── test_insert.py
│       ├── test_select.py
│       ├── test_update.py
│       ├── test_delete.py
│       ├── test_exec.py
│       └── test_table_dict.py
├── pyproject.toml
├── README.md
├── LICENSE
└── requirements.txt
```

---

## 安装

```bash
pip install dbqk
```

或手动安装依赖：

```bash
pip install pymysql psycopg2-binary dbutils
```

> 要求 Python **3.10+**（使用了 `X | None` 联合类型语法）。
> 如果只用一种数据库，只装对应驱动即可（`pymysql` 或 `psycopg2-binary`）。

---

## 快速开始

### MySQL

```python
from dbqk.mysql_manager import Database

db = Database(
    host="127.0.0.1",
    port=3306,
    user="root",
    password="admin0",
    database="test",
)

users = db["users"]
uid = users.insert({"name": "Tom", "age": 18}).lastrowid
rows = users.select(where={"age__gte": 18}).rows
users.update({"age": 20}, where={"id": uid})
users.delete(where={"id": uid})
db.close()
```

### PostgreSQL

```python
from dbqk.pgsql_manager import Database

db = Database(
    host="127.0.0.1",
    port=5432,
    user="postgres",
    password="admin0",
    database="test",
)

users = db["users"]
uid = users.insert({"name": "Tom", "age": 18}).lastrowid
rows = users.select(where={"age__gte": 18}).rows
users.update({"age": 20}, where={"id": uid})
users.delete(where={"id": uid})
db.close()
```

---

## 核心概念

### 1. `Database`：数据库 + 连接池

**MySQL**：

```python
from dbqk.mysql_manager import Database

db = Database(
    host="127.0.0.1", port=3306,
    user="root", password="admin0", database="test",
    charset="utf8mb4",
    mincached=2, maxcached=5, maxconnections=20,
    blocking=True,
)
```

**PostgreSQL**：

```python
from dbqk.pgsql_manager import Database

db = Database(
    host="127.0.0.1", port=5432,
    user="postgres", password="admin0", database="test",
    client_encoding="UTF8",
    mincached=2, maxcached=5, maxconnections=20,
    blocking=True,
)
```

两者 API 完全一致。

**字典式访问表对象**：

```python
users = db["users"]        # 自动创建并缓存
db["orders"]               # 第二次访问返回同一对象
"users" in db              # True
del db["users"]            # 移出缓存

# 手动绑定（自定义子类时常用）
from dbqk.mysql_manager import Table
db["users"] = Table(db, "users")
```

**支持 `with` 语法自动关闭**：

```python
with Database(...) as db:
    db["users"].select()
# 退出自动 db.close()
```

---

### 2. `exec()`：所有 SQL 的统一入口

签名：

```python
db.exec(
    sql: str,
    params: list | tuple | dict | None = None,
    *,
    fetch_mode: FetchMode | str = "dict",   # "dict" / "tuple"
    many: bool = False,                      # 是否批量
    fetch: bool = True,                      # SELECT 是否取结果
) -> ExecResult
```

| SQL 类型                   | 主要属性                              |
| -------------------------- | ------------------------------------- |
| SELECT / SHOW / EXPLAIN …  | `.rows` / `.first` / `.scalar` / 迭代 |
| INSERT                     | `.lastrowid` / `.rowcount`            |
| UPDATE / DELETE            | `.rowcount`                           |

---

### 3. `ExecResult`：统一返回对象

| 属性/方法            | 含义                                       |
| -------------------- | ------------------------------------------ |
| `.rows`              | 结果集 list（仅查询语句）                  |
| `.first`             | 第一行（无数据为 `None`）                  |
| `.scalar`            | 第一行第一列的值                           |
| `.one()`             | 取唯一行（不是恰好 1 行则抛 `ValueError`） |
| `.lastrowid`         | INSERT 后的自增 id                         |
| `.rowcount`          | 受影响 / 返回行数                          |
| `.sql`               | 实际执行的 SQL（调试用）                   |
| `.params`            | 实际传入的参数                             |
| `.sql_kind`          | SQL 关键字大写：`"SELECT"`、`"INSERT"`...  |
| `len(result)`        | 行数（DML 时为 rowcount）                  |
| `bool(result)`       | 是否有行 / 是否有受影响                    |
| `for row in result:` | 迭代 `.rows`                               |
| `result[i]`          | 索引 `.rows[i]`                            |

---

### 4. `Table`：单表 CRUD 封装

| 方法                  | 返回         | 说明                                                |
| --------------------- | ------------ | --------------------------------------------------- |
| `insert(data)`        | `ExecResult` | dict → 单条；list[dict] → 批量                      |
| `select(...)`         | `ExecResult` | 支持 where/columns/order_by/limit/offset/fetch_mode |
| `find_one(where)`     | `ExecResult` | 取一行，用 `.first` 拿数据                          |
| `count(where)`        | `int`        | 直接返回整数                                        |
| `update(data, where)` | `ExecResult` | 受影响行数 `.rowcount`                              |
| `delete(where)`       | `ExecResult` | 必须传 where，否则报错                              |

**WHERE 语法糖**：

| 写法                   | 等价 SQL         |
| ---------------------- | ---------------- |
| `{"name": "Tom"}`      | `name = 'Tom'`   |
| `{"age__gt": 18}`      | `age > 18`       |
| `{"age__gte": 18}`     | `age >= 18`      |
| `{"age__lt": 18}`      | `age < 18`       |
| `{"age__lte": 18}`     | `age <= 18`      |
| `{"age__ne": 18}`      | `age != 18`      |
| `{"name__like": "T%"}` | `name LIKE 'T%'` |

多个键之间用 `AND` 连接。

---

## Demo & 示例输出

> 测试表结构：
>
> **MySQL**：
> ```sql
> CREATE TABLE `test` (
>   `id`   INT AUTO_INCREMENT PRIMARY KEY,
>   `name` VARCHAR(64) NOT NULL,
>   `age`  INT NOT NULL DEFAULT 0
> );
> ```
>
> **PostgreSQL**：
> ```sql
> CREATE TABLE "test" (
>   "id"   SERIAL PRIMARY KEY,
>   "name" VARCHAR(64) NOT NULL,
>   "age"  INT NOT NULL DEFAULT 0
> );
> ```
>
> 以下所有 Demo 的 Table API 在 MySQL 和 PostgreSQL 中**完全一致**。

### Demo 1：连接

```python
db = Database(host="127.0.0.1", user="root", password="admin0", database="test")
result = db.exec("SELECT 1 AS ok")

print(result)          # <ExecResult SELECT rows=1>
print(result.rows)     # [{'ok': 1}]
print(result.first)    # {'ok': 1}
print(result.scalar)   # 1
```

---

### Demo 2：插入

```python
users = db["test"]

# 单条插入
r1 = users.insert({"name": "Tom", "age": 18})
print(r1)              # <ExecResult INSERT lastrowid=1 rowcount=1>
print(r1.lastrowid)    # 1
print(r1.rowcount)     # 1

# 批量插入
r2 = users.insert([
    {"name": "A", "age": 1},
    {"name": "B", "age": 2},
    {"name": "C", "age": 3},
])
print(r2)              # <ExecResult INSERT lastrowid=4 rowcount=3>
print(r2.rowcount)     # 3

print(users.count())   # 4
```

---

### Demo 3：查询

```python
users = db["test"]
users.insert([
    {"name": "A", "age": 10},
    {"name": "B", "age": 20},
    {"name": "C", "age": 30},
])

# 1) 全部查询（默认 dict）
r = users.select()
print(r.rows)
# [{'id': 1, 'name': 'A', 'age': 10},
#  {'id': 2, 'name': 'B', 'age': 20},
#  {'id': 3, 'name': 'C', 'age': 30}]

# 2) 直接迭代
for row in r:
    print(row["name"], row["age"])
# A 10
# B 20
# C 30

# 3) 条件 + 排序 + 限制
r = users.select(
    where={"age__gte": 20},
    columns=["name", "age"],
    order_by="age DESC",
    limit=10,
)
print(r.rows)
# [{'name': 'C', 'age': 30}, {'name': 'B', 'age': 20}]

# 4) 模糊查询
r = users.select(where={"name__like": "A%"})
print(r.rows)
# [{'id': 1, 'name': 'A', 'age': 10}]

# 5) tuple 模式
r = users.select(fetch_mode="tuple")
print(r.first)
# (1, 'A', 10)

# 6) find_one
r = users.find_one(where={"name": "B"})
print(r.first)
# {'id': 2, 'name': 'B', 'age': 20}

# 不存在时 first 是 None
r = users.find_one(where={"name": "NoBody"})
print(r.first)
# None

# 7) count（直接返回 int）
print(users.count())                       # 3
print(users.count(where={"age__gt": 15}))  # 2

# 8) scalar 取第一行第一列
total = db.exec("SELECT COUNT(*) FROM test").scalar
print(total)                               # 3
```

---

### Demo 4：更新

```python
users = db["test"]
users.insert({"name": "Tom", "age": 18})

r = users.update({"age": 20}, where={"name": "Tom"})
print(r)               # <ExecResult UPDATE rowcount=1>
print(r.rowcount)      # 1

print(users.find_one(where={"name": "Tom"}).first)
# {'id': 1, 'name': 'Tom', 'age': 20}
```

---

### Demo 5：删除

```python
users = db["test"]
users.insert([{"name": "A", "age": 1}, {"name": "B", "age": 2}])

r = users.delete(where={"name": "A"})
print(r.rowcount)      # 1
print(users.count())   # 1

# 安全护栏：不传 where 会报错
users.delete()
# ValueError: 拒绝执行无 WHERE 的 DELETE，请显式传入 where={...}
```

---

### Demo 6：底层 `exec` 直接执行原生 SQL

```python
# INSERT
r = db.exec(
    "INSERT INTO test (name, age) VALUES (%s, %s)",
    ("Tom", 18),
)
print(r.lastrowid, r.rowcount)             # 1 1

# 批量 INSERT
r = db.exec(
    "INSERT INTO test (name, age) VALUES (%s, %s)",
    [("A", 1), ("B", 2), ("C", 3)],
    many=True,
)
print(r.rowcount)                          # 3

# SELECT dict
r = db.exec("SELECT * FROM test", fetch_mode="dict")
print(r.first)
# {'id': 1, 'name': 'Tom', 'age': 18}

# SELECT tuple
r = db.exec("SELECT * FROM test", fetch_mode="tuple")
print(r.first)
# (1, 'Tom', 18)

# 标量
print(db.exec("SELECT COUNT(*) FROM test").scalar)   # 4

# UPDATE / DELETE
print(db.exec("UPDATE test SET age=99 WHERE name=%s", ("Tom",)).rowcount)  # 1
print(db.exec("DELETE FROM test WHERE name=%s", ("Tom",)).rowcount)        # 1

# bool 判断
r = db.exec("SELECT * FROM test WHERE name=%s", ("NoBody",))
print(bool(r))                             # False
```

---

### Demo 7：表对象字典式访问

```python
from dbqk.mysql_manager import Table

# 自动创建并缓存
t1 = db["test"]
t2 = db["test"]
print(t1 is t2)             # True

# 手动绑定（用于自定义子类）
custom = Table(db, "placeholder")
db["test"] = custom
print(db["test"] is custom) # True
print(custom.name)          # "test"（赋值时同步表名）

# in / del
print("test" in db)         # True
del db["test"]
print("test" in db)         # False

# 再次访问会重新创建
db["test"]
```

---

## 异常

```python
# MySQL
from dbqk.mysql_manager import (
    MySQLManagerError,    # 基础异常
    ExecError,            # SQL 执行失败（自动 rollback）
    TableNotFoundError,   # 预留
)

# PostgreSQL
from dbqk.pgsql_manager import (
    PgsqlManagerError,
    ExecError,
    TableNotFoundError,
)

try:
    db.exec("SELECT * FROM not_exists")
except ExecError as e:
    print("执行出错:", e)
```

---

## 测试

测试不依赖 pytest，每个文件一个功能，直接 `python` 运行。

### MySQL 测试

```bash
cd dbqk/_tests/mysql

# 编辑 _helpers.py 配置连接信息

python test_connect.py
python test_insert.py
python test_select.py
python test_update.py
python test_delete.py
python test_exec.py
python test_table_dict.py
```

### PostgreSQL 测试

```bash
cd dbqk/_tests/pgsql

# 编辑 _helpers.py 配置连接信息

python test_connect.py
python test_insert.py
python test_select.py
python test_update.py
python test_delete.py
python test_exec.py
python test_table_dict.py
```

每个脚本运行结束会打印 `✓ xxx 测试通过`。

---

## 设计要点速查

| 设计         | MySQL 实现                                              | PostgreSQL 实现                                                |
| ------------ | ------------------------------------------------------- | -------------------------------------------------------------- |
| 连接池       | `PooledDB(creator=pymysql, ping=1, ...)`                | `PooledDB(creator=psycopg2, ping=1, ...)`                      |
| 自动事务     | `_cursor` 上下文管理器：异常 rollback、正常 commit       | 同左                                                           |
| 连接归还     | `conn.close()` 实际归还到池而不是真关闭                   | 同左                                                           |
| dict / tuple | `pymysql.cursors.DictCursor` / `Cursor`                 | `psycopg2.extras.RealDictCursor` / 普通 Cursor                 |
| SQL 注入防护 | `%s` 参数化 + 反引号标识符                               | `%s` 参数化 + 双引号标识符                                      |
| 自增 id      | `cursor.lastrowid`（自动）                               | `lastrowid == 0` 时自动 `SELECT lastval()`                      |
| 表对象缓存   | `Database._tables: dict[str, Table]`                    | 同左                                                           |
| 删除护栏     | 空 where 直接抛 `ValueError`                            | 同左                                                           |
| 统一返回     | 所有 SQL 都封装为 `ExecResult`                           | 同左                                                           |

---

## License

MIT
