from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel
from .enums import GoalStatus, OwnerType


class Goal(BaseModel):
    id: str
    type: Literal["goal"] = "goal"
    title: str
    status: GoalStatus
    milestone: Optional[str] = None
    owner: OwnerType = OwnerType.HUMAN
    created: date
    modified: date
    tags: list[str] = []
