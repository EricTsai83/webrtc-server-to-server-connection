import os
import asyncio
from aiohttp import web
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    RTCConfiguration,
    RTCIceServer,
)
from aiortc.contrib.media import MediaRecorder

# 設置音頻儲存路徑
save_path = os.path.join(os.path.dirname(__file__), "received_audio.wav")


async def offer(request):
    print("Received an offer from Server B...")

    params = await request.json()
    pc = RTCPeerConnection()

    # 添加 STUN 服務器
    stun_servers = RTCConfiguration([RTCIceServer(urls="stun:stun.l.google.com:19302")])
    pc = RTCPeerConnection(stun_servers)

    # 設置 WebRTC 記錄器，儲存音頻
    recorder = MediaRecorder(save_path)

    @pc.on("track")
    async def on_track(track):
        print(f"Receiving track: {track.kind}")
        if track.kind == "audio":
            recorder.addTrack(track)
            print("Audio track added to recorder.")

    # 設定遠端描述 (SDP)
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    await pc.setRemoteDescription(offer)
    print("Remote description set.")

    # 創建 answer，返回給 Server B
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    print("Answer created and local description set.")

    # 開始錄音，並將音頻保存到指定的文件
    await recorder.start()
    print(f"Started recording audio to {save_path}")

    # 停止錄製的處理
    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        if pc.iceConnectionState == "closed":
            await recorder.stop()
            print("Recording stopped.")

    response = {
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type,
    }

    return web.json_response(response)


async def start_server():
    app = web.Application()
    app.router.add_post("/offer", offer)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("Server A is running on http://0.0.0.0:8080")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_server())
    loop.run_forever()
