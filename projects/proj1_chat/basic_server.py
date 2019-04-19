import socket
import sys


class BasicServer(object):

    def __init__(self, port):
        self.port = int(port)
        self.address = 'localhost'

    def listen(self):
        server_socket = socket.socket()
        server_socket.bind((self.address, self.port))
        server_socket.listen(5)

        while True:
            # Serve connections forever.
            (client_socket, address) = server_socket.accept()
            print(client_socket)
            message = client_socket.recv(1024)

            print message


args = sys.argv
if len(args) != 2:
    print "Please supply a port."
    sys.exit()

server = BasicServer(args[1])
server.listen()
