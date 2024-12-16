import requests
import time
import asyncio
import json
import ssl
import uuid
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from websockets_proxy import Proxy, proxy_connect
from fake_useragent import UserAgent
from loguru import logger
import schedule
import base64
# Tetapkan user_id
USER_ID = "2oSjgJ8VS3Rg9j46tDpo0v17ttM"

def log_reputation(completeness, consistency, timeliness, availability):
    logger.info(f"Complete: {completeness}, Konsistensi: {consistency}, Waktu: {timeliness}, Ketersediaan: {availability}")
async def connect_to_wss(socks5_proxy, user_id, traffic_type='PET'):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
    logger.info(device_id)
    user_agent = UserAgent()
    random_user_agent = user_agent.random

    while True:
        try:
            await asyncio.sleep(1)
            custom_headers = {"User-Agent": random_user_agent}
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            urilist = ["wss://proxy.wynd.network:4444/", "wss://proxy.wynd.network:4650/", "wss://proxy2.wynd.network:4444/", "wss://proxy2.wynd.network:4650/", "wss://proxy3.wynd.network:4444/", "wss://proxy3.wynd.network:4650/"]
            uri = random.choice(urilist)

            async with websockets.connect(uri, ssl=ssl_context, server_hostname=server_hostname,
                                          extra_headers=custom_headers) as websocket:
                async def send_ping():
                    while True:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        try:
                            await websocket.send(send_message)
                            logger.debug(send_message)
                        except Exception as e:
                            logger.error(f"Gagal kirim PING: {e}")
                        await asyncio.sleep(2)

                asyncio.create_task(send_ping())

                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(message)

                    completeness = True 
                    consistency = True
                    timeliness = True 
                    availability = True 

                    log_reputation(completeness, consistency, timeliness, availability)

                    if message.get("action") == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "extension",
                                "version": "3.3.2"
                            }
                        }
                        try:
                            await websocket.send(json.dumps(auth_response))
                            logger.debug(auth_response)
                        except Exception as e:
                            logger.error(f"Gagal kirim respon AUTH: {e}")

                    elif message.get("action") == "PONG":
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        try:
                            await websocket.send(json.dumps(pong_response))
                            logger.debug(pong_response)
                        except Exception as e:
                            logger.error(f"Gagal kirim respon PONG: {e}")

        except Exception as e:
            pass 
            await asyncio.sleep(10) 

async def main():
    with open(user_ids_file, 'r') as file:
        user_ids = file.read().splitlines()

    tasks = [asyncio.ensure_future(connect_to_wss(proxy, user_id.strip(), traffic_type='PET'))]
    await asyncio.gather(*tasks)
