import socket

import io
import os
import stem.process
import re

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 1254

SOCKS_PORT = 9050
TOR_PATH = os.path.normpath(os.getcwd()+"\\tor.exe")
tor_process = stem.process.launch_tor_with_config(
  config = {
    'SocksPort': str(SOCKS_PORT),
    'HiddenServiceDir': "./tor",
    'HiddenServicePort': f'{str(SERVER_PORT)} {SERVER_HOST}:{str(SERVER_PORT)}'
  },
  init_msg_handler = lambda line: print(line) if re.search('Bootstrapped', line) else False,
  tor_cmd = TOR_PATH
)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.bind((SERVER_HOST, SERVER_PORT))

os.system("type tor/hostname")

server_socket.listen(1)
print(f"[*] Listening on {SERVER_HOST}:{SERVER_PORT}")

client_socket, client_address = server_socket.accept()
print(f"[*] Connection from {client_address}")

while True:
  data = client_socket.recv(1024)
  print(f"[*] Received: {data.decode()}")

client_socket.close()
server_socket.close()
tor_process.kill()
