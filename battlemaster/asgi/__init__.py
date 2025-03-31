import logging

from hypercorn.config import Config
from hypercorn.trio import serve
from triotp import supervisor

from battlemaster.asgi import probes
from battlemaster.config import settings


async def start():
    config = Config()
    config.bind = [f"{settings.bind_address}:{settings.port}"]
    config.accesslog = logging.getLogger('hypercorn.access')
    config.errorlog = logging.getLogger('hypercorn.error')

    children = [
        supervisor.child_spec(
            id='probes',
            task=serve,
            args=[probes.App(), config],
        ),
    ]
    opts = supervisor.options()
    await supervisor.start(children, opts)
