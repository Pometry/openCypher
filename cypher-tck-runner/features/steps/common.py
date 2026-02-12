
from dataclasses import dataclass
from typing import Any


@dataclass
class ResultTable: 
    columns: list[str] 
    rows: list[list[Any]]