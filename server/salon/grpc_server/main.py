import os
from concurrent import futures

import grpc
from salon_proto import game_pb2_grpc as rpc
from salon.grpc_server.servicer import Game

def create_server(address):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    rpc.add_GameServicer_to_server(Game(), server)
    port = server.add_insecure_port(address)
    return server, port

def main():
    address = os.environ.get("SALON_ADDRESS", "127.0.0.1:50051")# if defined will use SALON_ADDRESS
    server, port = create_server(address)
    server.start()
    print(f"server running on {address} (Ctrl+C to stop)")
    server.wait_for_termination()

if __name__ == "__main__":
    main()

#this command to run server(from \server): python -m salon.grpc_server.main