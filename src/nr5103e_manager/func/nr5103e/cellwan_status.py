from ...models.nr5103e import NR5103ESession, endpoints


async def get_cellular_status(
    session: NR5103ESession,
) -> endpoints.CellWanStatusResponse:
    """
    Get the cellular status from the NR5103E device using the provided session.
    """
    _, response = await session.call(
        endpoint=endpoints.cellwan_status_endpoint,
        query=endpoints.CellWanStatusQuery(),
        body=None,
    )

    return response
