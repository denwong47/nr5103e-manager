from pydantic import BaseModel, Field

from .common import GLOBAL_MODEL_CONFIG, HealthStatus
from .lifespan import LifeSpanData
from .ping import PingResponse


class HealthCheckResponse(BaseModel):
    """
    Health check response model.
    """

    model_config = GLOBAL_MODEL_CONFIG

    overall: HealthStatus = Field(..., description="The health status of the service.")
    pings: list[PingResponse] = Field(
        default_factory=list,
        description="A list of ping responses for the monitored hosts.",
    )

    @classmethod
    def from_lifespan(cls, lifespan_data: LifeSpanData) -> "HealthCheckResponse":
        """
        Create a HealthCheckResponse from the given LifeSpanData.

        Parameters
        ----------
        lifespan_data : LifeSpanData
            The LifeSpanData instance containing the ping history.

        Returns
        -------
        HealthCheckResponse
            The health check response with overall status and ping responses.
        """
        pings = list(lifespan_data.ping_history.values())
        pings_health = (
            sum(ping.success_rate() for ping in pings) / len(pings) if pings else 0.0
        )

        all_healths = [
            pings_health,
        ]

        match sum(all_healths) / len(all_healths):
            case health if health >= 0.9:
                overall_status = HealthStatus.HEALTHY
            case health if health > 0:
                overall_status = HealthStatus.UNSTABLE
            case _:
                overall_status = HealthStatus.OFFLINE

        return cls(overall=overall_status, pings=pings)
