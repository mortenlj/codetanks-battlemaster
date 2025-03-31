from lightkube import AsyncClient
from triotp import supervisor

from battlemaster import asgi, servers


async def start(client: AsyncClient):
    children = [
        supervisor.child_spec(
            id='asgi',
            task=asgi.start,
            args=[],
        ),
        supervisor.child_spec(
            id='servers',
            task=servers.start,
            args=[client],
        ),
    ]
    opts = supervisor.options(
        max_restarts=3,
        max_seconds=5,
    )
    await supervisor.start(children, opts)
