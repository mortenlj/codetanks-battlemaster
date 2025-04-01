import types
from dataclasses import dataclass

from lightkube import AsyncClient
from lightkube.core import resource
from triotp import supervisor
from triotp.logging import getLogger

from battlemaster.servers import informer


@dataclass
class ReconcilerConfig:
    resource: resource.Resource
    reconciler: types.ModuleType

    @property
    def name(self):
        return self.reconciler.__name__


async def start(client: AsyncClient, configs: list[ReconcilerConfig]):
    logger = getLogger(__name__)
    logger.debug(f"Starting manager with {len(configs)} reconcilers")
    opts = supervisor.options()
    children = [
        supervisor.child_spec(
            id=rc.name,
            task=informer.start,
            args=[rc.resource, client, rc.name],
        ) for rc in configs
    ]
    children.extend([
        supervisor.child_spec(
            id=rc.name,
            task=rc.reconciler.start,
            args=[rc.name],
        ) for rc in configs
    ])

    await supervisor.start(children, opts)
