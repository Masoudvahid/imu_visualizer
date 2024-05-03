import json
import math
import socket
import numpy as np

class TCP_server:
    def __init__(self):
        # Set up the server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = socket.gethostname()
        self.IPAddr = socket.gethostbyname(self.host)
        self.port = 9885
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        self.client_socket = None
        self.addr = None
        self.received_data = list()

        self.__init_connection()
        self.__transmit_data()

    def __init_connection(self):
        print(f"Server Listening on, {self.IPAddr} | {self.host}, port {self.port}")
        # Accept incoming connections
        self.client_socket, self.addr = self.server_socket.accept()
        print("Successfully Connected to ", self.addr)

    def __transmit_data(self):
        while True:
            data = self.client_socket.recv(1024 * 2)
            print(data)


if __name__ == '__main__':
    server = TCP_server()
