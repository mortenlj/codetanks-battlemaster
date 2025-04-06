from lightkube import AsyncClient
from lightkube.core import resource
from triotp import mailbox
from triotp.helpers import current_module
from triotp.logging import getLogger

from battlemaster.servers.types import Key

__module__ = current_module()


class Informer:
    _res: resource.Resource
    _client: AsyncClient
    _reconciler_name: str

    def __init__(self, res: resource.Resource, client: AsyncClient, reconciler_name: str):
        self._res = res
        self._client = client
        self._reconciler_name = reconciler_name

    async def watch(self: "Informer"):
        """Watch for changes in the resource and update the cache."""
        logger = getLogger(f"{__name__}.{self._reconciler_name}")
        logger.debug(f"Watching {self._res} for {self._reconciler_name}")

        async for obj in (objlist := self._client.list(self._res)):
            key = Key.from_obj(obj)
            logger.debug(f"Found {key}")
            await mailbox.send(self._reconciler_name, key)

        async for event, obj in self._client.watch(self._res, resource_version=objlist.resourceVersion):
            key = Key.from_obj(obj)
            logger.debug(f"Received event {event} for {key}")
            await mailbox.send(self._reconciler_name, key)


async def start(res: resource.Resource, client: AsyncClient, reconciler_name: str):
    informer = Informer(res, client, reconciler_name)
    await informer.watch()
