"""Bounded interface contract and a synthetic executor with no external tools."""
from collections.abc import Mapping
from typing import Protocol
from .entities import Task, Run, State


class ExecutionCancelled(Exception):
    pass


class Cancellation:
    def __init__(self):
        self._requested = False

    @property
    def requested(self) -> bool:
        return self._requested

    def request(self):
        self._requested = True

    def checkpoint(self):
        if self._requested:
            raise ExecutionCancelled()


class Executor(Protocol):
    def execute(self, task: Task, run: Run, cancellation: Cancellation) -> Mapping:
        """Return a structured result; cooperate with cancellation checkpoints.

        Only trusted in-process implementations are allowed at this phase.
        This contract cannot interrupt or sandbox arbitrary Python code.
        """
        ...


class MockExecutor:
    def __init__(self, outcome='success'):
        if outcome not in ('success', 'fail', 'cancel'):
            raise ValueError('invalid_mock_outcome')
        self._outcome = outcome

    def execute(self, task: Task, run: Run, cancellation: Cancellation) -> Mapping:
        if task.status != State.RUNNING or run.status != State.RUNNING or run.task_id != task.id or run.goal_id != task.goal_id:
            raise ValueError('run_not_executable')
        cancellation.checkpoint()
        if self._outcome == 'cancel':
            raise ExecutionCancelled()
        if self._outcome == 'fail':
            raise RuntimeError('synthetic_failure')
        cancellation.checkpoint()
        return {'demo': True, 'attempt': run.attempt, 'action': 'simulated_only'}
