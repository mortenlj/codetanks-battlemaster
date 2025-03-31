from lightkube import AsyncClient
from triotp import supervisor

from battlemaster.k8s.resources.battle import Battle
from battlemaster.servers import manager, battle


async def start(client: AsyncClient):
    configs = [
        manager.ReconcilerConfig(
            name="battle",
            resource=Battle,
        )
    ]
    children = [
        supervisor.child_spec(
            id='manager',
            task=manager.start,
            args=[client, configs],
        ),
        supervisor.child_spec(
            id='battle',
            task=battle.start,
            args=["battle"],
        ),
    ]
    opts = supervisor.options()
    await supervisor.start(children, opts)
