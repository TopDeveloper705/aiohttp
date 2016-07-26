#!/usr/bin/env python3
"""Example for aiohttp.web websocket server
"""

import asyncio
import os
from aiohttp.web import (Application, Response, MsgType,
                         WebSocketResponse, run_app)

WS_FILE = os.path.join(os.path.dirname(__file__), 'websocket.html')


async def wshandler(request):
    resp = WebSocketResponse()
    ok, protocol = resp.can_start(request)
    if not ok:
        with open(WS_FILE, 'rb') as fp:
            return Response(body=fp.read(), content_type='text/html')

    await resp.prepare(request)

    try:
        print('Someone joined.')
        for ws in request.app['sockets']:
            ws.send_str('Someone joined')
        request.app['sockets'].append(resp)

        async for msg in resp:
            if msg.tp == MsgType.text:
                for ws in request.app['sockets']:
                    if ws is not resp:
                        ws.send_str(msg.data)
            else:
                break

    finally:
        request.app['sockets'].remove(resp)
        print('Someone disconnected.')
        for ws in request.app['sockets']:
            ws.send_str('Someone disconnected.')
    return resp


async def on_shutdown(app):
    for ws in app['sockets']:
        await ws.close()


async def init(loop):
    app = Application(loop=loop)
    app['sockets'] = []
    app.router.add_get('/', wshandler)
    app.on_shutdown.append(on_shutdown)
    return app


loop = asyncio.get_event_loop()
app = loop.run_until_complete(init(loop))
run_app(app, loop=loop)
