import http
from datetime import UTC, datetime
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field

from ...models.common import GLOBAL_MODEL_CONFIG
from ...models.nr5103e import NR5103ESession, endpoints


class RebootResponse(BaseModel):
    """
    Response model for the reboot endpoint.
    """

    model_config = GLOBAL_MODEL_CONFIG

    result: Literal["success"]
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="The timestamp when the reboot was initiated.",
    )


async def reboot(
    session: NR5103ESession,
) -> RebootResponse:
    """
    Force a reboot of the NR5103E device using the provided session.
    """
    # Ensure the session is logged in before attempting to reboot the device,
    # as we need the session key.
    await session.ensure_logged_in()

    if session.session_key is None:
        raise HTTPException(
            status_code=http.HTTPStatus.BAD_GATEWAY,
            detail="Session key is missing; cannot reboot the device.",
        )

    status, response = await session.call(
        endpoint=endpoints.reboot_endpoint,
        query=endpoints.RebootQuery(session_key=session.session_key),
        body=None,
    )

    if status == http.HTTPStatus.OK:
        session.reboot_epoch += 1
        return RebootResponse(result="success")

    # Should be unreachable due to the expected_status in the endpoint definition, but we handle it just in case.
    raise HTTPException(
        status_code=status,
        detail=f"Failed to reboot the NR5103E device. Status: {status}, Response: {response}",
    )
