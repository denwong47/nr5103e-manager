import asyncio
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager


@asynccontextmanager
async def wait_at_least(
    duration: float,
) -> AsyncGenerator[None]:
    """
    Async context manager that ensures the enclosed code block runs for at least the
    specified duration.

    Parameters
    ----------
    duration : float
        The minimum duration in seconds for which the code block should run.
    """
    start_time = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start_time
        if elapsed < duration:
            await asyncio.sleep(duration - elapsed)
