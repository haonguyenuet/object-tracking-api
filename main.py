from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.testclient import TestClient
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

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

templates = Jinja2Templates(directory="templates")


# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["Process-Time"] = str(process_time)
    return response

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
        <button onclick="connect(event)">Connect WS</button>
        <button onclick="fetchObjects(event)">Get Objects</button>
        <ul id='messages'>
        </ul>
        <script>
            var ws = null;
            function connect(event) {
                var clientId = document.getElementById("clientId")
                ws = new WebSocket("ws://localhost:8000/v1/mot/yolov5_ws/" + clientId.value);
                var sendTime = (new Date()).getTime();

                ws.onmessage = function(event) {
                    var responseTime = (new Date()).getTime() - sendTime;
                    console.log(responseTime)

                    var messages = document.getElementById('messages')
                    messages.innerHTML = ''
                    var message = document.createElement('li')
                    var content = document.createTextNode(event.data)
                    message.appendChild(content)
                    messages.appendChild(message)
                };
                event.preventDefault()
            }

            function fetchObjects(event){
                var sendTime = (new Date()).getTime();

                fetch('http://127.0.0.1:8000/v1/mot/yolov5')
                .then((response) => {
                    var responseTime = (new Date()).getTime() - sendTime;
                    console.log("API" + responseTime)
                });
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
    objects = []
    with open(video_txt_path, 'r') as f:
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
    return objects

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
