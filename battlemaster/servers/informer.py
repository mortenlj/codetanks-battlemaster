from lightkube import AsyncClient
from lightkube.core import resource
from triotp import mailbox
from triotp.helpers import current_module
from triotp.logging import getLogger

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
            logger.debug(f"Found {_key(obj)}")
            await mailbox.send(self._reconciler_name, _key(obj))
        async for event, obj in self._client.watch(self._res, resource_version=objlist.resourceVersion):
            logger.debug(f"Received event {event} for {_key(obj)}")
            await mailbox.send(self._reconciler_name, _key(obj))


async def start(res: resource.Resource, client: AsyncClient, reconciler_name: str):
    informer = Informer(res, client, reconciler_name)
    await informer.watch()


# implementation

def _key(obj):
    return obj.metadata.name, obj.metadata.namespace
