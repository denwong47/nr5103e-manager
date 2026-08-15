import asyncio
from collections.abc import Mapping

from pydantic import IPvAnyAddress

from ...common import wait_at_least
from ...models import logger
from ...models.nr5103e import NR5103ESession
from ...models.ping import PingResponse
from .reboot import reboot

MIN_SUCCESS_RATE = 0.01
"""
The minimum success rate of pings to the monitored IPs before triggering a modem reboot.
If the success rate is below or equal this threshold, a reboot will be triggered.
"""


async def monitor_cellular_health(
    *,
    monitored_ips: list[IPvAnyAddress],
    ping_responses: Mapping[IPvAnyAddress, PingResponse],
    session: NR5103ESession,
    interval: float,
    stop_signal: asyncio.Event | None = None,
):
    """
    Monitor the cellular health by checking the ping responses to a set of monitored IPs.
    If the success rate of pings falls below a defined threshold, trigger a modem reboot.

    Parameters
    ----------
    monitored_ips : list[IPvAnyAddress]
        The subset of IPs that, when failed to ping, will trigger a modem reboot.
    ping_responses : Mapping[IPvAnyAddress, PingResponse]
        A mapping of IP addresses to their corresponding ping responses.
    session : NR5103ESession
        The session object for interacting with the NR5103E device.
    interval : float
        The interval (in seconds) at which to check the ping responses.
    stop_signal : asyncio.Event | None, optional
        An optional asyncio event that can be used to signal the monitoring loop to stop.
    """
    logger.info("Starting cellular health monitoring.")

    while True:
        if stop_signal and stop_signal.is_set():
            logger.info("Stopping cellular health monitoring.")
            break

        async with wait_at_least(interval):
            relevant_pings = [
                ping_responses[ip].summary
                for ip in monitored_ips
                if ip in ping_responses
            ]

            if not relevant_pings:
                logger.warning(
                    "No ping responses available for monitored IPs yet: {ips}",
                    ips=monitored_ips,
                )
                continue

            success_rate = sum(summary.successful for summary in relevant_pings) / sum(
                summary.total for summary in relevant_pings
            )

            if success_rate <= MIN_SUCCESS_RATE:
                logger.warning(
                    "Cellular health check failed. Success rate: {rate:.2%}. Triggering modem reboot.",
                    rate=success_rate,
                )
                try:
                    response = await reboot(session=session)
                    if response.result != "success":
                        logger.error("Failed to reboot the modem.", response)
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "Exception occurred while rebooting the modem: {exc}", exc=exc
                    )
            else:
                logger.info(
                    "Cellular health check passed. Success rate: {rate:.2%}.",
                    rate=success_rate,
                )

    logger.info("Cellular health monitoring stopped.")
