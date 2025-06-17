from typing import List, Optional, Union

class Filter:
    def __init__(self, expr: str = ""):
        self.expr = expr

    def eq(self, field: str, value) -> "Filter":
        val = f"'{value}'" if isinstance(value, str) else value
        return Filter(f"{field} eq {val}")

    def gt(self, field: str, value) -> "Filter":
        return Filter(f"{field} gt {value}")

    def lt(self, field: str, value) -> "Filter":
        return Filter(f"{field} lt {value}")

    def contains(self, field: str, substring: str) -> "Filter":
        return Filter(f"contains({field},'{substring}')")

    def and_(self, other: "Filter") -> "Filter":
        return Filter(f"({self.expr}) and ({other.expr})")

    def or_(self, other: "Filter") -> "Filter":
        return Filter(f"({self.expr}) or ({other.expr})")

    def build(self) -> str:
        return self.expr

class QueryOptions:
    def __init__(
        self,
        filter: Union[str, Filter, None] = None,
        expand: Optional[List[str]] = None,
        select: Optional[List[str]] = None,
        top: Optional[int] = None,
        skip: Optional[int] = None,
    ):
        self.filter = filter
        self.expand = expand
        self.select = select
        self.top = top
        self.skip = skip

    def to_params(self) -> dict:
        params = {}
        if self.filter:
            params["$filter"] = (
                self.filter.build()
                if isinstance(self.filter, Filter)
                else self.filter
            )
        if self.expand:
            params["$expand"] = ",".join(self.expand)
        if self.select:
            params["$select"] = ",".join(self.select)
        if self.top is not None:
            params["$top"] = str(self.top)
        if self.skip is not None:
            params["$skip"] = str(self.skip)
        return params

