import http
from typing import TypeVar

from fastapi import HTTPException
from httpx2 import AsyncClient
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from ...common import GLOBAL_MODEL_CONFIG
from ...logger import logger

B = TypeVar("B", bound=BaseModel | None)
Q = TypeVar("Q", bound=BaseModel | None)
R = TypeVar("R", bound=BaseModel | None)

DEFAULT_ATTEMPTS = 3
"""
Default number of attempts for calling an NR5103E web endpoint.
"""

DEFAULT_TIMEOUT = 5
"""
Default timeout for calling an NR5103E web endpoint, in seconds.
"""

ENDPOINT_MODEL_CONFIG = GLOBAL_MODEL_CONFIG.copy()
ENDPOINT_MODEL_CONFIG.update(
    {
        "arbitrary_types_allowed": True,
    }
)


class NR5103EWebEndpoint[Q, B, R](BaseModel):
    """
    Protocol for NR5103E web endpoints.
    """

    model_config = ENDPOINT_MODEL_CONFIG

    method: http.HTTPMethod
    path: str

    query_type: type[Q] | None = None
    body_type: type[B] | None = None
    response_type: type[R] | None = None

    expected_status: tuple[http.HTTPStatus, ...] | range = Field(
        default=(http.HTTPStatus.OK,),
        description="The expected HTTP status codes for a meaningful response.",
    )

    async def call(
        self,
        *,
        client: AsyncClient,
        query: Q = None,
        body: B = None,
        attempts: int = DEFAULT_ATTEMPTS,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> tuple[http.HTTPStatus, R]:
        """
        Call the endpoint with the given session, query parameters, and request body.

        Parameters
        ----------
        client : AsyncClient
            The HTTPX client instance to use for the request.

        query : Q | None, optional
            The query parameters to include in the request, by default None.

        body : B | None, optional
            The request body to include in the request, by default None.

        attempts : int, optional
            The number of attempts to make for the request, by default DEFAULT_ATTEMPTS.

        timeout : float, optional
            The timeout for the request in seconds, by default DEFAULT_TIMEOUT.

        Returns
        -------
        http.HTTPStatus
            The HTTP status code of the response.
        R
            The response from the endpoint, parsed into the specified response type.

        Raises
        ------
        HTTPException
            If the request fails after the specified number of attempts.
        """
        response = None
        last_exc = None
        for attempt in range(attempts):
            try:
                response = await client.request(
                    method=self.method.value,
                    url=self.path,
                    params=query.model_dump(by_alias=True)
                    if isinstance(query, BaseModel)
                    else None,
                    json=body.model_dump(by_alias=True)
                    if isinstance(body, BaseModel)
                    else None,
                    timeout=timeout,
                    follow_redirects=True,
                )
                if response.status_code not in self.expected_status:
                    logger.error(
                        "{status_code} {reason_phrase} for endpoint {path}:\n{text}",
                        status_code=response.status_code,
                        reason_phrase=response.reason_phrase,
                        path=self.path,
                        text=response.text,
                    )

                try:
                    if isinstance(self.response_type, type) and issubclass(
                        self.response_type, BaseModel
                    ):
                        return http.HTTPStatus(
                            response.status_code
                        ), self.response_type.model_validate(response.json())

                    # The only logical reason to reach this point is if the response type is
                    # None, in which case we return the raw JSON response.
                    return http.HTTPStatus(response.status_code), TypeAdapter(
                        None
                    ).validate_python(response.json())
                except ValidationError as exc:
                    raise HTTPException(
                        status_code=502,
                        detail=f"Response from endpoint {self.path} could not be parsed into {type(self.response_type).__name__}:\n{exc}",
                    )

            except Exception as exc:  # noqa: BLE001
                if attempt < attempts - 1:
                    continue

                last_exc = exc

        raise HTTPException(
            status_code=response.status_code if response else 503,
            detail=f"Failed to call endpoint {self.path} after {attempts:,} attempts: {last_exc}",
        )
