class MySQLManagerError(Exception):
    """MySQL 管理器基础异常类。"""


class TableNotFoundError(MySQLManagerError):
    """表不存在异常。"""


class ExecError(MySQLManagerError):
    """SQL 执行异常。"""
