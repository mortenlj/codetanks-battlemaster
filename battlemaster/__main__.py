from triotp import node, application
from triotp.helpers import current_module

from battlemaster import app_supervisor

__module__ = current_module()


def main():
    node.run(apps=[
        application.app_spec(
            module=__module__,
            start_arg=None,
            permanent=False,
        )
    ])


async def start(_start_arg):
    await app_supervisor.start()


if __name__ == '__main__':
    main()
