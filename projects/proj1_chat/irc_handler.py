import select
import socket
import sys

import utils

from ds import Client
from ds import Channel
from ds import Message


class IRCHandler(object):
    def __init__(self):
        self.connected_clients = dict()
        self.channels = dict()
        self._messages = list()

    @property
    def messages(self):
        return self._messages
    

    def add_client(self, client):
        # Note that the client's IP address will act as its ID.
        self.connected_clients[client.address] = client

    def add_channel(self, name):
        self.channels[name] = Channel(name)

    def remove_client(self, address):
        client = self.connected_clients[address]

        message = utils.SERVER_CLIENT_LEFT_CHANNEL.format(client.name)

        if client.channel is not None:
            client.channel.messages.append(message)

        del self.connected_clients[address]

    def remove_channel(self, name):
        del self.channels[name]

    def process_client_message(self, message, address):
        client = self.connected_clients[address]

        print('Received message from {} (Channel: {}).'.format(client.address,
                                                               client.channel))

        message = message.strip()
        message_blocks = message.split()

        if message[0] == '/':
            # So it is a command.
            response = self._validate_command_message(message_blocks)
            if response != '':
                client.client_socket.send(response)

            self._process_command(message)
        else:
            # The client sent a message.
            if client.channel is None:
                response = utils.SERVER_CLIENT_NOT_IN_CHANNEL
                response = utils.pad_message(response)

                message = Message(client.address, None, response)
                self._messages.append(message)
            else:
                pass

    def _process_command(self, message):
        pass

    def _validate_command_message(self, message_blocks):
        message = ' '.join(message_blocks)
        command = message_blocks[0]

        if not self._is_command_valid(command):
            response = utils.SERVER_INVALID_CONTROL_MESSAGE.format(message)
            response = utils.pad_message(response)

            return response

        if not self._is_channel_command_valid_length(message_blocks):
            if command == '/join':
                response = utils.SERVER_JOIN_REQUIRES_ARGUMENT.format(message)
                response = utils.pad_message(response)

                return response
            elif command == '/create':
                response = utils.SERVER_CREATE_REQUIRES_ARGUMENT.format(message)
                response = utils.pad_message(response)

                return response

        return ''

    def _is_irc_command_valid_length(self, message_blocks):
        return 1 <= len(message_blocks) <= 2

    def _is_channel_command_valid_length(self, message_blocks):
        return len(message_blocks) == 2

    def _is_command_valid(self, command):
        valid_commands = ['/join', '/create', '/list']
        return command in valid_commands