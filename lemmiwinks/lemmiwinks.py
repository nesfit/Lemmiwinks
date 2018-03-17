import abc
import asyncio


class Lemmiwinks(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def task_executor(self):
        raise NotImplemented

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.task_executor())
