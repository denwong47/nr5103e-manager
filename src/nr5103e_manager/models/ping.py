from datetime import UTC, datetime
from typing import Annotated, Self

from pydantic import BaseModel, Field, IPvAnyAddress, computed_field, model_validator
from pydantic.json_schema import SkipJsonSchema

from .common import GLOBAL_MODEL_CONFIG, HealthStatus


class PingRequestQuery(BaseModel):
    """
    Model for ping request query parameters.
    """

    model_config = GLOBAL_MODEL_CONFIG

    interval: float = Field(
        default=1,
        description="Interval between consecutive ping requests in seconds.",
        ge=0.1,
        le=10,
    )
    timeout: int = Field(
        default=5,
        description="Timeout for the ping request in seconds.",
        ge=0,
        le=20,
    )
    count: int = Field(
        default=1,
        description="Number of ping requests to send.",
        ge=1,
        le=10,
    )


class PingHistorySummary(BaseModel):
    """
    Summary of ping history.
    """

    model_config = GLOBAL_MODEL_CONFIG

    total: int = Field(..., description="Total number of ping attempts.")
    successful: int = Field(..., description="Number of successful ping attempts.")
    success_rate: float = Field(
        ..., description="Success rate of ping attempts as a float between 0 and 1."
    )
    mean_rtt: float | None = Field(
        default=None, description="Mean round-trip time (RTT) of successful pings."
    )
    max_rtt: float | None = Field(
        default=None, description="Maximum round-trip time (RTT) of successful pings."
    )


class PingResponse(BaseModel):
    """
    Ping response model.
    """

    model_config = GLOBAL_MODEL_CONFIG

    previous_result: Annotated["PingResponse | None", SkipJsonSchema] = Field(
        default=None,
        exclude=True,
        description="A weak reference to the previous ping response, if any.",
    )

    host: IPvAnyAddress = Field(..., description="The IP address of the host.")
    status: HealthStatus = Field(
        default=HealthStatus.OFFLINE, description="The health status of the host."
    )
    rtt: float | None = Field(..., description="The round-trip time in seconds.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="The timestamp of the ping response in UTC.",
    )

    @classmethod
    def empty(cls, host: IPvAnyAddress) -> "Self":
        """
        Create an empty PingResponse with default values.

        Parameters
        ----------
        host : IPvAnyAddress
            The IP address of the host.

        Returns
        -------
        PingResponse
            An empty PingResponse with default values.
        """
        return cls(host=host, status=HealthStatus.OFFLINE, rtt=None)

    @model_validator(mode="after")
    def _infer_status(self) -> "Self":
        """
        Infer the health status based on the round-trip time (RTT).

        Parameters
        ----------
        values : dict[str, object]
            The model values.

        Returns
        -------
        dict[str, object]
            The updated model values with inferred health status.
        """
        match self.success_rate():
            case rate if rate >= 0.95:
                self.status = HealthStatus.HEALTHY
            case rate if rate > 0:
                self.status = HealthStatus.UNSTABLE
            case _:
                self.status = HealthStatus.OFFLINE
        return self

    @computed_field
    @property
    def summary(self) -> PingHistorySummary:
        """
        Compute a summary of the ping history.

        Returns
        -------
        PingHistorySummary
            A summary of the ping history, including total attempts, successful attempts,
            success rate, mean RTT, and max RTT.
        """
        total = 0
        successful = 0
        rtts = []
        current = self

        while current is not None:
            total += 1
            if current.rtt is not None:
                successful += 1
                rtts.append(current.rtt)
            current = (
                current.previous_result if current.previous_result is not None else None
            )

        mean_rtt = sum(rtts) / len(rtts) if rtts else None
        max_rtt = max(rtts) if rtts else None

        return PingHistorySummary(
            total=total,
            successful=successful,
            success_rate=successful / total if total > 0 else 0.0,
            mean_rtt=mean_rtt,
            max_rtt=max_rtt,
        )

    def prune_chain(self, *, max_length: int = 10) -> None:
        """
        Prune the chain of previous results to a maximum length.

        Parameters
        ----------
        max_length : int, optional
            The maximum length of the chain. Default is 10.
        """
        if max_length <= 1:
            self.previous_result = None
            return

        current = self
        count = 1
        while current.previous_result is not None and count < max_length:
            count += 1
            current = current.previous_result

        if current.previous_result is not None:
            current.previous_result = None

    def success_rate(
        self, *, up_to: int | None = None, max_rtt: float | None = None
    ) -> float:
        """
        Calculate the success rate of ping responses in the chain.

        Parameters
        ----------
        up_to : int | None, optional
            The maximum number of previous results to consider. If None, all previous
            results are considered.

        max_rtt : float | None, optional
            The maximum round-trip time (RTT) to consider a ping response successful. If
            None, all RTTs are considered.

        Returns
        -------
        float
            The success rate of ping responses in the chain.
        """
        success_count = 0
        total_count = 0
        current = self

        while current is not None and (up_to is None or total_count < up_to):
            if current.rtt is not None and (max_rtt is None or current.rtt <= max_rtt):
                success_count += 1
            total_count += 1
            current = (
                current.previous_result if current.previous_result is not None else None
            )

        return success_count / total_count if total_count > 0 else 0.0
