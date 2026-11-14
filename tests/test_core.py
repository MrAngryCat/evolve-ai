"""Finite in-memory core acceptance tests."""
import contextlib
from dataclasses import FrozenInstanceError
import io
import json
import unittest

from evolve.core import Orchestrator, MockExecutor, State, EventBus
from evolve.cli import main


class CoreTests(unittest.TestCase):
    def test_cancel_observer_sees_consistent_goal(self):
        core = Orchestrator()
        goal = core.create_goal('goal')
        task = core.add_task(goal.id, 'task')
        observed = []
        core.events.subscribe('task.cancelled', lambda e: observed.append(core.goal(e.goal_id).status))
        core.cancel_task(task.id)
        self.assertEqual(observed, [State.CANCELLED])

    def test_event_metadata_cannot_capture_mutable_objects(self):
        bus = EventBus()
        for key in ('source', 'goal_id', 'task_id', 'run_id'):
            with self.assertRaises(ValueError):
                bus.emit('demo', **{key: {'mutable': True}})
        self.assertEqual(bus.history, ())

    def test_shared_payload_expansion_is_bounded(self):
        value = 0
        for _ in range(7):
            value = [value]*64
        with self.assertRaises(ValueError):
            EventBus().emit('demo', payload={'x': value})

    def test_cancel_during_executor_return_and_reentrant_execution(self):
        core = self.core
        goal = self.goal
        task = self.task
        class CancellingExecutor:
            def execute(self, snapshot, run, token):
                core.cancel_task(task.id)
                return {'demo': True}
        core.events.subscribe('run.started', lambda e: core.execute_next(goal.id, MockExecutor()))
        run = core.execute_next(goal.id, CancellingExecutor())
        self.assertEqual(run.status, State.CANCELLED)
        self.assertEqual(core.events.subscriber_errors, 1)

    def test_close_during_execution_finishes_before_closed_event(self):
        core = Orchestrator()
        goal = core.create_goal('goal')
        core.add_task(goal.id, 'task')
        core.events.subscribe('run.started', lambda e: core.close())
        core.execute_next(goal.id, MockExecutor())
        kinds = [e.kind for e in core.events.history]
        self.assertLess(kinds.index('run.cancelled'), kinds.index('core.closed'))

    def test_subscriber_cancel_of_remaining_task_has_one_goal_terminal(self):
        core = Orchestrator()
        goal = core.create_goal('goal')
        core.add_task(goal.id, 'one')
        other = core.add_task(goal.id, 'two')
        core.events.subscribe('run.completed', lambda e: core.cancel_task(other.id))
        core.execute_next(goal.id, MockExecutor())
        self.assertEqual([e.kind for e in core.events.history].count('goal.cancelled'), 1)

    def test_subscriber_emission_chain_is_bounded(self):
        bus = EventBus()
        bus.subscribe('echo', lambda e: bus.emit('echo'))
        bus.emit('echo')
        self.assertLessEqual(len(bus.history), 256)
        self.assertEqual(bus.subscriber_errors, 1)

    def test_completed_run_rejected_by_mock(self):
        core = Orchestrator()
        goal = core.create_goal('goal')
        task = core.add_task(goal.id, 'task')
        run = core.execute_next(goal.id, MockExecutor())
        from evolve.core import Cancellation
        with self.assertRaises(ValueError):
            MockExecutor().execute(core.task(task.id), run, Cancellation())

    def setUp(self):
        self.core = Orchestrator()
        self.goal = self.core.create_goal('Demo only')
        self.task = self.core.add_task(self.goal.id, 'Synthetic task')

    def test_goal_task_relationship_and_immutable_views(self):
        self.assertEqual(self.task.goal_id, self.goal.id)
        self.assertEqual(self.core.goal(self.goal.id).task_ids, (self.task.id,))
        with self.assertRaises(FrozenInstanceError):
            self.task.status = State.COMPLETED

    def test_success_creates_linked_run(self):
        run = self.core.execute_next(self.goal.id, MockExecutor())
        self.assertEqual(run.task_id, self.task.id)
        self.assertEqual(run.goal_id, self.goal.id)
        self.assertEqual(run.status, State.COMPLETED)
        self.assertEqual(self.core.task(self.task.id).result['demo'], True)
        self.assertEqual(self.core.goal(self.goal.id).status, State.COMPLETED)
        self.assertIsNone(self.core.execute_next(self.goal.id, MockExecutor()))

    def test_error_is_redacted_and_state_consistent(self):
        run = self.core.execute_next(self.goal.id, MockExecutor('fail'))
        self.assertEqual(run.status, State.FAILED)
        self.assertEqual(run.error, 'executor_error')
        self.assertEqual(self.core.task(self.task.id).status, State.FAILED)
        self.assertEqual(self.core.goal(self.goal.id).status, State.FAILED)

    def test_pending_cancel_is_idempotent(self):
        self.assertTrue(self.core.cancel_task(self.task.id))
        count = len(self.core.events.history)
        self.assertFalse(self.core.cancel_task(self.task.id))
        self.assertEqual(len(self.core.events.history), count)
        self.assertIsNone(self.core.execute_next(self.goal.id, MockExecutor()))
        self.assertEqual(self.core.goal(self.goal.id).status, State.CANCELLED)

    def test_running_cancel_is_cooperative_and_wins_over_return(self):
        self.core.events.subscribe('run.started', lambda e: self.core.cancel_task(e.task_id))
        run = self.core.execute_next(self.goal.id, MockExecutor())
        self.assertEqual(run.status, State.CANCELLED)
        self.assertEqual(self.core.task(self.task.id).status, State.CANCELLED)

    def test_mock_cancellation(self):
        run = self.core.execute_next(self.goal.id, MockExecutor('cancel'))
        self.assertEqual(run.status, State.CANCELLED)

    def test_retry_is_explicit_and_preserves_prior_run(self):
        first = self.core.execute_next(self.goal.id, MockExecutor('fail'))
        self.core.retry_task(self.task.id)
        second = self.core.execute_next(self.goal.id, MockExecutor())
        self.assertNotEqual(first.id, second.id)
        self.assertEqual(self.core.run(first.id).status, State.FAILED)
        self.assertEqual(self.core.task(self.task.id).run_ids, (first.id, second.id))

    def test_no_implicit_completed_task_reexecution(self):
        first = self.core.execute_next(self.goal.id, MockExecutor())
        self.assertIsNone(self.core.execute_next(self.goal.id, MockExecutor()))
        self.assertEqual(self.core.run(first.id), first)
        self.core.retry_task(self.task.id)
        second = self.core.execute_next(self.goal.id, MockExecutor())
        self.assertEqual(second.attempt, 2)

    def test_retry_pending_is_invalid(self):
        with self.assertRaises(ValueError):
            self.core.retry_task(self.task.id)

    def test_event_order(self):
        self.core.execute_next(self.goal.id, MockExecutor())
        events = self.core.events.history
        self.assertEqual([e.kind for e in events], ['goal.created', 'task.created', 'run.started', 'run.completed', 'goal.completed'])
        self.assertEqual([e.sequence for e in events], [1, 2, 3, 4, 5])
        self.assertTrue(events[2].run_id)

    def test_independent_goals(self):
        other = self.core.create_goal('Other')
        task = self.core.add_task(other.id, 'Other task')
        self.core.execute_next(self.goal.id, MockExecutor())
        self.assertEqual(self.core.task(task.id).status, State.PENDING)
        self.assertEqual(self.core.goal(other.id).status, State.PENDING)

    def test_subscriber_failure_is_safe(self):
        def bad(e):
            raise RuntimeError('PRIVATE_SECRET')
        self.core.events.subscribe('run.started', bad)
        run = self.core.execute_next(self.goal.id, MockExecutor())
        self.assertEqual(run.status, State.COMPLETED)
        self.assertEqual(self.core.events.subscriber_errors, 1)
        self.assertNotIn('PRIVATE_SECRET', repr(self.core.events.history))

    def test_event_payload_is_immutable_and_rejects_secrets_and_objects(self):
        bus = EventBus()
        for payload in ({'api_key': 'private'}, {'x': object()}, {'x': float('nan')}):
            with self.assertRaises(ValueError):
                bus.emit('demo', payload=payload)
        event = bus.emit('demo', payload={'x': [1, {'y': True}]})
        with self.assertRaises(TypeError):
            event.payload['x'][1]['y'] = False

    def test_shutdown_is_idempotent_and_rejects_work(self):
        self.core.close()
        self.core.close()
        self.assertEqual(self.core.task(self.task.id).status, State.CANCELLED)
        with self.assertRaises(RuntimeError):
            self.core.create_goal('new')

    def test_invalid_description_and_unknown_ids(self):
        with self.assertRaises(ValueError):
            self.core.create_goal(' ')
        with self.assertRaises(KeyError):
            self.core.add_task('missing', 'task')

    def test_demo_cli_is_finite_and_explicit(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(['demo']), 0)
        self.assertIn('DEMO', output.getvalue())
        self.assertIn('completed', output.getvalue())
        self.assertEqual(output.getvalue().count('run.completed'), 4)

    def test_mock_has_no_network_process_or_file_operations(self):
        import sys
        denied = []
        active = [False]
        def guard(event, args):
            if active[0] and (event.startswith(('socket.', 'subprocess.', 'winreg.')) or event in ('open', 'os.system', 'os.mkdir', 'os.remove')):
                denied.append(event)
                raise AssertionError(event)
        sys.addaudithook(guard)
        try:
            active[0] = True
            for mode in ('success', 'fail', 'cancel'):
                c = Orchestrator()
                g = c.create_goal('demo')
                c.add_task(g.id, 'task')
                c.execute_next(g.id, MockExecutor(mode))
        finally:
            active[0] = False
        self.assertEqual(denied, [])
