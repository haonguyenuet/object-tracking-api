from fastapi import FastAPI
from fastapi.testclient import TestClient

import time

from main import app
client = TestClient(app)


def test_mot_yolov5():
    print("Test API")
    start_time = time.time()
    response = client.get("/v1/mot/yolov5")
    response_time = time.time() - start_time
    print("Response time: ", response_time)
    print("Result: ", response.json())

def test_mot_yolov5_ws():
    print("Test WS")

    with client.websocket_connect("/v1/mot/yolov5_ws/1") as websocket:
        start_time = time.time()
        websocket.send_text("fetch_objects")
        data = websocket.receive_json()
        response_time = time.time() - start_time
        print("Response time: ", response_time)
        print("Result: ", data)



        
if __name__ == "__main__":
    test_mot_yolov5()
    # test_mot_yolov5_ws()