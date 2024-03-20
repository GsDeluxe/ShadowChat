import socket
import socks
import io
import os
import stem.process
import re

SOCKS_PORT = 9050
TOR_PATH = os.path.normpath(os.getcwd()+"\\tor.exe")
tor_process = stem.process.launch_tor_with_config(
  config = {
    'SocksPort': str(SOCKS_PORT),
  },
  init_msg_handler = lambda line: print(line) if re.search('Bootstrapped', line) else False,
  tor_cmd = TOR_PATH
)

TOR_PROXY_HOST = '127.0.0.1'
TOR_PROXY_PORT = 9050

SERVER_HOST = 's2mekv7sjm5icsz7i5pnpq436y67r74bkfobarkevpjqnfnifx57jlid.onion'
SERVER_PORT = 1254

socks.set_default_proxy(socks.SOCKS5, TOR_PROXY_HOST, TOR_PROXY_PORT)
socket.socket = socks.socksocket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_HOST, SERVER_PORT))

client_socket.sendall(b"Hello, server!")
client_socket.close()
tor_process.kill()