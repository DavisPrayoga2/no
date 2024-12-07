import asyncio
import random
import ssl
import json
import time
import uuid
import websockets
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from loguru import logger
from fake_useragent import UserAgent

# Tetapkan user_id
USER_ID = "2oSjgJ8VS3Rg9j46tDpo0v17ttM"

# Inisialisasi User-Agent dan Counter Reboot
user_agent = UserAgent(os='windows', platforms='pc', browsers='chrome')
random_user_agent = user_agent.random
reboot_counter = 0  # Counter reboot


async def connect_to_wss(user_id):
    device_id = str(uuid.uuid4())
    logger.info(f"Device ID: {device_id}")
    while True:
        try:
            custom_headers = {
                "User-Agent": random_user_agent,
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            urilist = ["wss://proxy2.wynd.network:4444/", "wss://proxy2.wynd.network:4650/"]
            uri = random.choice(urilist)
            server_hostname = "proxy2.wynd.network"

            logger.info(f"Connecting to WebSocket server at {uri}...")
            async with websockets.connect(uri, ssl=ssl_context, extra_headers=custom_headers,
                                          server_hostname=server_hostname) as websocket:
                async def send_ping():
                    while True:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        logger.debug(f"Sending PING: {send_message}")
                        await websocket.send(send_message)
                        await asyncio.sleep(5)

                asyncio.create_task(send_ping())

                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(f"Received: {message}")

                    if message.get("action") == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "desktop",
                                "version": "4.28.1",
                            }
                        }
                        logger.debug(f"Sending AUTH Response: {auth_response}")
                        await websocket.send(json.dumps(auth_response))

                    elif message.get("action") == "PONG":
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        logger.debug(f"Sending PONG Response: {pong_response}")
                        await websocket.send(json.dumps(pong_response))

        except ConnectionClosedError as e:
            logger.warning(f"Connection closed with error: {e}. Retrying in 10 seconds...")
            await asyncio.sleep(10)
        except ConnectionClosedOK:
            logger.info("Connection closed gracefully. Restarting in 10 seconds...")
            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            logger.info("Retrying connection in 10 seconds...")
            await asyncio.sleep(10)


async def auto_reboot_task():
    """Task to reboot the WebSocket connection every 1 hour."""
    global reboot_counter
    while True:
        logger.info("Reboot timer started. Rebooting WebSocket connection in 1 hour...")
        await asyncio.sleep(3600)  # Tunggu 1 jam
        reboot_counter += 1
        logger.info(f"Rebooting WebSocket connection... (Total Reboots: {reboot_counter})")
        # Restart the main WebSocket connection task
        asyncio.create_task(connect_to_wss(USER_ID))


async def main():
    # Jalankan koneksi WebSocket dan task reboot otomatis
    asyncio.create_task(auto_reboot_task())  # Task untuk reboot setiap 1 jam
    await connect_to_wss(USER_ID)


if __name__ == '__main__':
    asyncio.run(main())
