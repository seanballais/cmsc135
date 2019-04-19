import select
import socket
import sys
import traceback

import utils

from irc_handler import IRCHandler
from ds import Client
from ds import Channel


class Server(object):
    def __init__(self, port):
        self.address = 'localhost'
        self.port = int(port)
        self.server_socket = None
        self.irc_handler = IRCHandler()
        self.client_socket_id_map = dict()
        self.socket_id_client_map = dict()

    def create_client(self, client_socket):
        name = client_socket.recv(1024).decode().strip()
        client_address = client_socket.getpeername()[0]
        client = Client(name, client_address, None)

        self.irc_handler.add_client(client)
        # Note that the client's IP address will act as its ID.
        self.socket_id_client_map[id(client_socket)] = client_address
        self.client_socket_id_map[client_address] = client_socket

    def remove_client(self, client_address):
        self.irc_handler.remove_client(client_address)

        socket_id = id(self.client_socket_map[client_address])
        del self.socket_id_client_map[socket_id]
        del self.client_socket_id_map[client_address]

    def run(self):
        print('Server started in port {}.'.format(self.port))

        self.server_socket = socket.socket()
        self.server_socket.bind((self.address, self.port))
        self.server_socket.listen(5)

        client_sockets = [self.server_socket]
        while True:
            # Wait for messages from clients forever. At least here, we have
            # a forever.
            readable, writable, errored = select.select(client_sockets, [], [])
            for s in readable:
                if s is self.server_socket:
                    client_socket, address = self.server_socket.accept()
                    client_sockets.append(client_socket)

                    self.create_client(client_socket)   

                    print('Connection received from {}'.format(address[0]))
                else:
                    client_address = self.socket_id_client_map[id(s)]
                    data = s.recv(200)
                    if data:
                        self.irc_handler.process_client_message(data, client_address)
                    else:
                        client_sockets.remove(s)  # Could be optimized. We use
                                                  # the object itself instead 
                                                  # of the client_name because
                                                  # we only need to delete
                                                  # the socket object itself of,
                                                  # the client which we
                                                  # obviously already know.
                        self.remove_client(client_address)

                        disconnect_message = 'Connection from {} disconnected.'
                        print(disconnect_message.format(s.getpeername()[0]))

                        s.close()

            self.send_messages()

        self.close()

    def send_messages(self):
        for message in self.irc_handler.messages:
            client_socket = self.client_socket_id_map[message.sender_client]
            client_socket.send(message.message)

    def close(self):
        self.server_socket.close()


if __name__ == '__main__':
    args = sys.argv
    if len(args) != 2:
        print 'Port not supplied.'
        sys.exit(-1)

    server = Server(args[1])
    try:
        server.run()
    except Exception:
        print('Server message (ERROR):\n{}'.format(traceback.format_exc()))
    finally:
        server.close()
