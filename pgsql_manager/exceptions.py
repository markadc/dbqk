class PgsqlManagerError(Exception):
    """PostgreSQL 管理器基础异常类。"""


class TableNotFoundError(PgsqlManagerError):
    """表不存在异常。"""


class ExecError(PgsqlManagerError):
    """SQL 执行异常。"""
