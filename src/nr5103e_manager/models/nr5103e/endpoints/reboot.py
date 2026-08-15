import http

from pydantic import BaseModel, Field

from .protocol import GLOBAL_MODEL_CONFIG, NR5103EWebEndpoint


class RebootQuery(BaseModel):
    """
    The query parameters for the reboot request to the NR5103E device.
    """

    model_config = GLOBAL_MODEL_CONFIG

    session_key: int = Field(
        ...,
        description="The session key for the NR5103E device.",
        serialization_alias="sessionkey",
    )


class RebootResponse(BaseModel):
    """
    The response from the NR5103E device after a reboot attempt.
    """

    model_config = GLOBAL_MODEL_CONFIG

    result: str = Field(
        ...,
        description="The result of the reboot operation, typically `ZCFG_SUCCESS` for a successful reboot.",
    )


reboot_endpoint = NR5103EWebEndpoint[RebootQuery, None, RebootResponse](
    path="/cgi-bin/Reboot",
    method=http.HTTPMethod.POST,
    query_type=RebootQuery,
    body_type=None,
    response_type=RebootResponse,
    expected_status=(http.HTTPStatus.OK,),
)
"""
The NR5103E web endpoint for rebooting the device.
"""
