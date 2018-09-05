import asyncio


def task(func):
    def wrapper(*args, **kwargs):
        task = asyncio.get_event_loop().create_task(func(*args, **kwargs))
        return task
    return wrapper
