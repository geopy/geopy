try:
    # >=3.7
    from asyncio import current_task
except ImportError:
    from asyncio import Task
    current_task = Task.current_task
    del Task
