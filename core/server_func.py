import socket
import struct
import os
import stem.process
import re
import threading
import rsa

from core import cryptohandler


class Server():
    def __init__(self, host="127.0.0.1", port=1254, tor=False, password=None) -> None:
        self.tor = tor
        self.password = password
        self.host = host
        self.port = port
        self.PUBLIC_KEY, self.PRIVATE_KEY = rsa.newkeys(2048)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cryptoHandler = cryptohandler.CryptoHandler()
        self.client_dict = {
                "CLIENT_OBJ": [],
                "CLIENT_IPS": [],
                "CLIENT_KEYS": [],
                "CLIENT_NICKS": []
            }
        
    def __start_tor(self):
        SOCKS_PORT = 9050
        SERVER_HOST = "127.0.0.1"
        TOR_PATH = os.path.normpath(os.getcwd()+"\\tor\\tor.exe")
        tor_process = stem.process.launch_tor_with_config(
        config = {
            'SocksPort': str(SOCKS_PORT),
            'HiddenServiceDir': "./tor",
            'HiddenServicePort': f'{str(self.port)} {SERVER_HOST}:{str(self.port)}'
        },
        init_msg_handler = lambda line: print(line) if re.search('Bootstrapped', line) else False,
        tor_cmd = TOR_PATH
        )

        with open("tor/hostname", "r") as f:
            hostname = f.read().strip()
            f.close()
        
        return {"TOR_PROC": tor_process, "HOSTNAME": hostname}
    
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

    def send_encrypt(self, client_obj: socket.socket, data: bytes, pubkey: rsa.PublicKey):
        key = self.cryptoHandler.generate_key(self.cryptoHandler.get_random_bytes())
        key_encrypted = rsa.encrypt(pub_key=pubkey, message=key)
        self.__send_msg(sock=client_obj, msg=key_encrypted)
        
        msg = self.cryptoHandler.encryption(key=key, data=data)
        self.__send_msg(sock=client_obj, msg=msg)



    def recv_encrypt(self, client_obj: socket.socket, privkey: rsa.PrivateKey):
        key = rsa.decrypt(crypto=self.__recv_msg(sock=client_obj), priv_key=privkey)

        encrypted_msg = self.__recv_msg(sock=client_obj)
        decrypted_msg = self.cryptoHandler.decryption(key=key, cipherdata=encrypted_msg)
        return decrypted_msg

    def broadcast_msg(self, data: bytes, nickname: str):
        for index, client in enumerate(self.client_dict["CLIENT_OBJ"]):
            data_ = b"[" + nickname + b"]: " + data
            self.send_encrypt(client_obj=client, data=data_, pubkey=self.client_dict["CLIENT_KEYS"][index])

    def __handle_client(self, client_obj: socket.socket, nickname: str):
        self.broadcast_msg(data=f"{nickname.decode()} Has Joined".encode(), nickname=b"Server")
        while True:
            try:
                msg = self.recv_encrypt(client_obj=client_obj, privkey=self.PRIVATE_KEY)
                self.broadcast_msg(data=msg, nickname=nickname)
            except:
                index = self.client_dict["CLIENT_OBJ"].index(client_obj)
                del self.client_dict["CLIENT_OBJ"][index]
                del self.client_dict["CLIENT_IPS"][index]
                del self.client_dict["CLIENT_KEYS"][index]
                del self.client_dict["CLIENT_NICKS"][index]

                self.broadcast_msg(data=f"{nickname.decode()} Has Left".encode(), nickname=b"Server")
                break

    def __accept_thread(self, socket_obj: socket.socket) -> None:
        while True:
            socket_obj.listen()
            client_obj, client_ip = socket_obj.accept()

            # KEY EXCHANGE
            client_key = rsa.PublicKey.load_pkcs1(client_obj.recv(20480))
            client_obj.sendall(self.PUBLIC_KEY.save_pkcs1())

            # NICKNAME RECV
            client_nick = self.recv_encrypt(client_obj=client_obj, privkey=self.PRIVATE_KEY)
            client_nick.decode()
            
            self.client_dict["CLIENT_OBJ"].append(client_obj)
            self.client_dict["CLIENT_IPS"].append(client_ip)
            self.client_dict["CLIENT_KEYS"].append(client_key)
            self.client_dict["CLIENT_NICKS"].append(client_nick)

            threading.Thread(target=self.__handle_client, args=(client_obj, client_nick)).start()
    
    def create_socket(self) -> bool:
        if self.tor:
            self.host = "127.0.0.1"
            self.tor_ret = self.__start_tor()
            self.hostname = self.tor_ret["HOSTNAME"]
            print(self.hostname)
        try:
            self.sock.bind((self.host, self.port))
            threading.Thread(target=self.__accept_thread, args=(self.sock, ), daemon=True).start()
            return True
        except Exception as e:
            print(e)
            return False

