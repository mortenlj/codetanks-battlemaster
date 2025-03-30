from triotp import supervisor

from hypercorn.config import Config
from hypercorn.trio import serve

from battlemaster.asgi import probes


async def start():
    config = Config()
    config.bind = ["0.0.0.0:8000"]

    children = [
        supervisor.child_spec(
            id='probes',
            task=serve,
            args=[probes.App(), config],
        ),
    ]
    opts = supervisor.options()
    await supervisor.start(children, opts)
