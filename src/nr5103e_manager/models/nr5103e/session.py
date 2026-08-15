import http
from datetime import UTC, datetime

from fastapi import HTTPException
from httpx2 import AsyncClient, Cookies
from pydantic import BaseModel, Field, IPvAnyAddress

from ..common import GLOBAL_MODEL_CONFIG
from . import endpoints
from .endpoints.protocol import NR5103EWebEndpoint

LOCAL_MODEL_CONFIG = GLOBAL_MODEL_CONFIG.copy()
LOCAL_MODEL_CONFIG.update(
    {
        "arbitrary_types_allowed": True,
    }
)


class NR5103ESession(BaseModel):
    """
    A permanent connection to the NR5103E device, with the ability to relogin if the
    session expires.
    """

    model_config = LOCAL_MODEL_CONFIG

    host: IPvAnyAddress = Field(
        ..., description="The IP address of the NR5103E device."
    )
    username: str = Field(
        ...,
        description="The username for the NR5103E device.",
        exclude=True,
    )
    password: str = Field(
        ...,
        description="The password for the NR5103E device.",
        exclude=True,
    )

    client: AsyncClient | None = Field(
        default=None,
        description="The HTTPX client instance with session cookies.",
        exclude=True,
    )
    client_epoch: int = Field(
        default=0,
        description="Each time we refresh the client, we increment this epoch. This is used to determine if the client has been refreshed since the last call.",
    )
    reboot_epoch: int = Field(
        default=0,
        description="Each time we reboot the device, we increment this epoch. This is used to determine if the device has been rebooted since the last call.",
    )
    session_key: int | None = Field(
        default=None,
        description="The session key for the NR5103E device, used for authenticated requests. This is not stored in the cookies.",
        exclude=True,
    )
    last_connected: datetime | None = None

    def _instantiate_client(self) -> None:
        """
        Reset the NR5103E client instance and increment the client epoch.
        """
        self.client_epoch += 1
        self.client = AsyncClient(
            cookies=Cookies(),  # Use a new cookie jar for each session
            base_url=f"https://{self.host}",
            verify=False,  # NR5103E uses self-signed certificates
        )

    async def is_logged_in(self) -> bool:
        """
        Check if the session is currently logged in by calling the login check endpoint.
        """
        if self.client is None:
            return False

        status, _response = await endpoints.login_check_endpoint.call(
            client=self.client,
            query=None,
            body=None,
        )

        return status == http.HTTPStatus.OK

    async def login(self) -> None:
        """
        Ensure that the session is logged in. If not, perform a login.
        """
        # Force rebuild the client to purge all cookies and reset the session state.
        # This is necessary because the NR5103E device will invalidate the session after
        # a certain period of inactivity, and we want to ensure that we always start
        # with a fresh session.
        self._instantiate_client()

        assert self.client is not None, (
            "Client should be instantiated before logging in."
        )

        status, response = await endpoints.login_endpoint.call(
            client=self.client,
            body=endpoints.LoginBody(
                username=self.username,
                password=self.password,
            ),
        )

        if status is http.HTTPStatus.OK:
            self.last_connected = datetime.now(tz=UTC)
            self.session_key = response.session_key
            return
        elif status is http.HTTPStatus.UNAUTHORIZED:
            raise HTTPException(
                status_code=http.HTTPStatus.UNAUTHORIZED,
                detail="Invalid username or password for NR5103E device.",
            )

    async def ensure_logged_in(self) -> None:
        """
        Ensure that the session is logged in. If not, perform a login.

        Raises
        ------
        HTTPException
            If the login fails after the specified number of attempts.
        """
        while not await self.is_logged_in():
            await self.login()

    async def call[Q, B, R](
        self,
        endpoint: NR5103EWebEndpoint[Q, B, R],
        *,
        query: Q = None,
        body: B = None,
    ) -> tuple[http.HTTPStatus, R]:
        """
        Call an NR5103E endpoint with the given query and body, returning the response.
        """
        await self.ensure_logged_in()

        assert self.client is not None, (
            "Client should be instantiated before making a call."
        )
        return await endpoint.call(client=self.client, query=query, body=body)
