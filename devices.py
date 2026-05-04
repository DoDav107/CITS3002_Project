# Device Classes 
# Host
# Router 
# Interface 
"""
devices.py

This file implements the simulated network devices used in the project:
- Host: represents Host A or Host B
- Router: represents Router R1

The devices use the protocol header classes from protocol.py to simulate
Layer 2, Layer 3, and Layer 4 behaviour.
"""

import ipaddress

from config import (
    DEFAULT_TTL,
    HOST_A_PORT,
    HOST_B_PORT,
    L4_TYPE_ACK,
    L4_TYPE_DATA,
    MAX_SEGMENT_DATA_SIZE,
)

from protocol import Layer2Frame, Layer3Packet, Layer4Segment


class Device:
    """
    Base class for shared device behaviour.

    Both Host and Router use:
    - a routing table for Layer 3 decisions
    - a MAC table for Layer 2 next-hop MAC lookups
    - a learned MAC table to record source MAC addresses from received frames
    """

    def __init__(self, name, routing_table, mac_table):
        self.name = name
        self.routing_table = routing_table
        self.mac_table = dict(mac_table)
        self.learned_mac_table = {}

    def log(self, layer, message):
        """
        Prints a structured log message for the simulation.
        """

        print(f"{self.name}: {layer}: {message}")

    def lookup_route(self, destination_ip):
        """
        Finds the matching route for a destination IP address.
        """

        destination = ipaddress.ip_address(destination_ip)

        for route in self.routing_table:
            network = ipaddress.ip_network(route["destination_network"], strict=False)

            if destination in network:
                next_hop_ip = route["next_hop_ip"]

                # If next_hop_ip is None, the destination is directly connected.
                if next_hop_ip is None:
                    next_hop_ip = destination_ip

                return next_hop_ip, route["outgoing_interface"]

        raise ValueError(f"No route found from {self.name} to {destination_ip}")

    def lookup_mac(self, next_hop_ip):
        """
        Looks up the destination MAC address for a next-hop IP address.
        """

        if next_hop_ip in self.mac_table:
            return self.mac_table[next_hop_ip]

        raise ValueError(f"No MAC address found for next-hop IP {next_hop_ip}")


class Host(Device):
    """
    Represents an end host such as Host A or Host B.

    A host can:
    - send application data
    - create Layer 4 DATA segments
    - send and receive ACK segments
    - create Layer 3 packets
    - create Layer 2 frames
    - receive frames and deliver valid data to the application layer
    """

    def __init__(self, name, ip_address, mac_address, routing_table, mac_table):
        super().__init__(name, routing_table, mac_table)
        self.ip_address = ip_address
        self.mac_address = mac_address

        self.connected_router = None
        self.connected_router_interface = None

        self.next_send_seq = 0
        self.expected_receive_seq = 0
        self.last_ack_received = None
        self.last_ack_sent = None

    def connect_to_router(self, router, router_interface):
        """
        Connects this host to a router interface in the logical simulation.
        """

        self.connected_router = router
        self.connected_router_interface = router_interface

    # ------------------------------------------------------------
    # Layer 4 sending logic
    # ------------------------------------------------------------

    def send_application_data(
        self,
        data_size,
        destination_ip,
        source_port=HOST_A_PORT,
        destination_port=HOST_B_PORT,
    ):
        """
        Receives data from the application layer and sends it to another host.

        If the data is larger than MAX_SEGMENT_DATA_SIZE, it is split into
        multiple transport-layer DATA segments.
        """

        self.log("Layer 4", f"Data received from Application Layer. Data size={data_size}")

        remaining = data_size

        while remaining > 0:
            segment_data_size = min(MAX_SEGMENT_DATA_SIZE, remaining)
            data = b"X" * segment_data_size
            current_seq = self.next_send_seq

            segment = Layer4Segment(
                src_port=source_port,
                dst_port=destination_port,
                segment_type=L4_TYPE_DATA,
                seq_num=current_seq,
                data=data,
            )

            self.log("Layer 4", "Checksum computed")
            self.log(
                "Layer 4",
                f"Segment created by adding transport layer header (DATA, seq={current_seq}) (encapsulation)",
            )

            self._send_data_segment_until_ack(segment, destination_ip)

            # Alternate sequence number after correct ACK is received.
            self.next_send_seq = 1 - self.next_send_seq
            remaining -= segment_data_size

    def _send_data_segment_until_ack(self, segment, destination_ip):
        """
        Sends one DATA segment and waits for the correct ACK.

        In this project there is no loss or corruption, so the correct ACK
        should arrive deterministically. The loop still demonstrates the
        rdt2.2 retransmission behaviour.
        """

        while True:
            self.last_ack_received = None
            self.log("Layer 4", "Segment sent to Network Layer")
            self.send_segment_to_network(segment, destination_ip)

            if self.last_ack_received == segment.seq_num:
                return

            self.log(
                "Layer 4",
                f"Segment retransmitted due to incorrect ACK. Expected ACK seq={segment.seq_num}",
            )

    def send_segment_to_network(self, segment, destination_ip):
        """
        Passes a Layer 4 segment down to Layer 3.
        """

        packet = Layer3Packet(
            src_ip=self.ip_address,
            dst_ip=destination_ip,
            payload=segment,
            ttl=DEFAULT_TTL,
        )

        self.log(
            "Layer 3",
            f"Segment received from Transport Layer: SRC_IP={packet.src_ip}, DST_IP={packet.dst_ip}, TTL={packet.ttl}",
        )
        self.log("Layer 3", f"Destination IP read: {packet.dst_ip}")
        self.log("Layer 3", "Routing table lookup performed")

        next_hop_ip, outgoing_interface = self.lookup_route(packet.dst_ip)

        self.log("Layer 3", f"Next-hop IP determined: {next_hop_ip}")
        self.log("Layer 3", "Outgoing interface selected")
        self.log("Layer 3", "Packet forwarded to Data Link Layer")

        self.send_packet_to_data_link(packet, next_hop_ip, outgoing_interface)

    # ------------------------------------------------------------
    # Layer 2 sending and receiving logic
    # ------------------------------------------------------------

    def send_packet_to_data_link(self, packet, next_hop_ip, outgoing_interface):
        """
        Encapsulates a Layer 3 packet into a Layer 2 frame and sends it to
        the connected router.
        """

        self.log("Layer 2", "Packet received from Network Layer")

        destination_mac = self.lookup_mac(next_hop_ip)
        self.log(
            "Layer 2",
            f"Destination MAC lookup for next-hop IP ({next_hop_ip}) → {destination_mac}",
        )

        frame = Layer2Frame(
            src_mac=self.mac_address,
            dst_mac=destination_mac,
            payload=packet,
        )

        self.log(
            "Layer 2",
            f"Frame created: SRC_MAC={frame.src_mac}, DST_MAC={frame.dst_mac}",
        )
        self.log("Layer 2", "Frame sent")

        if self.connected_router is None:
            raise RuntimeError(f"{self.name} is not connected to a router")

        self.connected_router.receive_frame(frame, self.connected_router_interface)

    def receive_frame(self, frame):
        """
        Receives a Layer 2 frame from the router.
        """

        self.log("Layer 2", "Frame received")

        if frame.dst_mac != self.mac_address:
            self.log("Layer 2", "Frame discarded because destination MAC does not match")
            return

        self.learned_mac_table[frame.src_mac] = "local-link"
        self.log("Layer 2", f"Source MAC learned: {frame.src_mac}")
        self.log("Layer 2", "Packet delivered to Network Layer")

        self.receive_packet_from_data_link(frame.payload)

    # ------------------------------------------------------------
    # Layer 3 receiving logic
    # ------------------------------------------------------------

    def receive_packet_from_data_link(self, packet):
        """
        Receives a Layer 3 packet from Layer 2.
        """

        self.log(
            "Layer 3",
            f"Packet received from Data Link Layer: SRC_IP={packet.src_ip}, DST_IP={packet.dst_ip}, TTL={packet.ttl}",
        )
        self.log("Layer 3", f"Destination IP read: {packet.dst_ip}")

        if packet.dst_ip == self.ip_address:
            self.log("Layer 3", "Packet identified as local delivery")
            self.log("Layer 3", "Segment delivered to Transport Layer")
            self.receive_segment_from_network(packet.payload, packet.src_ip)
        else:
            self.log("Layer 3", "Packet discarded because destination IP does not match this host")

    # ------------------------------------------------------------
    # Layer 4 receiving logic
    # ------------------------------------------------------------

    def receive_segment_from_network(self, segment, source_ip):
        """
        Receives a Layer 4 segment from Layer 3.
        """

        self.log("Layer 4", "Segment received from Network Layer")

        if not segment.verify_checksum():
            self.log("Layer 4", "Segment discarded due to checksum error")

            if self.last_ack_sent is not None:
                self._send_ack(self.last_ack_sent, source_ip, segment.dst_port, segment.src_port)

            return

        self.log("Layer 4", "Checksum verified")

        if segment.is_ack():
            self.last_ack_received = segment.seq_num
            self.log("Layer 4", f"ACK received: seq={segment.seq_num}")
            return

        if segment.is_data():
            if segment.seq_num == self.expected_receive_seq:
                self.log(
                    "Layer 4",
                    f"DATA segment delivered to Application Layer. Data size={segment.get_data_size()}",
                )

                self.last_ack_sent = segment.seq_num
                self.expected_receive_seq = 1 - self.expected_receive_seq

                self._send_ack(
                    seq_num=segment.seq_num,
                    destination_ip=source_ip,
                    source_port=segment.dst_port,
                    destination_port=segment.src_port,
                )
            else:
                self.log("Layer 4", "Duplicate DATA segment received")

                if self.last_ack_sent is not None:
                    self._send_ack(
                        seq_num=self.last_ack_sent,
                        destination_ip=source_ip,
                        source_port=segment.dst_port,
                        destination_port=segment.src_port,
                    )

    def _send_ack(self, seq_num, destination_ip, source_port, destination_port):
        """
        Creates and sends an ACK segment back to the sender.
        """

        ack_segment = Layer4Segment(
            src_port=source_port,
            dst_port=destination_port,
            segment_type=L4_TYPE_ACK,
            seq_num=seq_num,
            data=b"",
        )

        self.log(
            "Layer 4",
            f"Segment created by adding transport layer header (ACK, seq={seq_num})",
        )
        self.log("Layer 4", "Segment sent to Network Layer")

        self.send_segment_to_network(ack_segment, destination_ip)


class Router(Device):
    """
    Represents Router R1.

    The router can:
    - receive frames on Interface 1 or Interface 2
    - learn incoming source MAC addresses
    - decapsulate Layer 2 frames to get Layer 3 packets
    - decrement TTL
    - perform routing table lookup
    - forward packets out of the correct interface
    """

    def __init__(self, name, routing_table, mac_table):
        super().__init__(name, routing_table, mac_table)
        self.interfaces = {}

    def add_interface(self, interface_name, ip_address, mac_address):
        """
        Adds a router interface with an IP address and MAC address.
        """

        self.interfaces[interface_name] = {
            "ip_address": ip_address,
            "mac_address": mac_address,
            "connected_device": None,
        }

    def connect_interface(self, interface_name, connected_device):
        """
        Connects a router interface to a host in the logical simulation.
        """

        if interface_name not in self.interfaces:
            raise ValueError(f"Unknown router interface: {interface_name}")

        self.interfaces[interface_name]["connected_device"] = connected_device

    def receive_frame(self, frame, incoming_interface):
        """
        Receives a Layer 2 frame on one of the router interfaces.
        """

        self.log("Layer 2", f"Frame received on {incoming_interface}")

        if incoming_interface not in self.interfaces:
            self.log("Layer 2", "Frame discarded because incoming interface is unknown")
            return

        expected_mac = self.interfaces[incoming_interface]["mac_address"]

        if frame.dst_mac != expected_mac:
            self.log("Layer 2", "Frame discarded because destination MAC does not match incoming interface")
            return

        self.learned_mac_table[frame.src_mac] = incoming_interface
        self.log("Layer 2", f"Source MAC learned: {frame.src_mac} on {incoming_interface}")
        self.log("Layer 2", "Packet delivered to Network Layer")

        self.receive_packet_from_data_link(frame.payload)

    def receive_packet_from_data_link(self, packet):
        """
        Receives a Layer 3 packet from Layer 2 and forwards it.
        """

        self.log(
            "Layer 3",
            f"Packet received from Data Link Layer: SRC_IP={packet.src_ip}, DST_IP={packet.dst_ip}, TTL={packet.ttl}",
        )
        self.log("Layer 3", f"Destination IP read: {packet.dst_ip}")

        old_ttl, new_ttl = packet.decrement_ttl()
        self.log("Layer 3", f"TTL decremented: {old_ttl} → {new_ttl}")

        if packet.is_expired():
            self.log("Layer 3", "Packet dropped due to TTL expiry")
            return

        self.log("Layer 3", "Routing table lookup performed")

        next_hop_ip, outgoing_interface = self.lookup_route(packet.dst_ip)

        self.log("Layer 3", f"Next-hop IP determined: {next_hop_ip}")
        self.log("Layer 3", f"Outgoing interface selected ({outgoing_interface})")
        self.log("Layer 3", "Packet forwarded to Data Link Layer")

        self.send_packet_to_data_link(packet, next_hop_ip, outgoing_interface)

    def send_packet_to_data_link(self, packet, next_hop_ip, outgoing_interface):
        """
        Encapsulates the Layer 3 packet into a new Layer 2 frame and forwards
        it out of the selected router interface.
        """

        if outgoing_interface not in self.interfaces:
            raise ValueError(f"Unknown outgoing interface: {outgoing_interface}")

        self.log("Layer 2", "Packet received from Network Layer")

        destination_mac = self.lookup_mac(next_hop_ip)
        self.log(
            "Layer 2",
            f"Destination MAC lookup for next-hop IP ({next_hop_ip}) → {destination_mac}",
        )

        source_mac = self.interfaces[outgoing_interface]["mac_address"]

        frame = Layer2Frame(
            src_mac=source_mac,
            dst_mac=destination_mac,
            payload=packet,
        )

        self.log(
            "Layer 2",
            f"Frame created: SRC_MAC={frame.src_mac}, DST_MAC={frame.dst_mac}",
        )
        self.log("Layer 2", f"Frame forwarded on {outgoing_interface}")

        connected_device = self.interfaces[outgoing_interface]["connected_device"]

        if connected_device is None:
            raise RuntimeError(f"No device connected to {outgoing_interface}")

        connected_device.receive_frame(frame)