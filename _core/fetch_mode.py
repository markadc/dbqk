from enum import Enum


class FetchMode(Enum):
    """查询结果返回格式。"""

    DICT = "dict"
    TUPLE = "tuple"
