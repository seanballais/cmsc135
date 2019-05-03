# Project 1 - Chat
Submitted by: Sean Francis N. Ballais

As per project specifications, the project is separated into the server and the client.

## Server
The server is architectured in a way that splits the server-side functionality into two components: (1) the server module handling the low-level networking functionalities, and (2) the IRC module handling the IRC-specific functionalities.

The server module is responsible for handling client management and sending/receiving messages. This module acts as a mediator between the IRC module and the client, abstracting with the networking level aspects for the IRC module. This module passes IRC-level messages immediately to the IRC module. Server messages, outside of he judiciary of the IRC module, are created (and thus sent) in this module. The server module also only sends channel messages to non-sender clients.

The IRC module processes the messages, figures out whether it is a client message or a correct command, and performs the appropriate actions. The appropriate messages (e.g. informational and error messages) are created here. Messages from clients with channels, are binned into the channels to allow for easier and correct sending of messages. Non-subscribed clients' messages are ignored and are given a message stating that they must subscribe to a channel first, as per the project specifications.

## Client
The client is what one call back in the old days of computing as a "dumb terminal". The client exists only to send and receive and display messages from the server. It has no state related to the chat stored. It is only aware of the necessary information enough to communicate with the server. This means it only stores the client name, and socket connection and the IP address and port to the server. It only waits for data from the server or standard input and acts appropriately.

## Known Bugs

 * There is one particularly relatively hard-to-recreate bug with the server where it will take in more than 200 bytes from the TCP socket stream. This results in more than one message worth of bytes being captured. This has been observed to occur only when the using `client_split_messages.py` client at certain times. This bug results in the server wrongly knowing the connecting client's name. I am unable to replicate this bug in a deterministic manner. Thus, I am leaving this as a non-fixable bug. However, I have determined that this bug is the result of my implementation of data buffering.
