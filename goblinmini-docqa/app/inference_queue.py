# app/inference_queue.py
import asyncio
from typing import Callable, Any
from contextlib import asynccontextmanager


class InferenceQueue:
    def __init__(
        self,
        model_callable: Callable[[str], Any],
        max_workers: int = 1,
        max_queue: int = 16,
    ):
        self.model_callable = model_callable
        self.queue = asyncio.Queue(maxsize=max_queue)
        self.semaphore = asyncio.Semaphore(max_workers)
        self.running = False

    async def start(self):
        if self.running:
            return
        self.running = True
        # spawn consumer tasks equal to max_workers
        for _ in range(self.semaphore._value):  # internal but fine here
            asyncio.create_task(self._worker_loop())

    async def _worker_loop(self):
        while True:
            job = await self.queue.get()
            payload, future = job["payload"], job["future"]
            try:
                async with self._semaphore_ctx():
                    # model_call can be sync or async; run in thread if sync
                    if asyncio.iscoroutinefunction(self.model_callable):
                        result = await self.model_callable(payload)
                    else:
                        loop = asyncio.get_running_loop()
                        result = await loop.run_in_executor(
                            None, self.model_callable, payload
                        )
                    future.set_result(result)
            except Exception as e:
                future.set_exception(e)
            finally:
                self.queue.task_done()

    async def submit(self, payload, timeout: float = 10.0):
        future = asyncio.get_event_loop().create_future()
        job = {"payload": payload, "future": future}
        try:
            await asyncio.wait_for(self.queue.put(job), timeout=timeout)
        except asyncio.TimeoutError:
            raise RuntimeError("Inference queue full; backpressure applied")

        return await future

    # small helper to use semaphore as async context manager
    @asynccontextmanager
    async def _semaphore_ctx(self):
        await self.semaphore.acquire()
        try:
            yield
        finally:
            self.semaphore.release()
