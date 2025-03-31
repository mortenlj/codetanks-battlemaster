from triotp import node, application
from triotp.helpers import current_module
from triotp.logging import LogLevel, getLogger

from battlemaster import app_supervisor
from battlemaster.config import settings

__module__ = current_module()


def main():
    log_level = LogLevel.DEBUG if settings.debug else LogLevel.INFO

    node.run(
        loglevel=log_level,
        logformat="[{record.time:%Y-%m-%d %H:%M:%S.%f%z}|{record.level_name:.5}] {record.message} ({record.channel})",
        apps=[
            application.app_spec(
                module=__module__,
                start_arg=None,
                permanent=False,
            )
        ]
    )


async def start(_start_arg):
    logger = getLogger(__name__)
    logger.debug(f"Starting BattleMaster with configuration {settings}")
    await app_supervisor.start()


if __name__ == '__main__':
    main()
