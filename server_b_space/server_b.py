import os
import json
import asyncio
import aiohttp
from aiohttp import web
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    RTCConfiguration,
    RTCIceServer,
)
from aiortc.contrib.media import MediaPlayer

# 設置音頻文件路徑
audio_file = os.path.join(os.path.dirname(__file__), "demo-instruct.wav")


async def offer(request):
    # 添加 STUN 服務器
    stun_servers = RTCConfiguration([RTCIceServer(urls="stun:stun.l.google.com:19302")])
    pc = RTCPeerConnection(stun_servers)
    pc = RTCPeerConnection()

    # 播放音頻文件
    player = MediaPlayer(audio_file)
    pc.addTrack(player.audio)  # 將音頻流添加到 PeerConnection 中

    # 創建 offer
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    # 發送 offer 到 Server A
    headers = {"Content-Type": "application/json"}
    offer_json = json.dumps(
        {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
    )

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://127.0.0.1:8080/offer", headers=headers, data=offer_json
        ) as resp:
            answer = await resp.json()

    # 設置 Server A 的 answer 作為遠程描述
    remote_description = RTCSessionDescription(sdp=answer["sdp"], type=answer["type"])
    await pc.setRemoteDescription(remote_description)

    return web.Response(text="Audio stream sent to Server A")


async def start_server():
    app = web.Application()
    app.router.add_post("/send-audio", offer)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8081)
    await site.start()


if __name__ == "__main__":
    # 創建一個新的事件循環並設置為當前上下文的循環，確保後續所有的異步任務都在這個循環中執行。這樣做可以避免與其他已存在的事件循環衝突（例如在某些情況下，如在不同線程中創建事件循環時）
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # 通過 run_until_complete 方法運行 start_server() 協程函數。這樣可以確保伺服器的設置（如路由配置和網絡綁定）在事件循環開始之前完成
    loop.run_until_complete(start_server())
    # 通過 run_forever 方法保持事件循環運行，這樣 server 可以持續處理進來的客戶端請求。這一步是必須的，否則伺服器將在完成初始化協程後立即退出
    loop.run_forever()
