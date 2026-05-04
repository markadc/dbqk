# 测试说明

直接运行 python 脚本即可。每个文件只测一个功能。

## 运行前

```bash
pip install -r requirements.txt
```

并保证 `_helpers.py` 中 `TEST_DB_CONFIG` 指向的 MySQL 库可用。

## 文件清单

| 文件                 | 功能                                        |
| -------------------- | ------------------------------------------- |
| `test_connect.py`    | 测试连接（SELECT 1）                        |
| `test_insert.py`     | 测试插入（单条 + 批量）                     |
| `test_select.py`     | 测试查询（dict/tuple/where/find_one/count） |
| `test_update.py`     | 测试更新                                    |
| `test_delete.py`     | 测试删除                                    |
| `test_exec.py`       | 测试底层 exec 原生 SQL                      |
| `test_table_dict.py` | 测试 `db[name]` 字典式访问                  |

## 运行

```bash
python _tests/mysql/test_connect.py
python _tests/mysql/test_insert.py
python _tests/mysql/test_select.py
python _tests/mysql/test_update.py
python _tests/mysql/test_delete.py
python _tests/mysql/test_exec.py
python _tests/mysql/test_table_dict.py
```
