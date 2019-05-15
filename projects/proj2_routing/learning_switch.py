"""
Your learning switch warm-up exercise for CS-168.

Start it up with a commandline like...

  ./simulator.py --default-switch-type=learning_switch topos.rand --links=0

"""

import sim.api as api
import sim.basics as basics


class RoutingTable(object):
    def __init__(self):
        self._node_ports = dict()

    def get_node_ports(self, node):
        return self._node_ports[node]

    def has_seen_node(self, node):
        return node in self._node_ports

    def remember_node_port(self, node, port):
        if self.has_seen_node(node):
            self._node_ports[node] += port
        else:
            self._node_ports[node] = [ port ]

    def remove_port(self, port):
        for k, v in self._node_ports.items():
            if v == port:
                del self._node_ports[k]


class LearningSwitch(api.Entity):
    """
    A learning switch.

    Looks at source addresses to learn where endpoints are.  When it doesn't
    know where the destination endpoint is, floods.

    This will surely have problems with topologies that have loops!  If only
    someone would invent a helpful poem for solving that problem...

    """

    def __init__(self):
        """
        Do some initialization.

        You probablty want to do something in this method.

        """
        self._routing_table = RoutingTable()

    def handle_link_down(self, port):
        """
        Called when a port goes down (because a link is removed)

        You probably want to remove table entries which are no longer
        valid here.

        """
        self._routing_table.remove(port)

    def handle_rx(self, packet, in_port):
        """
        Called when a packet is received.

        You most certainly want to process packets here, learning where
        they're from, and either forwarding them toward the destination
        or flooding them.

        """

        if isinstance(packet, basics.HostDiscoveryPacket):
            # Don't forward discovery messages
            return

        # Remember the packet's port, if we haven't yet. Its source can be
        # accessed from there.
        if not self._routing_table.has_seen_node(packet.src):
            self._routing_table.remember_node_port(packet.src, in_port)

        # Manage sending of packets to its destination.
        if self._routing_table.has_seen_node(packet.dst):
            dest_ports = self._routing_table.get_node_ports(packet.dst)
            self.send(packet, dest_ports)
        else:
            # Flood out all ports except the input port
            self.send(packet, in_port, flood=True)
