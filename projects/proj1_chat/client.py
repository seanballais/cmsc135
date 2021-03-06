from __future__ import print_function

import select
import socket
import sys
import termios

import utils


class BasicClient(object):

    def __init__(self, name, address, port):
        self.name = name
        self.address = address
        self.port = int(port)
        self.socket = socket.socket()

    def connect(self):
        self.socket.connect((self.address, self.port))
        self.send_message(self.name)

    def send_message(self, message):
        message = self._pad_message(message)
        self.socket.send(self._pad_message(message))

    def run(self):
        try:
            self.connect()
        except socket.error:
            print(utils.CLIENT_CANNOT_CONNECT.format(self.address, self.port))
            sys.exit(1)

        inputs = [self.socket, sys.stdin]
        while True:
            print(utils.CLIENT_MESSAGE_PREFIX, end='')
            sys.stdout.flush()

            readable, _, _ = select.select(inputs, [], [])
            for s in readable:
                if s is sys.stdin:
                    message = sys.stdin.readline().strip()
                    self.send_message(message)
                else:
                    # We received a message from the server.
                    data = self._recv_all()

                    if data:
                        self._clear_current_line()
                        print('\r{}'.format(data.strip()))
                    else:
                        # Disconnected from the server. Most likely the server
                        # went down.
                        message = utils.CLIENT_SERVER_DISCONNECTED.format(
                            self.address, port
                        )
                        self._clear_current_line()
                        print('\r{}.'.format(message))

                        self.socket.close()
                        sys.exit(0)

    def _recv_all(self):
        self.socket.setblocking(False)

        data = ''
        ttl = 12  # Use a TTL to prevent any infinitely expecting data.
        while (len(data) < utils.MESSAGE_LENGTH) and (ttl > 0):
            try:
                data_chunk = self.socket.recv(utils.MESSAGE_LENGTH)
            except socket.error:
                # No more data to be read.
                break

            data += data_chunk
            ttl -= 1

        data = data.strip()

        self.socket.setblocking(True)

        return data

    def _clear_current_line(self):
        print(utils.CLIENT_WIPE_ME, end='')

    def _pad_message(self, message):
        # We pad the message by 200 since we only expect messages itself to be
        # 200 characters long.
        num_space_pads = min(200 - len(message), 200)
        message = '{}{}'.format(message, ' ' * num_space_pads)

        return message


if __name__ == '__main__':
    args = sys.argv
    if len(args) != 4:
        print('Please supply a name, server address, and port.')
        sys.exit()

    server_address = args[2]
    port = args[3]
    client = BasicClient(args[1], server_address, port)
    client.run()
