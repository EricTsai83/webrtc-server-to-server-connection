## Prerequisite

### 建立 vitual environment

`python -m venv venv`

### 激活環境

`source ./venv/bin/activate`

### 更新 pip

`pip install --upgrade pip`

### 安裝套件

`pip install -r requirements.txt`

## 執行過程

### launch server A

`python server_a_space/server_a.py`

### launch server B

`python server_b_space/server_b.py`

### 透過 API 請求送出音檔的行為

執行之前請先確保 server_a_space 下是沒有 received_audio 檔案的，否則無法觀察是否真的有透過 server b 將音檔傳給 server a

`curl -X POST http://localhost:8081/send-audio`

### 其他

`pip freeze > requirements.txt`

## Server-to-Server 音檔傳輸的邏輯說明

使用 WebRTC 建構 P2P 連線，並通過 STUN 服務器來確保在不同網絡環境中進行 NAT 穿透。

### 概述

1. Server B 播放音檔並創建一個 WebRTC 連接（Offer）。
2. Server B 通過 HTTP 將 Offer 發送給 Server A。
3. Server A 接收 Offer，設置 WebRTC 連接，並創建 Answer 返回給 Server B。
4. Server B 接收 Answer，完成 WebRTC P2P 連接。
5. 音頻資料通過 WebRTC 並使用 SRTP 傳輸，Server A 接收並錄製音頻數據。

### 詳細步驟

#### server B

1. Server B 生成並發送 Offer
2. Server B 播放音頻文件並創建 RTCPeerConnection。
3. Server B 使用 STUN 服務器來協助 NAT 穿透。
4. Server B 創建一個 SDP Offer 並設置本地描述（local description）。
5. Server B 將生成的 Offer 作為 JSON 通過 HTTP 發送給 Server A。

#### server A

1. Server A 接收並處理 Offer
2. Server A 接收到 Server B 的 Offer，創建 RTCPeerConnection。
3. Server A 使用 STUN 服務器來協助 NAT 穿透。
4. Server A 設置遠端描述（remote description）為接收到的 Offer。
5. Server A 使用 pc.on("track") 方法處理接收到的音頻流。
6. Server A 創建一個 SDP Answer 並設置本地描述（local description）。
7. Server A 將回應的 Answer 作為 JSON 返回給 Server B。

### 總結

- 信令交換: 通過 HTTP 交換 SDP Offer 和 Answer，完成 P2P 連接的設置。
- 連接設置: 兩個伺服器各自設置本地和遠端描述，並使用 STUN 服務器協助 NAT 穿透。
- 音頻流數據處理:
  - Server B 使用 pc.addTrack(player.audio) 將音頻流添加到 PeerConnection，這樣音頻數據可以通過 WebRTC 發送。
  - Server A 使用 pc.on("track") 回調函數來處理接收到的音頻流，並使用 recorder.addTrack(track) 添加到 MediaRecorder 進行錄製。
  - 音頻錄製通過 await recorder.start() 開始，一旦連接結束，會通過 await recorder.stop() 停止錄製。
