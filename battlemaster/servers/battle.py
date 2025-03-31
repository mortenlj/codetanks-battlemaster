from triotp import mailbox
from triotp.logging import getLogger


class Reconciler:
    def __init__(self):
        pass

    async def reconcile(self, key):
        logger = getLogger(__name__)
        logger.info(f"Reconciling {key}")


async def start(name: str):
    reconciler = Reconciler()
    async with mailbox.open(name=name) as mid:
        logger = getLogger(__name__)
        logger.info(f"Starting reconciler {name}")
        while True:
            key = await mailbox.receive(mid)
            logger.debug(f"Received key {key} for {name}")
            await reconciler.reconcile(key)
