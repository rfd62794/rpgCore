from enum import Enum


class GoalStatus(str, Enum):
    ACTIVE     = "ACTIVE"
    DEFERRED   = "DEFERRED"
    COMPLETE   = "COMPLETE"
    SUPERSEDED = "SUPERSEDED"


class MilestoneStatus(str, Enum):
    ACTIVE   = "ACTIVE"
    QUEUED   = "QUEUED"
    COMPLETE = "COMPLETE"
    BLOCKED  = "BLOCKED"


class TaskStatus(str, Enum):
    ACTIVE  = "ACTIVE"
    QUEUED  = "QUEUED"
    DONE    = "DONE"
    BLOCKED = "BLOCKED"


class TaskScope(str, Enum):
    SHARED  = "shared"
    DEMO    = "demo"
    TOOLING = "tooling"
    DOCS    = "docs"


class OwnerType(str, Enum):
    HUMAN   = "human"
    SCRIBE  = "scribe"
    CURATOR = "curator"
