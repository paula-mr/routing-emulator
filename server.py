import socket

class Server:
    def __init__(self, address):
        self.PORT = 55151
        self.sock = None
        self.address = address

    def create_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.address, self.PORT))
        return self.sock

    def send_message(self, address, message):
        self.sock.sendto(message.encode('utf-8'), (address, self.PORT))
    
    def receive_message(self):
        data, address = self.sock.recvfrom(1024)
        return data, address
        