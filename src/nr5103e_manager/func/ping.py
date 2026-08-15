import asyncio
from collections.abc import AsyncGenerator, MutableMapping
from typing import Any, cast

from asyncping3 import ping
from pydantic import IPvAnyAddress

from ..common import wait_at_least
from ..models import logger
from ..models.ping import PingResponse

DEFAULT_TIMEOUT = 15
"""
Module for pinging hosts asynchronously.
"""

DEFAULT_MIN_INTERVAL = 2
"""
The minimum interval between consecutive ping requests in seconds.
"""


async def ping_host(
    host: IPvAnyAddress,
    *,
    source: IPvAnyAddress | None = None,
    previous: "PingResponse| None" = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> PingResponse:
    """
    Ping a host and return the response.

    Parameters
    ----------
    host : IPvAnyAddress
        The host to ping.

    source : IPvAnyAddress | None, optional
        The source IP address to use for the ping request. If None, the system will use
        all available network interfaces. Default is None.

    previous: PingResponse | None, optional
        The previous ping response, if any. This is used to maintain a chain of ping
        responses for historical analysis. Default is None.

    timeout : float, optional
        The timeout for the ping request in seconds. Default is 15.0 seconds.

    Returns
    -------
    PingResponse
        The response of the ping request, including the host, success status, and
        response time or error message.
    """
    kwargs = {}
    if source is not None:
        kwargs["src_addr"] = str(source)

    try:
        match await ping(str(host), timeout=timeout, **kwargs):
            case float() as response_time:
                logger.debug(
                    "Ping to host {host} succeeded with response time {response_time:.3f}s.",
                    host=host,
                    response_time=response_time,
                )
                return PingResponse(
                    host=host, rtt=response_time, previous_result=cast(Any, previous)
                )
            case None:
                logger.warning(
                    "Ping to host {host} timed out after {timeout} seconds.",
                    host=host,
                    timeout=timeout,
                )
                return PingResponse(
                    host=host, rtt=None, previous_result=cast(Any, previous)
                )
            case False:
                raise RuntimeError("Host may not be valid.")
            case _:
                raise RuntimeError("Unexpected ping response.")

    except Exception as exc:  # noqa: BLE001 - we are catching blind errors here intentionally.
        logger.error("Error pinging host {host}: {error}", host=host, error=str(exc))
        return PingResponse(host=host, rtt=None, previous_result=cast(Any, previous))


async def recurring_ping_host(
    host: IPvAnyAddress,
    *,
    history: int = 10,
    source: IPvAnyAddress | None = None,
    min_interval: float = DEFAULT_MIN_INTERVAL,
    timeout: int = DEFAULT_TIMEOUT,
) -> AsyncGenerator[PingResponse]:
    """
    Recurring ping a host and yield the response.

    Parameters
    ----------
    host : IPvAnyAddress
        The host to ping.

    Yields
    ------
    PingResponse
        The response of the ping request, including the host, success status, and
        response time or error message.

    history : int, optional
        The maximum number of previous results to keep. Default is 10.
    source : IPvAnyAddress | None, optional
        The source IP address to use for the ping request. If None, the system will use
        all available network interfaces. Default is None.
    min_interval : float, optional
        The minimum interval between consecutive ping requests in seconds. Default is 2.
    timeout : int, optional
        The timeout for the ping request in seconds. Default is 15.
    """
    result: PingResponse | None = None

    while True:
        response = await ping_host(
            host, previous=result, timeout=timeout, source=source
        )

        async with wait_at_least(min_interval):
            response.prune_chain(max_length=history)

            yield response

        result = response


async def recurring_ping_all_hosts(
    hosts: list[IPvAnyAddress],
    *,
    buffer: MutableMapping[IPvAnyAddress, PingResponse],
    history: int = 10,
    source: IPvAnyAddress | None = None,
    min_interval: float = DEFAULT_MIN_INTERVAL,
    timeout: int = DEFAULT_TIMEOUT,
    stop_signal: asyncio.Event | None = None,
):
    """
    Recurring ping all hosts in the list and update the buffer with the latest responses.

    A mutable mapping must be passed in as the buffer to store the latest ping responses
    for each host. The buffer will be updated with the latest response for each host
    after each ping.

    This function will run indefinitely until the ``stop_signal`` is set, if provided.
    It will not return any values; the upstream caller is responsible for checking
    the buffer for the latest ping responses.

    Parameters
    ----------
    hosts : list[IPvAnyAddress]
        The list of hosts to ping.

    buffer : MutableMapping[IPvAnyAddress, PingResponse]
        A mutable mapping to store the latest ping responses for each host.

    history : int, optional
        The maximum number of previous results to keep for each host. Default is 10.

    source : IPvAnyAddress | None, optional
        The source IP address to use for the ping requests. If None, the system will use
        all available network interfaces. Default is None.

    min_interval : float, optional
        The minimum interval between consecutive ping requests in seconds. Default is 2.

    timeout : int, optional
        The timeout for the ping request in seconds. Default is 15.

    stop_signal : asyncio.Event | None, optional
        An optional asyncio.Event that can be used to signal the function to stop.
        If provided, the function will exit when the event is set. Default is None.
    """
    logger.info(
        "Starting recurring ping for hosts: {hosts} with min_interval={min_interval}s, timeout={timeout}s, history={history}, source={source}.",
        hosts=hosts,
        min_interval=min_interval,
        timeout=timeout,
        history=history,
        source=source,
    )

    async def ping_host_and_update_buffer(host: IPvAnyAddress):
        """
        Ping a host and update the buffer with the latest response.

        Parameters
        ----------
        host : IPvAnyAddress
            The host to ping.
        """
        async for response in recurring_ping_host(
            host,
            history=history,
            source=source,
            min_interval=min_interval,
            timeout=timeout,
        ):
            buffer[host] = response

        return True

    tasks = [asyncio.create_task(ping_host_and_update_buffer(host)) for host in hosts]

    if stop_signal is not None:
        await stop_signal.wait()
        logger.warning("Stop signal received. Cancelling all ping tasks.")
        for task in tasks:
            task.cancel()
    else:
        await asyncio.gather(*tasks)
        # Unreachable
