from lightkube import AsyncClient
from triotp import mailbox
from triotp import supervisor
from triotp.logging import getLogger

from battlemaster.servers import informer
from battlemaster.servers.types import ReconcilerConfig, Reconciler


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
            task=_start_reconciler,
            args=[rc.name, rc.reconciler],
        ) for rc in configs
    ])

    await supervisor.start(children, opts)


async def _start_reconciler(name: str, reconciler: Reconciler):
    async with mailbox.open(name=name) as mid:
        logger = getLogger(__name__)
        logger.info(f"Starting reconciler {name}")
        while True:
            key = await mailbox.receive(mid)
            logger.debug(f"Received key {key} for {name}")
            await reconciler.reconcile(key)
