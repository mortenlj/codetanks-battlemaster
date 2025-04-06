from lightkube import AsyncClient
from triotp import supervisor

from battlemaster.k8s.resources.battle import Battle
from battlemaster.reconcilers import battle
from battlemaster.servers import manager
from battlemaster.servers.types import ReconcilerConfig


async def start(client: AsyncClient):
    configs = [
        ReconcilerConfig(
            name='battle',
            resource=Battle,
            reconciler=battle.Reconciler(client),
        )
    ]
    children = [
        supervisor.child_spec(
            id='manager',
            task=manager.start,
            args=[client, configs],
        ),
    ]
    opts = supervisor.options()
    await supervisor.start(children, opts)
