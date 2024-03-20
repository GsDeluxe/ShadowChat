import socket
import socks
import rsa
import struct
import threading
import os
import stem.process
import re

from core import cryptohandler


class Client():
    def __init__(self, host: str, port: int, nickname: str, tor=False) -> None:
        self.tor = tor
        self.host = host
        self.port = port
        self.nickname = nickname
        self.PUBLIC_KEY, self.PRIVATE_KEY = rsa.newkeys(2048)
        if self.tor:
            self.tor_proc = self.__start_tor()
            socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
            socket.socket = socks.socksocket

        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cryptoHandler = cryptohandler.CryptoHandler()

    def __start_tor(self):
        SOCKS_PORT = 9050
        TOR_PATH = os.path.normpath(os.getcwd()+"\\tor\\tor.exe")
        print(TOR_PATH)
        tor_process = stem.process.launch_tor_with_config(
          config = {
            'SocksPort': str(SOCKS_PORT),
          },
          init_msg_handler = lambda line: print(line) if re.search('Bootstrapped', line) else False,
          tor_cmd = TOR_PATH
        )

        return tor_process

    def __send_msg(self, sock, msg):
        msg = struct.pack('>I', len(msg)) + msg
        sock.sendall(msg)

    def __recv_msg(self, sock):
        raw_msglen = self.__recvall(sock, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        return self.__recvall(sock, msglen)

    def __recvall(self, sock, n):
        data = bytearray()
        packet = sock.recv(n - len(data))
        while len(data) < n:
            if not packet:
                return None
            data.extend(packet)
        return data
    
    def send_encrypt(self, socket_obj: socket.socket, data: bytes, pubkey: rsa.PublicKey):
        key = self.cryptoHandler.generate_key(self.cryptoHandler.get_random_bytes())
        key_encrypted = rsa.encrypt(pub_key=pubkey, message=key)
        self.__send_msg(sock=socket_obj, msg=key_encrypted)
        
        msg = self.cryptoHandler.encryption(key=key, data=data)
        self.__send_msg(sock=socket_obj, msg=msg)


    def recv_encrypt(self, socket_obj: socket.socket, privkey: rsa.PrivateKey):
        key = rsa.decrypt(crypto=self.__recv_msg(sock=socket_obj), priv_key=privkey)

        encrypted_msg = self.__recv_msg(sock=socket_obj)
        decrypted_msg = self.cryptoHandler.decryption(key=key, cipherdata=encrypted_msg)
        return decrypted_msg

    def connect(self):
        try:
            self.client_sock.connect((self.host, self.port))

            # KEY EXCHANGE
            self.client_sock.sendall(self.PUBLIC_KEY.save_pkcs1())
            self.SERVER_PUBLIC_KEY = rsa.PublicKey.load_pkcs1(self.client_sock.recv(20480))

            self.send_encrypt(socket_obj=self.client_sock, data=self.nickname.encode(), pubkey=self.SERVER_PUBLIC_KEY)

            return True
        except:
            return False
