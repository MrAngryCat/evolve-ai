"""Four synthetic TTS steps; no actual research, coding, TTS or self-update."""
from . import Orchestrator, MockExecutor


def demo() -> int:
    core = Orchestrator()
    goal = core.create_goal('Добавить синтез речи (имитация)')
    for description in ('Изучить варианты TTS', 'Выбрать решение', 'Подготовить модуль', 'Проверить результат'):
        core.add_task(goal.id, description)
    print('DEMO: только имитация; нет исследования, кода, LLM или синтеза речи.')
    for _ in range(4):
        core.execute_next(goal.id, MockExecutor())
    for event in core.events.history:
        print(f'{event.sequence:02d} {event.kind}')
    print('Goal: '+core.goal(goal.id).status.value)
    core.close()
    return 0
