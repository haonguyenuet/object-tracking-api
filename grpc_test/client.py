from __future__ import print_function

import grpc
import object_tracking_pb2_grpc
import object_tracking_pb2


def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = object_tracking_pb2_grpc.ObjectTrackingStub(channel)
        responses = stub.Track(object_tracking_pb2.EmptyMsg())
        for response in responses:
            print(response)


if __name__ == '__main__':
    run()
   
