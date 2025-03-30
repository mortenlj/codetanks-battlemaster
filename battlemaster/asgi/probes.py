class App:
    async def __call__(self, scope, receive, send):
        while True:
            event = await receive()
            if (
                    event['type'] == 'http.request' and
                    not event.get('more_body', False)
            ):
                if scope['path'] == '/_/live':
                    await self.send_msg(send, "I am alive!")
                elif scope['path'] == '/_/ready':
                    await self.send_msg(send, "I am ready!")
                else:
                    await self.send_404(send)
            elif event['type'] == 'http.disconnect':
                break
            elif event['type'] == 'lifespan.startup':
                await send({'type': 'lifespan.startup.complete'})
            elif event['type'] == 'lifespan.cleanup':
                await send({'type': 'lifespan.cleanup.complete'})
            elif event['type'] == 'lifespan.shutdown':
                await send({'type': 'lifespan.shutdown.complete'})

    async def send_msg(self, send, msg):
        data = msg.encode('utf-8')
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [(b'content-length', b"%d" % len(data))],
        })
        await send({
            'type': 'http.response.body',
            'body': data,
            'more_body': False,
        })

    async def send_404(self, send):
        await send({
            'type': 'http.response.start',
            'status': 404,
            'headers': [(b'content-length', b'0')],
        })
        await send({
            'type': 'http.response.body',
            'body': b'',
            'more_body': False,
        })


if __name__ == '__main__':
    import trio
    from hypercorn.trio import serve
    from hypercorn.config import Config

    config = Config()
    config.bind = ["localhost:8000"]
    trio.run(serve, App(), config)
