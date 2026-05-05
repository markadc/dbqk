from dbqk._core.table import BaseTable


class Table(BaseTable):
    """PostgreSQL 单表 CRUD 封装。"""

    identifier_quote = '"'
