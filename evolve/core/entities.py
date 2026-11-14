"""Immutable public snapshots; business state is owned by the orchestrator."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import math
from types import MappingProxyType
from collections.abc import Mapping


class State(str, Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


TERMINAL = frozenset((State.COMPLETED, State.FAILED, State.CANCELLED))


def freeze(value, depth=0, _budget=None):
    """Bounded JSON-like values; immutable copies, no executable objects.

    Reserved credential keys are rejected. This is not a general secret detector;
    callers must never supply secrets, including in ordinary string values.
    """
    if _budget is None:
        _budget = [1024]
    _budget[0] -= 1
    if depth > 8 or _budget[0] < 0:
        raise ValueError('payload_depth')
    if value is None or type(value) in (bool, int):
        if type(value) is int and value.bit_length() > 256:
            raise ValueError('payload_integer')
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if type(value) is str and len(value) <= 4096:
        return value
    if isinstance(value, Mapping) and len(value) <= 64:
        result = {}
        for key, item in value.items():
            if type(key) is not str or len(key) > 80 or any(x in key.lower() for x in ('password', 'secret', 'token', 'api_key', 'credential')):
                raise ValueError('payload_key')
            result[key] = freeze(item, depth+1, _budget)
        return MappingProxyType(result)
    if type(value) in (list, tuple) and len(value) <= 64:
        return tuple(freeze(x, depth+1, _budget) for x in value)
    raise ValueError('payload_value')


@dataclass(frozen=True)
class Goal:
    id: str
    description: str
    status: State
    task_ids: tuple[str, ...]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Task:
    id: str
    goal_id: str
    description: str
    status: State
    run_ids: tuple[str, ...]
    created_at: datetime
    updated_at: datetime
    result: Mapping | None = None
    error: str | None = None


@dataclass(frozen=True)
class Run:
    id: str
    goal_id: str
    task_id: str
    attempt: int
    status: State
    started_at: datetime
    finished_at: datetime | None = None
    result: Mapping | None = None
    error: str | None = None


@dataclass(frozen=True)
class Event:
    sequence: int
    kind: str
    timestamp: datetime
    source: str
    goal_id: str | None
    task_id: str | None
    run_id: str | None
    payload: Mapping
