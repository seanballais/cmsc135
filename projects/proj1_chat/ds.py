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
        self.messages = list()

    @property
    def name(self):
        return self._name

    @property
    def clients(self):
        return self._clients

    @property
    def messages(self):
        return self._pending_messages

    def flush_messages(self):
        del self.messages[:]
    
    def add_client(self, client):
        self._clients[client.name] = client

    def remove_client(self, client):
        del self._clients[client.name]

    def send_messages(self):
        for client in self._clients:
            for message in self.messages:
                client.client_socket.send(message)


class Message(object):
    def __init__(self, sender_client, receiver_channel, message):
        self._sender_client = sender_client
        self._receiver_channel = receiver_channel
        self._message = message

    @property
    def sender_client(self):
        return self._sender_client
    
    @property
    def receiver_channel(self):
        return self._receiver_channel

    @property
    def message(self):
        return self._message
        
