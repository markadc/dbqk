from dbqk._core.table import BaseTable


class Table(BaseTable):
    """MySQL 单表 CRUD 封装。"""

    identifier_quote = "`"
