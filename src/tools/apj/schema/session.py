from datetime import date
from typing import Annotated, Literal, Optional, Union
from pydantic import BaseModel, BeforeValidator
from .enums import SessionStatus


def _coerce_date(v: object) -> Union[date, None]:
    """Accept date, str ('2026-02-25'), or None."""
    if v is None:
        return None
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        return date.fromisoformat(v)
    return v  # let Pydantic handle unexpected types


class Session(BaseModel):
    id: str                               # S001, S012
    type: Literal["session"] = "session"
    date: Annotated[Union[date, None], BeforeValidator(_coerce_date)] = None
    status: SessionStatus
    test_floor: Union[int, None] = None
    focus: str = ""
    tasks_planned: list[str] = []
    tasks_completed: list[str] = []
    tasks_deferred: list[str] = []
