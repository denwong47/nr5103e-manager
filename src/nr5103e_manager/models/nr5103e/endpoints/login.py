import base64
import http

from pydantic import BaseModel, Field, computed_field

from .protocol import GLOBAL_MODEL_CONFIG, NR5103EWebEndpoint


class LoginBody(BaseModel):
    """
    The body of the login request to the NR5103E device.

    The field naming on the login form is non-sensical, so we use aliases to map the
    fields to the correct names.
    """

    model_config = GLOBAL_MODEL_CONFIG

    username: str = Field(
        ...,
        description="The username for the NR5103E device.",
        serialization_alias="Input_Account",
        min_length=1,
    )
    password: str = Field(
        ...,
        description="The password for the NR5103E device.",
        exclude=True,
    )
    language: str = Field(
        default="en",
        description="The language for the NR5103E device.",
        serialization_alias="currLang",
        min_length=2,
        max_length=2,
    )
    remember_password: int = Field(
        default=0,
        description="Whether to remember the password for the NR5103E device.",
        serialization_alias="RememberPassword",
        ge=0,
        le=1,
    )
    sha512_password: bool = Field(
        default=False,
        description="Whether to use SHA512 hashing for the password.",
        serialization_alias="SHA512_password",
    )

    @computed_field(
        alias="Input_Passwd",
    )
    def password_encoded(self) -> str:
        """
        The password encoded in base64 for the NR5103E device.
        """
        return base64.b64encode(self.password.encode("utf-8")).decode("utf-8")


class LoginResponse(BaseModel):
    """
    The response from the NR5103E device after a login attempt.
    """

    model_config = GLOBAL_MODEL_CONFIG

    session_key: int = Field(
        ...,
        description="The session key for the NR5103E device.",
        validation_alias="sessionkey",
    )
    theme_color: str = Field(
        ...,
        description="The theme color for the NR5103E device.",
        validation_alias="ThemeColor",
    )
    change_password: bool = Field(
        ...,
        description="Whether the user is required to change their password.",
        validation_alias="changePw",
    )
    show_skip_button: bool = Field(
        ...,
        description="Whether to show the skip button on the NR5103E device.",
        validation_alias="showSkipBtn",
    )
    quick_start: bool = Field(
        ...,
        description="Whether to show the quick start guide on the NR5103E device.",
        validation_alias="quickStart",
    )
    username: str = Field(
        ...,
        description="The login account for the NR5103E device.",
        validation_alias="loginAccount",
    )
    login_level: str = Field(
        ...,
        description="The login level for the NR5103E device. The meaning of this field is unknown, but it is typically `medium` for a successful login.",
        validation_alias="loginLevel",
    )
    result: str = Field(
        ...,
        description="The result of the login attempt, typically `ZCFG_SUCCESS` for a successful login.",
        validation_alias="result",
    )


login_endpoint = NR5103EWebEndpoint[None, LoginBody, LoginResponse](
    path="/UserLogin",
    method=http.HTTPMethod.POST,
    query_type=None,
    body_type=LoginBody,
    response_type=LoginResponse,
    expected_status=(http.HTTPStatus.OK, http.HTTPStatus.UNAUTHORIZED),
)
"""
The NR5103E web endpoint for logging in to the device.

This will set the cookies on the session, which will be used for subsequent requests to the device.
"""
