from pydantic import BaseModel, Field, IPvAnyAddress

from .. import config
from .common import GLOBAL_MODEL_CONFIG
from .nr5103e import NR5103ESession
from .ping import PingResponse


class LifeSpanData(BaseModel):
    """
    Static scope data for the lifespan of the service.
    """

    model_config = GLOBAL_MODEL_CONFIG

    ping_history: dict[IPvAnyAddress, PingResponse] = Field(
        default_factory=dict,
        description="A dictionary mapping IP addresses to their ping history.",
    )
    nr5103e_session: NR5103ESession = Field(
        default_factory=lambda: NR5103ESession(
            host=config.NR5103E_HOST,
            username=config.NR5103E_USERNAME,
            password=config.NR5103E_PASSWORD,
        ),
        description="A session object for interacting with the NR5103E device.",
    )
