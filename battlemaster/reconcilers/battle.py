from lightkube import AsyncClient
from triotp.logging import getLogger

from battlemaster.k8s.resources.battle import Battle


class Reconciler:
    def __init__(self, client: AsyncClient):
        self._client = client

    async def reconcile(self, key):
        logger = getLogger(__name__)
        logger.info(f"Reconciling {key}")
        battle = await self._client.get(Battle, name=key.name, namespace=key.namespace)
        logger.info(f"Found Battle: {battle}")