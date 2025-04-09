from lightkube import AsyncClient, ApiError
from triotp.logging import getLogger

from battlemaster.k8s.models import battle as m_battle
from battlemaster.k8s.resources import battle as r_battle


class Reconciler:
    def __init__(self, client: AsyncClient):
        self._client = client

    async def reconcile(self, key):
        logger = getLogger(__name__)
        logger.info(f"Reconciling {key}")
        try:
            battle = await self._client.get(r_battle.Battle, name=key.name, namespace=key.namespace)
        except ApiError as e:
            if e.status.code == 404:
                logger.info(f"Battle {key} not found, already deleted?")
                return None
        logger.info(f"Found Battle: {battle}")
        battle.status = battle.status or m_battle.BattleStatus()
        status = battle.status
        try:
            status.observedGeneration = battle.metadata.generation
            logger.info(f"Observed generation: {status.observedGeneration}")
            # TODO: self.do_stuff(battle)
        finally:
            battle_status = r_battle.Battle.Status(
                status=battle.status,
            )
            await self._client.apply(battle_status, name=key.name, namespace=key.namespace,
                                     field_manager="codetanks.ibidem.no/battlemaster")
