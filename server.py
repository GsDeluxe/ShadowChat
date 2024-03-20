import os
from core import server_func

SERVER_IP = "127.0.0.1"
SERVER_PORT = 1111
TOR = False

server = server_func.Server(host=SERVER_IP, port=SERVER_PORT, tor=TOR)
if not server.create_socket():
    print("[-] Error with Starting Server")
    os._exit(0)
else:
    print("SERVER STARTED")
    while True:
        cmd = input("Server >> ")
