

from typing import Literal, TypedDict


class SortDict(TypedDict):
    property: str
    order: Literal["+", "-"]