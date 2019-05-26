"""Your awesome Distance Vector router for CS 168."""
import heapq
import json

import sim.api as api
import sim.basics as basics

# We define infinity as a distance of 16.
INFINITY = 16


class DVRouter(basics.DVRouterBase):
    # NO_LOG = True # Set to True on an instance to disable its logging
    # POISON_MODE = True # Can override POISON_MODE here
    # DEFAULT_TIMER_INTERVAL = 5 # Can override this yourself for testing

    def __init__(self):
        """
        Called when the instance is initialized.

        You probably want to do some additional initialization here.

        """
        self._routing_table = RoutingTable()
        self._ports = set()

        self.start_timer()  # Starts calling handle_timer() at correct rate

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this Entity goes up.

        The port attached to the link and the link latency are passed
        in.

        """
        self._routing_table.adjust_port_costs(port, latency)
        self._ports.add(port)
        self._send_routes()

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this Entity does down.

        The port number used by the link is passed in.

        """
        self._routing_table.remove_down_ports(port)
        self._ports.remove(port)
        self._send_routes()

    def handle_rx(self, packet, port):
        """
        Called by the framework when this Entity receives a packet.

        packet is a Packet (or subclass).
        port is the port number it arrived on.

        You definitely want to fill this in.

        """
        #self.log("RX %s on %s (%s)", packet, port, api.current_time())
        if isinstance(packet, basics.RoutePacket):
            self._routing_table.add_node_entry(packet.destination,
                                               port,
                                               packet.latency)
        elif isinstance(packet, basics.HostDiscoveryPacket):
            self._routing_table.add_port_costs(port, INFINITY)
            self._routing_table.add_node_entry(packet.src, port, INFINITY)
        else:
            # Totally wrong behavior for the sake of demonstration only: send
            # the packet back to where it came from!
            if packet.src != packet.dst:
                dest_port = self._routing_table \
                                .get_dest_next_hop(packet.dst).port
                self.send(packet, port=dest_port)

    def handle_timer(self):
        """
        Called periodically.

        When called, your router should send tables to neighbors.  It
        also might not be a bad place to check for whether any entries
        have expired.

        """
        self._send_routes()

    def _send_routes(self):
        for dest in self._routing_table.get_dests():
            dest_cost = self._routing_table.get_dest_next_hop(dest).cost
            route_packet = basics.RoutePacket(dest, dest_cost)

            for port in self._ports:
                self.send(route_packet, port=port)


class RoutingTable(object):
    def __init__(self):
        self._table = dict()
        self._port_costs = dict()

    def add_node_entry(self, dest, port, cost):
        actual_cost = self._port_costs[port] + cost

        if self.is_dest_known(dest):
            self._table[dest].add_possible_hop(port, actual_cost)
        else:
            self._table[dest] = NextHop()
            self._table[dest].add_possible_hop(port, actual_cost)

    def add_port_costs(self, port, cost):
        self._port_costs[port] = cost

    def adjust_port_costs(self, port, new_cost):
        try:
            old_cost = self._port_costs[port]
            if old_cost == INFINITY:
                self._update_port_costs(port, new_cost)
            else:
                for _, hop_entries in self._table.items():
                    cost_delta = old_cost - new_cost
                    hop_entries.adjust_port_costs(port, cost_delta)
        except KeyError:
            pass

        self.add_port_costs(port, new_cost)

    def get_dest_next_hop(self, dest):
        return self._table[dest].get_dest_next_hop()

    def get_dests(self):
        return self._table.keys()

    def is_dest_known(self, dest):
        return dest in self._table

    def is_port_known(self, port):
        return port in self._port_costs

    def remove_down_ports(self, port):
        self._port_costs[port] = INFINITY

        for _, hop_entries in self._table.items():
            hop_entries.remove_possible_hop(port)

    def _update_port_costs(self, port, cost):
        self._port_costs[port] = cost

        for _, hop_entries in self._table.items():
            hop_entries.update_possible_hops(port, cost)

class NextHop(object):
    def __init__(self):
        self._possible_hops = []

    def add_possible_hop(self, port, cost):
        possible_hop = HopEntry(cost, port)
        self._possible_hops.append(possible_hop)
        heapq.heapify(self._possible_hops)

    def adjust_port_costs(self, port, cost_delta):
        for i, obj in enumerate(self._possible_hops):
            if obj.port == port:
                self._possible_hops[i].cost += cost_delta

    def get_dest_next_hop(self):
        return self._possible_hops[0]

    def remove_possible_hop(self, port):
        self.update_possible_hops(port, INFINITY)

        heapq.heapify(self._possible_hops)

    def update_possible_hops(self, port, cost):
        for i, obj in enumerate(self._possible_hops):
            if obj.port == port:
                self._possible_hops[i].cost = cost

        heapq.heapify(self._possible_hops)


class HopEntry(object):
    def __init__(self, cost, port):
        self._cost = cost
        self._port = port

    @property
    def cost(self):
        return self._cost

    @property
    def port(self):
        return self._port

    @cost.setter
    def cost(self, new_cost):
        self._cost = new_cost

    @port.setter
    def port(self, new_port):
        self._port = new_port

    def __lt__(self, other):
        return self.cost < other.cost