from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from pydantic import IPvAnyAddress, TypeAdapter, ValidationError

from .func import nr5103e, ping
from .lifespan import create_lifespan
from .models.health_check import HealthCheckResponse
from .models.lifespan import LifeSpanData
from .models.nr5103e import NR5103ESession
from .models.nr5103e.endpoints import CellWanStatusResponse
from .models.ping import PingRequestQuery, PingResponse

data = LifeSpanData()

app = FastAPI(lifespan=create_lifespan(data))


@app.get("/health")
async def health_check() -> HealthCheckResponse:
    """
    Health check endpoint to verify the service is running.
    """
    return HealthCheckResponse.from_lifespan(data)


@app.get("/ping/{host}")
async def ping_host(
    host: str,
    q: Annotated[PingRequestQuery, Query()],
) -> PingResponse:
    """
    Ping a host and return the response.
    """
    try:
        host_ip = TypeAdapter(IPvAnyAddress).validate_python(host)
    except ValidationError:
        raise HTTPException(status_code=400, detail=f"Invalid host IP address: {host}")

    count = q.count
    response = None
    async for response in ping.recurring_ping_host(
        host_ip, timeout=q.timeout, history=q.count, min_interval=q.interval
    ):
        count -= 1
        if count <= 0:
            break

    return response or PingResponse.empty(host=host_ip)


@app.get("/modem/cellular")
async def get_cellular_info() -> CellWanStatusResponse:
    """
    Get cellular information from the NR5103E device.
    """
    info = await nr5103e.get_cellular_status(session=data.nr5103e_session)
    return info


@app.get("/modem/session")
async def get_modem_session_info() -> NR5103ESession:
    """
    Get the current session information for the NR5103E device.
    """
    return data.nr5103e_session


@app.post("/modem/reboot")
async def reboot_modem() -> nr5103e.RebootResponse:
    """
    Reboot the cellular module of the NR5103E device.
    """
    response = await nr5103e.reboot(session=data.nr5103e_session)
    return response
