"""
Global configuration for Pydantic models in the nr5103e_manager package.
"""

import os

from pydantic import IPvAnyAddress, TypeAdapter

PING_TARGETS = os.environ.get("PING_TARGETS", default=None) or "1.1.1.1,8.8.8.8"
"""
Default ping targets for health checks. Can be overridden by the ``PING_TARGETS``
environment variable.
"""

MONITORED_IPS = os.environ.get("MONITORED_IPS", default=None) or "1.1.1.1,8.8.8.8"
"""
Default subset of ``PING_TARGETS`` that, when unreachable, will trigger a modem
reboot. Can be overridden by the ``MONITORED_IPS`` environment variable. Every IP
listed here must also be present in ``PING_TARGETS``.
"""

PING_INTERVAL: int = int(os.environ.get("PING_INTERVAL", default="60"))
"""
Default interval (in seconds) between ping attempts. Can be overridden by the ``PING_INTERVAL`` environment variable.
"""

PING_TIMEOUT: int = int(os.environ.get("PING_TIMEOUT", default="15"))
"""
Default timeout (in seconds) for ping attempts. Can be overridden by the ``PING_TIMEOUT`` environment variable.
"""

PING_SOURCE: IPvAnyAddress | None = (
    TypeAdapter(IPvAnyAddress).validate_python(os.environ.get("PING_SOURCE"))
    if os.environ.get("PING_SOURCE")
    else None
)
"""
Default source IP address for ping attempts. Can be overridden by the ``PING_SOURCE`` environment variable.
If not set, the system will use all available network interfaces for pinging.
"""

NR5103E_HOST: IPvAnyAddress = TypeAdapter(IPvAnyAddress).validate_python(
    os.environ.get("NR5103E_HOST", default="192.168.1.1")
)
"""
Default host IP address for the NR5103E device. Can be overridden by the ``NR5103E_HOST`` environment variable.
"""

NR5103E_USERNAME: str = os.environ.get("NR5103E_USERNAME", default="admin")
"""
Default username for the NR5103E device. Can be overridden by the ``NR5103E_USERNAME`` environment variable.
"""

NR5103E_PASSWORD: str = os.environ.get("NR5103E_PASSWORD", default="")
"""
Default password for the NR5103E device. Can be overridden by the ``NR5103E_PASSWORD`` environment variable.
"""

MONITORING_INTERVAL: float = float(os.environ.get("MONITORING_INTERVAL", default="150"))
"""
Default interval (in seconds) for monitoring the cellular health. Can be overridden by the ``MONITORING_INTERVAL`` environment variable.
"""


def get_ping_targets(targets: str = PING_TARGETS) -> list[IPvAnyAddress]:
    """
    Get the list of ping targets from a comma-separated string.

    Parameters
    ----------
    targets : str, optional
        A comma-separated string of ping targets. Default is the value of the
        ``PING_TARGETS`` environment variable.

    Returns
    -------
    list[IPvAnyAddress]
        A list of ping targets as IPvAnyAddress objects.

    Raises
    ------
    ValidationError
        If any of the targets are not valid IP addresses.
    """
    return TypeAdapter(list[IPvAnyAddress]).validate_python(
        [t for target in targets.split(",") if (t := target.strip())]
    )


def get_monitored_ips(ips: str = MONITORED_IPS) -> list[IPvAnyAddress]:
    """
    Get the list of monitored IPs (the subset of ``PING_TARGETS`` that, when
    unreachable, will trigger a modem reboot) from a comma-separated string.

    Parameters
    ----------
    ips : str, optional
        A comma-separated string of monitored IPs. Default is the value of the
        ``MONITORED_IPS`` environment variable.

    Returns
    -------
    list[IPvAnyAddress]
        A list of monitored IPs as IPvAnyAddress objects.

    Raises
    ------
    ValidationError
        If any of the IPs are not valid IP addresses.
    """
    return TypeAdapter(list[IPvAnyAddress]).validate_python(
        [t for target in ips.split(",") if (t := target.strip())]
    )


def validate_monitored_ips_subset(
    monitored_ips: list[IPvAnyAddress], ping_targets: list[IPvAnyAddress]
) -> None:
    """
    Ensure that every monitored IP is also a ping target.

    Parameters
    ----------
    monitored_ips : list[IPvAnyAddress]
        The IPs that, when unreachable, will trigger a modem reboot.
    ping_targets : list[IPvAnyAddress]
        The IPs that are actually pinged for health checks.

    Raises
    ------
    ValueError
        If ``monitored_ips`` is not a subset of ``ping_targets``.
    """
    missing = set(monitored_ips) - set(ping_targets)
    if missing:
        raise ValueError(
            "MONITORED_IPS must be a subset of PING_TARGETS. "
            f"Not present in PING_TARGETS: {', '.join(str(ip) for ip in sorted(missing, key=str))}"
        )
