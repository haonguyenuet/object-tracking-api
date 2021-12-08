from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient
from fastapi.responses import HTMLResponse

import uvicorn

import time
from typing import List
from os import path

video_txt_path = 'deepsort_yolov5/inference/output/video.txt'

# FastAPI 
app = FastAPI(
    title="Serving YOLO",
    description="""Visit port 8088/docs for the FastAPI documentation.""",
    version="0.0.1",
)

# WS 
class ConnectionManager:
    """Web socket connection manager."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data):
        for connection in self.active_connections:
            await connection.send_json(data)

con_mgr  = ConnectionManager()


# Client Test
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>FASTAPI</title>
    </head>
    <body>
        <h1>WebSocket Test</h1>
        <label>Client ID: <input type="number" id="clientId" autocomplete="off" value="111"/></label>
        <button onclick="connect(event)">Connect</button>
        <ul id='messages'>
        </ul>
        <script>
            var ws = null;
            function connect(event) {
                var clientId = document.getElementById("clientId")
                ws = new WebSocket("ws://localhost:8000/v1/mot/yolov5_ws/" + clientId.value);
                ws.onmessage = function(event) {
                    var messages = document.getElementById('messages')
                    messages.innerHTML = ''
                    var message = document.createElement('li')
                    var content = document.createTextNode(event.data)
                    message.appendChild(content)
                    messages.appendChild(message)
                };
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""

# Routes 
@app.get("/")
async def home():
    return HTMLResponse(html)


@app.get("/v1/mot/yolov5")
def mot_yolov5():
    start_time = time.time()
    data = []
    with open(video_txt_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            temp = line.split()
            x, y, w, h = map(float,temp[2:6])
            data.append({
                'x': x,
                'y': y,
                'w': w,
                'h': h
            })
    process_time = time.time() - start_time
    print("Time: ", process_time)
    return data

@app.websocket("/v1/mot/yolov5_ws/{client_id}")
async def mot_yolov5_ws(websocket: WebSocket, client_id: int):
    await con_mgr.connect(websocket)    
    try:
        while path.exists(video_txt_path):
            f = open(video_txt_path, 'r')
            pre_content = ''
            curr_content = f.read()

            if pre_content != curr_content:
                objects = []
                f = open(video_txt_path, 'r')
                lines = f.readlines()

                for line in lines:
                    temp = line.split()
                    x, y, w, h = map(float,temp[2:6])
                    objects.append({
                        'x': x,
                        'y': y,
                        'w': w,
                        'h': h
                    })

                await con_mgr.broadcast({
                    "objects": objects,
                    "quantity":  len(objects)
                })
            pre_content = curr_content
    except WebSocketDisconnect:
        con_mgr.disconnect(websocket)
        await con_mgr.broadcast(f"Client #{client_id} left the chat")

# Main
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
