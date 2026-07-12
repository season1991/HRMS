"""Phase 12 联调辅助：启动 fakeredis TCP server 让 backend 能连"""
import socket
from threading import Thread
from fakeredis import TcpFakeServer


def serve():
    server = TcpFakeServer(("127.0.0.1", 6379), server_type="redis")
    print("[fakeredis] listening on 127.0.0.1:6379")
    server.serve_forever()


if __name__ == "__main__":
    serve()