import asyncio
import websockets

async def hello(websocket, path):
    while True:
        await websocket.send('hello begin')
        name = await websocket.recv()
        print(f"< {name}")
        await websocket.send('hello end')


start_server = websockets.serve(hello, "127.0.0.1", 5001)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()