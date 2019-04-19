import select
import socket
import sys

import utils

class BasicClient(object):

    def __init__(self, name, address, port):
        self.name = name
        self.address = address
        self.port = int(port)
        self.socket = socket.socket()

    def connect(self):
        self.socket.connect((self.address, self.port))
        self.socket.send(self.name)

    def send_message(self, message):
        message = utils.pad_message(message.encode())
        self.socket.send(message)


args = sys.argv
if len(args) != 4:
    print "Please supply a name, server address, and port."
    sys.exit()

client = BasicClient(args[1], args[2], args[3])
client.connect()

inputs = [client.socket, sys.stdin]

while True:
    readable, _, _ = select.select(inputs, [], [])
    for s in readable:
        if s is sys.stdin:
            message = sys.stdin.readline().rstrip()
            client.send_message(message)
        else:
            # Received a message from the server.
            data = s.recv(200)

            if data:
                print(data.strip())
            else:
                # Disconnected from the server. Most likely the server
                # went down.
                message = utils.CLIENT_SERVER_DISCONNECTED.format(args[2],
                                                                  args[3])
                print(message)

                sys.exit(0)
