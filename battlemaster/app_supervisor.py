from hypercorn.config import Config
from triotp import supervisor

from battlemaster import asgi


async def start():
    config = Config()
    config.bind = ["localhost:8000"]

    children = [
        supervisor.child_spec(
            id='asgi',
            task=asgi.start,
            args=[],
        ),
    ]
    opts = supervisor.options(
        max_restarts=3,
        max_seconds=5,
    )
    await supervisor.start(children, opts)
