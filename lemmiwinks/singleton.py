import threading


class Singleton(type):
    _instances = dict()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ThreadSafeSingleton(type):
    _instances = dict()
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with ThreadSafeSingleton._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super(ThreadSafeSingleton, cls).__call__(*args,
                                                                               **kwargs)
            return cls._instances[cls]
