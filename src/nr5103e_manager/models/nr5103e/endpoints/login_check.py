import http

from pydantic import BaseModel, Field

from .protocol import GLOBAL_MODEL_CONFIG, NR5103EWebEndpoint


class LoginCheckResponse(BaseModel):
    """
    The response from the NR5103E device after a login attempt.
    """

    model_config = GLOBAL_MODEL_CONFIG

    result: str = Field(
        ...,
        description="The result of the login check, typically `ZCFG_SUCCESS` for a successful login.",
    )


login_check_endpoint = NR5103EWebEndpoint[None, None, LoginCheckResponse](
    path="/cgi-bin/UserLoginCheck",
    method=http.HTTPMethod.POST,
    query_type=None,
    body_type=None,
    response_type=LoginCheckResponse,
    expected_status=(http.HTTPStatus.OK, http.HTTPStatus.UNAUTHORIZED),
)
"""
The NR5103E web endpoint for checking the login status of the device.
"""
