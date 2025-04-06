from triotp.logging import getLogger


class Reconciler:
    async def reconcile(self, key):
        logger = getLogger(__name__)
        logger.info(f"Reconciling {key}")
