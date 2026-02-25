from datetime import date
from typing import Literal, Optional, Union
from pydantic import BaseModel
from .enums import SessionStatus


class Session(BaseModel):
    id: str                               # S001, S012
    type: Literal["session"] = "session"
    date: Union[date, None] = None
    status: SessionStatus
    test_floor: Union[int, None] = None
    focus: str = ""
    tasks_planned: list[str] = []
    tasks_completed: list[str] = []
    tasks_deferred: list[str] = []
