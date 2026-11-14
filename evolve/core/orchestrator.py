"""Finite task execution and controlled transitions; no persistence or scheduler."""
from dataclasses import replace
from uuid import uuid4
from collections.abc import Mapping
from .entities import Goal, Task, Run, State, TERMINAL, freeze
from .events import EventBus, utcnow
from .executor import Executor, Cancellation, ExecutionCancelled


class Orchestrator:
    def __init__(self, *, events=None, clock=utcnow, id_factory=lambda: str(uuid4())):
        self.events = events if events is not None else EventBus(clock)
        self._clock, self._id = clock, id_factory
        self._goals, self._tasks, self._runs = {}, {}, {}
        self._active = {}
        self._executing = False
        self._closed = False
        self._closed_notified = False

    def _open(self):
        if self._closed:
            raise RuntimeError('orchestrator_closed')

    def _description(self, text):
        if not isinstance(text, str) or not text.strip() or len(text) > 1000:
            raise ValueError('invalid_description')
        return text.strip()

    def _new_id(self):
        value = self._id()
        if not isinstance(value, str) or not value or value in self._goals or value in self._tasks or value in self._runs:
            raise ValueError('invalid_or_duplicate_id')
        return value

    def goal(self, goal_id: str) -> Goal:
        return self._goals[goal_id]

    def task(self, task_id: str) -> Task:
        return self._tasks[task_id]

    def run(self, run_id: str) -> Run:
        return self._runs[run_id]

    def create_goal(self, description: str) -> Goal:
        self._open()
        now = self._clock()
        goal = Goal(self._new_id(), self._description(description), State.PENDING, (), now, now)
        self._goals[goal.id] = goal
        self.events.emit('goal.created', goal_id=goal.id)
        return goal

    def add_task(self, goal_id: str, description: str) -> Task:
        self._open()
        goal = self.goal(goal_id)
        if goal.status != State.PENDING or self._executing:
            raise ValueError('goal_not_accepting_tasks')
        now = self._clock()
        task = Task(self._new_id(), goal_id, self._description(description), State.PENDING, (), now, now)
        self._tasks[task.id] = task
        self._goals[goal_id] = replace(goal, task_ids=goal.task_ids+(task.id,), updated_at=now)
        self.events.emit('task.created', goal_id=goal_id, task_id=task.id)
        return task

    def _refresh_goal(self, goal_id):
        goal = self.goal(goal_id)
        states = [self.task(x).status for x in goal.task_ids]
        status = State.PENDING
        if states and all(x in TERMINAL for x in states):
            status = State.FAILED if State.FAILED in states else (State.CANCELLED if State.CANCELLED in states else State.COMPLETED)
        elif any(x != State.PENDING for x in states):
            status = State.RUNNING
        self._goals[goal_id] = replace(goal, status=status, updated_at=self._clock())
        if status in TERMINAL and status != goal.status:
            self.events.emit('goal.'+status.value, goal_id=goal_id)

    def cancel_task(self, task_id: str) -> bool:
        task = self.task(task_id)
        if task.status in TERMINAL:
            return False
        if task.status == State.RUNNING:
            token = self._active[task.id]
            if token.requested:
                return False
            token.request()
            self.events.emit('task.cancel_requested', goal_id=task.goal_id, task_id=task.id, run_id=task.run_ids[-1])
        else:
            self._tasks[task.id] = replace(task, status=State.CANCELLED, updated_at=self._clock())
            previous = self.goal(task.goal_id).status
            self._refresh_goal_silent(task.goal_id)
            status = self.goal(task.goal_id).status
            self.events.emit('task.cancelled', goal_id=task.goal_id, task_id=task.id)
            if status in TERMINAL and status != previous:
                self.events.emit('goal.'+status.value, goal_id=task.goal_id)
        return True

    def retry_task(self, task_id: str) -> Task:
        self._open()
        task = self.task(task_id)
        if task.status not in TERMINAL or self._executing:
            raise ValueError('task_not_retryable')
        task = replace(task, status=State.PENDING, result=None, error=None, updated_at=self._clock())
        self._tasks[task_id] = task
        self._refresh_goal(task.goal_id)
        self.events.emit('task.retry_requested', goal_id=task.goal_id, task_id=task.id)
        return task

    def execute_next(self, goal_id: str, executor: Executor) -> Run | None:
        self._open()
        if self._executing:
            raise RuntimeError('execution_reentrant')
        goal = self.goal(goal_id)
        task = next((self.task(x) for x in goal.task_ids if self.task(x).status == State.PENDING), None)
        if task is None:
            return None
        now = self._clock()
        run = Run(self._new_id(), goal_id, task.id, len(task.run_ids)+1, State.RUNNING, now)
        task = replace(task, status=State.RUNNING, run_ids=task.run_ids+(run.id,), updated_at=now)
        token = Cancellation()
        self._runs[run.id], self._tasks[task.id], self._active[task.id] = run, task, token
        self._goals[goal_id] = replace(goal, status=State.RUNNING, updated_at=now)
        self._executing = True
        interrupted = None
        status, result, error = State.COMPLETED, None, None
        try:
            self.events.emit('run.started', goal_id=goal_id, task_id=task.id, run_id=run.id)
            token.checkpoint()
            raw = executor.execute(task, run, token)
            token.checkpoint()
            if not isinstance(raw, Mapping):
                raise ValueError('result_must_be_mapping')
            result = freeze(raw)
        except ExecutionCancelled:
            status = State.CANCELLED
        except Exception:
            status, error = State.FAILED, 'executor_error'
        except BaseException as exception:
            status, interrupted = State.CANCELLED, exception
        finally:
            now = self._clock()
            run = replace(run, status=status, finished_at=now, result=result, error=error)
            self._runs[run.id] = run
            self._tasks[task.id] = replace(task, status=status, result=result, error=error, updated_at=now)
            del self._active[task.id]
            # Keep reentrancy blocked through terminal event delivery.
            try:
                self._refresh_goal_silent(goal_id)
                goal_status = self.goal(goal_id).status
                self.events.emit('run.'+status.value, goal_id=goal_id, task_id=task.id, run_id=run.id)
                if goal_status in TERMINAL:
                    self.events.emit('goal.'+goal_status.value, goal_id=goal_id)
            finally:
                self._executing = False
                self._notify_closed()
        if interrupted is not None:
            raise interrupted
        return run

    def _refresh_goal_silent(self, goal_id):
        goal = self.goal(goal_id)
        states = [self.task(x).status for x in goal.task_ids]
        status = State.PENDING if all(x == State.PENDING for x in states) else State.RUNNING
        if all(x in TERMINAL for x in states):
            status = State.FAILED if State.FAILED in states else (State.CANCELLED if State.CANCELLED in states else State.COMPLETED)
        self._goals[goal_id] = replace(goal, status=status, updated_at=self._clock())

    def close(self):
        if not self._closed:
            self._closed = True
            self.events.emit('core.close_requested')
            for task in tuple(self._tasks.values()):
                self.cancel_task(task.id)
            self._notify_closed()

    def _notify_closed(self):
        if self._closed and not self._executing and not self._closed_notified:
            self._closed_notified = True
            self.events.emit('core.closed')
