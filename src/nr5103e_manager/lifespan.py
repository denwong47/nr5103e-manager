import asyncio
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI

from . import config
from .func.nr5103e.monitor import monitor_cellular_health
from .func.ping import recurring_ping_all_hosts
from .models import logger
from .models.lifespan import LifeSpanData


def create_lifespan(
    lifespan_data: LifeSpanData,
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    """
    Create a lifespan context manager for the FastAPI application.

    A static :class:`LifeSpanData` instance is passed to the function, which is used to store
    the ping history and other lifespan-related data. The returned context manager will manage
    the lifespan of the FastAPI application, starting and stopping the recurring ping tasks
    for the specified hosts.
    """

    @asynccontextmanager
    async def _lifespan(app: FastAPI):
        logger.info(
            "Starting application lifespan for FastAPI host #{app_id}...",
            app_id=id(app),
        )
        ping_targets = config.get_ping_targets()
        monitored_ips = config.get_monitored_ips()
        config.validate_monitored_ips_subset(monitored_ips, ping_targets)

        logger.info("Instantiating lifespan data...")

        stop_signal = asyncio.Event()

        futures = [
            recurring_ping_all_hosts(
                ping_targets,
                buffer=lifespan_data.ping_history,
                source=config.PING_SOURCE,
                min_interval=config.PING_INTERVAL,
                timeout=config.PING_TIMEOUT,
                stop_signal=stop_signal,
            ),
            monitor_cellular_health(
                monitored_ips=monitored_ips,
                ping_responses=lifespan_data.ping_history,
                session=lifespan_data.nr5103e_session,
                interval=config.MONITORING_INTERVAL,
                stop_signal=stop_signal,
            ),
        ]
        tasks = [asyncio.create_task(future) for future in futures]
        yield

        stop_signal.set()

        for task in tasks:
            task.cancel()

    return _lifespan
