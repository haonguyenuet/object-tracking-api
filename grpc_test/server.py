from concurrent import futures
from os import path

import grpc
import object_tracking_pb2
import object_tracking_pb2_grpc


video_txt_path = 'deepsort_yolov5/inference/output/video.txt'

class ObjectTrackingServicer(object_tracking_pb2_grpc.ObjectTrackingServicer):
    def Track(self, request_iterator, context):
        f = open(video_txt_path, 'r')
        lines = f.readlines()

        for line in lines:
            temp = line.split()
            x, y, w, h = map(float,temp[2:6])
            obj = object_tracking_pb2.Object(x = x, y = y, w = w, h = h)

            yield obj


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    object_tracking_pb2_grpc.add_ObjectTrackingServicer_to_server(ObjectTrackingServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
