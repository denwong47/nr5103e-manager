from enum import StrEnum

from pydantic import ConfigDict, alias_generators

GLOBAL_MODEL_CONFIG = ConfigDict(
    extra="forbid",
    alias_generator=alias_generators.to_camel,
    validate_by_name=True,
    validate_by_alias=True,
)


class HealthStatus(StrEnum):
    """
    Health check status enumeration.
    """

    HEALTHY = "ok"
    UNSTABLE = "unstable"
    OFFLINE = "offline"
