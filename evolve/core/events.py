"""Synchronous ordered in-process event history, with isolated subscribers."""
from datetime import datetime, timezone
from collections import deque
from .entities import Event, freeze


def utcnow():
    return datetime.now(timezone.utc)


class EventBus:
    def __init__(self, clock=utcnow):
        self._clock = clock
        self._history = []
        self._subscribers = {}
        self._queue = deque()
        self._dispatching = False
        self._errors = 0
        self._emissions = 0

    @property
    def history(self) -> tuple[Event, ...]:
        return tuple(self._history)

    @property
    def subscriber_errors(self) -> int:
        return self._errors

    def subscribe(self, kind: str, handler):
        if not isinstance(kind, str) or not kind or not callable(handler):
            raise ValueError('invalid_subscription')
        self._subscribers.setdefault(kind, []).append(handler)

    def emit(self, kind: str, *, source='core', goal_id=None, task_id=None,
             run_id=None, payload=None) -> Event:
        if type(kind) is not str or not kind or len(kind) > 80 or not kind.isprintable():
            raise ValueError('invalid_event_kind')
        for meta in (source, goal_id, task_id, run_id):
            if meta is not None and (type(meta) is not str or not meta or len(meta) > 128 or not meta.isprintable()):
                raise ValueError('invalid_event_metadata')
        if not self._dispatching:
            self._emissions = 0
        if self._emissions >= 256:
            raise RuntimeError('event_dispatch_budget')
        value = freeze({} if payload is None else payload)
        if not hasattr(value, 'items'):
            raise ValueError('payload_must_be_mapping')
        event = Event(len(self._history)+1, kind, self._clock(), source,
                      goal_id, task_id, run_id, value)
        self._history.append(event)
        self._emissions += 1
        self._queue.append(event)
        if self._dispatching:
            return event
        self._dispatching = True
        try:
            while self._queue:
                current = self._queue.popleft()
                for handler in tuple(self._subscribers.get(current.kind, ())):
                    try:
                        handler(current)
                    except Exception:
                        self._errors += 1  # Never store exception messages or recurse.
        finally:
            self._dispatching = False
        return event
