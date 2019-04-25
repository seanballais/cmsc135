import json
import select
import socket
import sys
import traceback

import utils


def pad_message(message):
    # We pad the message by 200 since we only expect messages itself to be
    # 200 characters long.
    num_space_pads = min(200 - len(message), 200)
    message = message.ljust(num_space_pads, ' ')

    return message


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
        if name in self.client_socket_id_map:
            raise ClientNameExistsError()

        client_address = client_socket.getpeername()[0]
        client = Client(name, client_address, None)

        self.irc_handler.add_client(client)
        # Note that the client's name will act as its ID.
        self.socket_id_client_map[id(client_socket)] = client
        self.client_socket_id_map[name] = client_socket

    def remove_client(self, name):
        self.irc_handler.remove_client(name)

        socket_id = id(self.client_socket_id_map[name])
        del self.socket_id_client_map[socket_id]
        del self.client_socket_id_map[name]

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

                    try:
                        self.create_client(client_socket)
                    except ClientNameExistsError:
                        print('Client connected with a name that is '
                              + 'already used by another client. Kicking this'
                              + ' client off...')
                        client_socket.send('Client name is already taken.'
                                           + ' Use a different one.')
                        client_socket.close()

                        continue

                    client_sockets.append(client_socket)
                    client = self.socket_id_client_map[id(client_socket)]

                    print('Connection received from {}'.format(client.address)
                          + ' with a name, \'{}\'.'.format(client.name))
                else:
                    client = self.socket_id_client_map[id(s)]

                    try:
                        data = s.recv(utils.MESSAGE_LENGTH)
                        print('Message data size: {}'.format(len(data)))
                    except socket.error:
                        continue

                    if data:
                        self.irc_handler.process_client_message(data,
                                                                client.name)
                    else:
                        client_sockets.remove(s)  # Could be optimized. We use
                                                  # the object itself instead 
                                                  # of the client_name because
                                                  # we only need to delete
                                                  # the socket object itself of,
                                                  # the client which we
                                                  # obviously already know.
                        self.remove_client(client.name)

                        print('Connection from {} '.format(client.address)
                              + '({}) disconnected.'.format(client.name))

                        s.close()

            self.send_messages()

        self.close()

    def send_messages(self):
        # Send server messages first.
        for server_message in self.irc_handler.server_messages:
            print('(SERVER) Sending message: {}'.format(
                server_message.message.strip())
            )
            client_socket = self.client_socket_id_map[
                server_message.sender_client_name
            ]
            client_socket.send(pad_message(server_message.message))

        self.irc_handler.clear_server_messages()

        # Now send the messages of each channel to their subscriber clients.
        for channel in self.irc_handler.channels.values():
            for client in channel.clients.values():
                for message in channel.messages:
                    if message.sender_client_name != client.name:
                        print('(CHANNELS) Sending '
                              + 'message: {}'.format(message.message.strip()))
                        client_socket = self.client_socket_id_map[client.name]
                        client_socket.send(pad_message(message.message))

            channel.clear_messages()

    def close(self):
        self.server_socket.close()

    def _recv_all(self, client_socket):
        client_socket.setblocking(False)

        data = ''
        while len(data) < utils.MESSAGE_LENGTH:
            try:
                data_chunk = client_socket.recv(utils.MESSAGE_LENGTH)
            except socket.error:
                break

            data += data_chunk

        data = data.strip()

        client_socket.setblocking(True)

        return data


class IRCHandler(object):
    def __init__(self):
        self.connected_clients = dict()
        self.channels = dict()
        self._server_messages = list()

    @property
    def server_messages(self):
        return self._server_messages

    def add_client(self, client):
        # Note that the client's name will act as its ID.
        self.connected_clients[client.name] = client

    def add_channel(self, name):
        self.channels[name] = Channel(name)

    def add_client_to_channel(self, client, channel_name):
        old_channel = client.channel
        new_channel = self.channels[channel_name]
        client.channel = new_channel

        # We remove the client from its old channel because, well duh, we're
        # adding the client to a new channel.
        try:
            old_channel.remove_client(client)
        except AttributeError:
            print('Client {} is not subscribed '.format(client.address)
                  + 'to any channel, so we ain\'t removing '
                  + 'its \'old channel\'.')
        finally:
            new_channel.add_client(client)

    def remove_client(self, name):
        client = self.connected_clients[name]

        # Remove the client from its current channel to stop any messages
        # being sent to this now disconnected channel and preventing any
        # possible errors from arising.
        try:
            client.channel.remove_client(client)
        except AttributeError:
            print('Client {} is not subscribed '.format(client.address)
                  + 'to any channel, so we ain\'t removing '
                  + 'its \'old channel\'.')

        message = utils.SERVER_CLIENT_LEFT_CHANNEL.format(name)

        if client.channel is not None:
            client.channel.add_message(client, message)

        del self.connected_clients[name]

    def remove_channel(self, name):
        # Set the channel of the clients that are subscribed to the channel
        # being removed to None since they won't have a channel.
        channel = self.channels[name]
        for client in channel.clients:
            client.channel = None

        del channel

    def process_client_message(self, message, name):
        client = self.connected_clients[name]

        try:
            client_channel_name = client.channel.name
        except AttributeError:
            client_channel_name = None

        print('Received message '
              + 'from {} (Address: {}, '.format(client.name, client.address)
              + 'Channel: {}).'.format(client_channel_name))

        message = message.strip()
        message_blocks = message.split()

        print('   Message: {}'.format(message))

        try:
            if message[0] == '/':
                # So it is a command.
                response = self._validate_command_message(message_blocks)
                if response == '':
                    self._process_command(message_blocks, client)
                else:
                    server_message = Message(client.name, response)
                    self._server_messages.append(server_message)
            else:
                # The client sent a non-channel command message.
                if client.channel is None:
                    response = utils.SERVER_CLIENT_NOT_IN_CHANNEL

                    server_message = Message(client.name, response)
                    self._server_messages.append(server_message)
                else:
                    # The functionality where the message sender tag is
                    # prepended to the message here in the IRC Handler
                    # because its responsibility is to process messages and
                    # place them in the message bucket of the appropriate
                    # channels. This functionality can be placed in the server
                    # part but it does not suit this task because the server's
                    # responsibilities are just to send and receive client data
                    # that will be processed by IRC Handler.
                    # TL;DR: This functionality is placed here in alignment
                    # with the single responsibility principle.
                    message = '[{}] {}'.format(client.name, message)
                    client.channel.add_message(client.name, message)
        except IndexError:
            print('Client {} has sent an empty message.'.format(name)
                  + ' Ignoring it.')

    def clear_server_messages(self):
        self._server_messages[:] = []

    def _process_command(self, message_blocks, client):
        if message_blocks[0] == '/list':
            if len(self.channels.keys()) > 0:
                response = '\n'.join(map(str, self.channels.keys())).strip()
            else:
                response = 'No rooms exist yet.'

            server_message = Message(client.name, response)
            self._server_messages.append(server_message)
        elif message_blocks[0] == '/create' or message_blocks[0] == '/join':
            channel_name = message_blocks[1]

            if message_blocks[0] == '/create':
                if channel_name not in self.channels:
                    self.add_channel(channel_name)
                else:
                    client_channel_exists_message = \
                        utils.SERVER_CHANNEL_EXISTS.format(channel_name)
                    server_message = Message(client.name,
                                             client_channel_exists_message)
                    self._server_messages.append(server_message)

                    return

            try:
                self.add_client_to_channel(client, channel_name)
            except KeyError:
                client_no_channel_message = \
                    utils.SERVER_NO_CHANNEL_EXISTS.format(channel_name)
                server_message = Message(client.name, client_no_channel_message)
                self._server_messages.append(server_message)

                return

            # Add the client joined message for the
            # client to the list of messages in the client's new channel.
            client_joined_message = \
                utils.SERVER_CLIENT_JOINED_CHANNEL.format(client.name)
            channel = self.channels[channel_name]
            channel.add_message(client.name, client_joined_message)

    def _validate_command_message(self, message_blocks):
        message = ' '.join(message_blocks)
        command = message_blocks[0]

        response = ''
        if not self._is_command_valid(command):
            response = utils.SERVER_INVALID_CONTROL_MESSAGE.format(message)
            return response

        if not self._is_channel_command_valid_length(message_blocks):
            if command == '/list':
                response = '/list should only be used by itself.'
            elif command == '/create':
                response = utils.SERVER_CREATE_REQUIRES_ARGUMENT.format(message)
            elif command == '/join':
                response = utils.SERVER_JOIN_REQUIRES_ARGUMENT.format(message)

        return response if response != '' else ''

    def _is_irc_command_valid_length(self, message_blocks):
        return 1 <= len(message_blocks) <= 2

    def _is_channel_command_valid_length(self, message_blocks):
        if message_blocks[0] == '/list':
            return len(message_blocks) == 1
        else:
            return len(message_blocks) == 2

    def _is_command_valid(self, command):
        valid_commands = ['/join', '/create', '/list']
        return command in valid_commands


class Client(object):
    def __init__(self, name, address, channel):
        self._name = name
        self._address = address
        self._channel = channel

    @property
    def name(self):
        return self._name

    @property
    def address(self):
        return self._address

    @property
    def channel(self):
        return self._channel
    
    @channel.setter
    def channel(self, new_channel):
        self._channel = new_channel


class Channel(object):
    def __init__(self, name):
        self._name = name
        self._clients = dict()
        self._messages = list()

    @property
    def name(self):
        return self._name

    @property
    def clients(self):
        return self._clients

    @property
    def messages(self):
        return self._messages
    
    def add_message(self, sender_client_name, message):
        self._messages.append(Message(sender_client_name, message))

    def clear_messages(self):
        self._messages[:] = []

    def add_client(self, client):
        self._clients[client.name] = client

    def remove_client(self, client):
        del self._clients[client.name]


class Message(object):
    def __init__(self, sender_client_name, message):
        self._sender_client_name = sender_client_name
        self._message = message

    @property
    def sender_client_name(self):
        return self._sender_client_name

    @property
    def message(self):
        return self._message


class ClientNameExistsError(Exception):
    def __init__(self):
        Exception.__init__(self, SERVER_CLIENT_NAME_TAKEN_ALREADY)


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
