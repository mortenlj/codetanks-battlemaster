from lightkube import AsyncClient
from triotp import supervisor

from battlemaster.servers import manager


async def start(client: AsyncClient, configs: list[manager.ReconcilerConfig]):
    children = [
        supervisor.child_spec(
            id='manager',
            task=manager.start,
            args=[client, configs],
        ),
    ]
    opts = supervisor.options()
    await supervisor.start(children, opts)
