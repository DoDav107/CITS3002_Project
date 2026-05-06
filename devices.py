"""
devices.py

Implements the simulated network devices used in the
Mini Internet Protocol Stack Simulator.

Devices:
- Host
- Router

This file simulates:
- Layer 2 frame forwarding
- Layer 3 routing and TTL handling
- Layer 4 reliable transport using rdt2.2

Features:
- segmentation
- checksum validation
- alternating-bit protocol
- retransmission handling
- MAC learning
- routing table lookup
"""

import ipaddress
import math

from config import (
    DEFAULT_TTL,
    HOST_A_PORT,
    HOST_B_PORT,
    L4_TYPE_ACK,
    L4_TYPE_DATA,
    MAX_SEGMENT_DATA_SIZE,
    MAX_RETRANSMISSIONS,
)

from protocol import (
    Layer2Frame,
    Layer3Packet,
    Layer4Segment,
)


# ============================================================
# Base Device Class
# ============================================================

class Device:
    """
    Shared functionality for all network devices.
    """

    def __init__(self, name, routing_table, mac_table):
        self.name = name
        self.routing_table = routing_table
        self.mac_table = dict(mac_table)

        # Learned MAC address table
        self.learned_mac_table = {}

    def log(self, layer, message):
        """
        Prints structured simulation logs.
        """

        print(f"{self.name}: {layer}: {message}")

    def lookup_route(self, destination_ip):
        """
        Finds the correct route for a destination IP.
        """

        destination = ipaddress.ip_address(destination_ip)

        for route in self.routing_table:
            network = ipaddress.ip_network(
                route["destination_network"],
                strict=False,
            )

            if destination in network:
                next_hop_ip = route["next_hop_ip"]

                # Directly connected destination
                if next_hop_ip is None:
                    next_hop_ip = destination_ip

                return next_hop_ip, route["outgoing_interface"]

        raise ValueError(
            f"{self.name}: No route found for {destination_ip}"
        )

    def lookup_mac(self, next_hop_ip):
        """
        Returns the MAC address for the next-hop IP.
        """

        if next_hop_ip in self.mac_table:
            return self.mac_table[next_hop_ip]

        raise ValueError(
            f"{self.name}: No MAC entry for next-hop IP {next_hop_ip}"
        )


# ============================================================
# Host Class
# ============================================================

class Host(Device):
    """
    Represents an end host.

    Supports:
    - application data transmission
    - segmentation
    - reliable transport (rdt2.2)
    - ACK handling
    - Layer 2/3/4 processing
    """

    def __init__(
        self,
        name,
        ip_address,
        mac_address,
        routing_table,
        mac_table,
    ):
        super().__init__(name, routing_table, mac_table)

        self.ip_address = ip_address
        self.mac_address = mac_address

        self.connected_router = None
        self.connected_router_interface = None

        # rdt2.2 state
        self.next_send_seq = 0
        self.expected_receive_seq = 0

        self.last_ack_received = None
        self.last_ack_sent = None

        # Statistics
        self.total_segments_sent = 0
        self.total_acks_received = 0
        self.total_retransmissions = 0

    # --------------------------------------------------------
    # Topology Connection
    # --------------------------------------------------------

    def connect_to_router(self, router, router_interface):
        """
        Connects the host to a router interface.
        """

        self.connected_router = router
        self.connected_router_interface = router_interface

    # --------------------------------------------------------
    # Layer 4 Sending Logic
    # --------------------------------------------------------

    def send_application_data(
        self,
        data_size,
        destination_ip,
        source_port=HOST_A_PORT,
        destination_port=HOST_B_PORT,
    ):
        """
        Receives application data and transmits it reliably.
        """

        self.log(
            "Layer 4",
            f"Data received from Application Layer. Data size={data_size}"
        )

        total_segments = math.ceil(
            data_size / MAX_SEGMENT_DATA_SIZE
        )

        self.log(
            "Layer 4",
            f"Application message segmented into {total_segments} segment(s)"
        )

        remaining = data_size
        segment_number = 1

        while remaining > 0:

            segment_data_size = min(
                MAX_SEGMENT_DATA_SIZE,
                remaining,
            )

            data = b"X" * segment_data_size

            current_seq = self.next_send_seq

            self.log(
                "Layer 4",
                f"Sending segment {segment_number}/{total_segments}"
            )

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
                f"Segment created by adding transport layer header "
                f"(DATA, seq={current_seq}) (encapsulation)"
            )

            self._send_data_segment_until_ack(
                segment,
                destination_ip,
            )

            self.next_send_seq = 1 - self.next_send_seq

            remaining -= segment_data_size
            segment_number += 1

    def _send_data_segment_until_ack(
        self,
        segment,
        destination_ip,
    ):
        """
        Sends one segment until the correct ACK is received.
        """

        retransmission_attempt = 0

        while retransmission_attempt < MAX_RETRANSMISSIONS:

            self.last_ack_received = None

            self.total_segments_sent += 1

            self.log(
                "Layer 4",
                "Segment sent to Network Layer"
            )

            self.send_segment_to_network(
                segment,
                destination_ip,
            )

            if self.last_ack_received == segment.seq_num:
                return

            retransmission_attempt += 1
            self.total_retransmissions += 1

            self.log(
                "Layer 4",
                f"Segment retransmitted due to incorrect ACK. "
                f"Expected ACK seq={segment.seq_num}"
            )

        raise RuntimeError(
            f"{self.name}: Maximum retransmissions exceeded"
        )

    def send_segment_to_network(
        self,
        segment,
        destination_ip,
    ):
        """
        Passes a Layer 4 segment to Layer 3.
        """

        packet = Layer3Packet(
            src_ip=self.ip_address,
            dst_ip=destination_ip,
            payload=segment,
            ttl=DEFAULT_TTL,
        )

        self.log(
            "Layer 3",
            f"Segment received from Transport Layer: "
            f"SRC_IP={packet.src_ip}, "
            f"DST_IP={packet.dst_ip}, "
            f"TTL={packet.ttl}"
        )

        self.log(
            "Layer 3",
            f"Destination IP read: {packet.dst_ip}"
        )

        self.log(
            "Layer 3",
            "Routing table lookup performed"
        )

        next_hop_ip, outgoing_interface = self.lookup_route(
            packet.dst_ip
        )

        self.log(
            "Layer 3",
            f"Next-hop IP determined: {next_hop_ip}"
        )

        self.log(
            "Layer 3",
            "Outgoing interface selected"
        )

        self.log(
            "Layer 3",
            "Packet forwarded to Data Link Layer"
        )

        self.send_packet_to_data_link(
            packet,
            next_hop_ip,
            outgoing_interface,
        )

    # --------------------------------------------------------
    # Layer 2 Sending Logic
    # --------------------------------------------------------

    def send_packet_to_data_link(
        self,
        packet,
        next_hop_ip,
        outgoing_interface,
    ):
        """
        Encapsulates a packet into a frame and sends it.
        """

        self.log(
            "Layer 2",
            "Packet received from Network Layer"
        )

        destination_mac = self.lookup_mac(next_hop_ip)

        self.log(
            "Layer 2",
            f"Destination MAC lookup for next-hop IP "
            f"({next_hop_ip}) → {destination_mac}"
        )

        frame = Layer2Frame(
            src_mac=self.mac_address,
            dst_mac=destination_mac,
            payload=packet,
        )

        self.log(
            "Layer 2",
            f"Frame created: "
            f"SRC_MAC={frame.src_mac}, "
            f"DST_MAC={frame.dst_mac}"
        )

        self.log("Layer 2", "Frame sent")

        if self.connected_router is None:
            raise RuntimeError(
                f"{self.name}: No connected router"
            )

        self.connected_router.receive_frame(
            frame,
            self.connected_router_interface,
        )

    # --------------------------------------------------------
    # Layer 2 Receiving Logic
    # --------------------------------------------------------

    def receive_frame(self, frame):
        """
        Receives a Layer 2 frame.
        """

        self.log("Layer 2", "Frame received")

        if frame.dst_mac != self.mac_address:
            self.log(
                "Layer 2",
                "Frame discarded because destination MAC "
                "does not match"
            )
            return

        if frame.src_mac not in self.learned_mac_table:

            self.learned_mac_table[frame.src_mac] = "local-link"

            self.log(
                "Layer 2",
                f"Source MAC learned: {frame.src_mac}"
            )

        self.log(
            "Layer 2",
            "Packet delivered to Network Layer"
        )

        self.receive_packet_from_data_link(frame.payload)

    # --------------------------------------------------------
    # Layer 3 Receiving Logic
    # --------------------------------------------------------

    def receive_packet_from_data_link(self, packet):
        """
        Receives a Layer 3 packet from Layer 2.
        """

        self.log(
            "Layer 3",
            f"Packet received from Data Link Layer: "
            f"SRC_IP={packet.src_ip}, "
            f"DST_IP={packet.dst_ip}, "
            f"TTL={packet.ttl}"
        )

        self.log(
            "Layer 3",
            f"Destination IP read: {packet.dst_ip}"
        )

        if packet.dst_ip == self.ip_address:

            self.log(
                "Layer 3",
                "Packet identified as local delivery"
            )

            self.log(
                "Layer 3",
                "Segment delivered to Transport Layer"
            )

            self.receive_segment_from_network(
                packet.payload,
                packet.src_ip,
            )

        else:
            self.log(
                "Layer 3",
                "Packet discarded because destination "
                "IP does not match this host"
            )

    # --------------------------------------------------------
    # Layer 4 Receiving Logic
    # --------------------------------------------------------

    def receive_segment_from_network(
        self,
        segment,
        source_ip,
    ):
        """
        Receives a Layer 4 segment from Layer 3.
        """

        self.log(
            "Layer 4",
            "Segment received from Network Layer"
        )

        if not segment.verify_checksum():

            self.log(
                "Layer 4",
                "Segment discarded due to checksum error"
            )

            if self.last_ack_sent is not None:

                self._send_ack(
                    self.last_ack_sent,
                    source_ip,
                    segment.dst_port,
                    segment.src_port,
                )

            return

        self.log("Layer 4", "Checksum verified")

        # ACK Handling
        if segment.is_ack():

            self.last_ack_received = segment.seq_num
            self.total_acks_received += 1

            self.log(
                "Layer 4",
                f"ACK received: seq={segment.seq_num}"
            )

            return

        # DATA Handling
        if segment.is_data():

            if segment.seq_num == self.expected_receive_seq:

                self.log(
                    "Layer 4",
                    f"DATA segment delivered to "
                    f"Application Layer. "
                    f"Data size={segment.get_data_size()}"
                )

                self.last_ack_sent = segment.seq_num

                self.expected_receive_seq = (
                    1 - self.expected_receive_seq
                )

                self._send_ack(
                    seq_num=segment.seq_num,
                    destination_ip=source_ip,
                    source_port=segment.dst_port,
                    destination_port=segment.src_port,
                )

            else:

                self.log(
                    "Layer 4",
                    "Duplicate DATA segment received"
                )

                if self.last_ack_sent is not None:

                    self._send_ack(
                        seq_num=self.last_ack_sent,
                        destination_ip=source_ip,
                        source_port=segment.dst_port,
                        destination_port=segment.src_port,
                    )

    def _send_ack(
        self,
        seq_num,
        destination_ip,
        source_port,
        destination_port,
    ):
        """
        Creates and sends an ACK segment.
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
            f"Segment created by adding transport "
            f"layer header (ACK, seq={seq_num})"
        )

        self.log(
            "Layer 4",
            "Segment sent to Network Layer"
        )

        self.send_segment_to_network(
            ack_segment,
            destination_ip,
        )


# ============================================================
# Router Class
# ============================================================

class Router(Device):
    """
    Represents Router R1.

    Supports:
    - MAC learning
    - Layer 2 forwarding
    - Layer 3 routing
    - TTL decrementing
    - packet forwarding
    """

    def __init__(
        self,
        name,
        routing_table,
        mac_table,
    ):
        super().__init__(name, routing_table, mac_table)

        self.interfaces = {}

    # --------------------------------------------------------
    # Interface Management
    # --------------------------------------------------------

    def add_interface(
        self,
        interface_name,
        ip_address,
        mac_address,
    ):
        """
        Adds a router interface.
        """

        self.interfaces[interface_name] = {
            "ip_address": ip_address,
            "mac_address": mac_address,
            "connected_device": None,
        }

    def connect_interface(
        self,
        interface_name,
        connected_device,
    ):
        """
        Connects a device to a router interface.
        """

        if interface_name not in self.interfaces:
            raise ValueError(
                f"Unknown router interface: {interface_name}"
            )

        self.interfaces[interface_name][
            "connected_device"
        ] = connected_device

    # --------------------------------------------------------
    # Layer 2 Receiving Logic
    # --------------------------------------------------------

    def receive_frame(
        self,
        frame,
        incoming_interface,
    ):
        """
        Receives a frame on a router interface.
        """

        self.log(
            "Layer 2",
            f"Frame received on {incoming_interface}"
        )

        if incoming_interface not in self.interfaces:

            self.log(
                "Layer 2",
                "Frame discarded because incoming "
                "interface is unknown"
            )

            return

        expected_mac = self.interfaces[
            incoming_interface
        ]["mac_address"]

        if frame.dst_mac != expected_mac:

            self.log(
                "Layer 2",
                "Frame discarded because destination "
                "MAC does not match incoming interface"
            )

            return

        if frame.src_mac not in self.learned_mac_table:

            self.learned_mac_table[
                frame.src_mac
            ] = incoming_interface

            self.log(
                "Layer 2",
                f"Source MAC learned: "
                f"{frame.src_mac} on {incoming_interface}"
            )

        self.log(
            "Layer 2",
            "Packet delivered to Network Layer"
        )

        self.receive_packet_from_data_link(frame.payload)

    # --------------------------------------------------------
    # Layer 3 Processing
    # --------------------------------------------------------

    def receive_packet_from_data_link(self, packet):
        """
        Processes and forwards Layer 3 packets.
        """

        self.log(
            "Layer 3",
            f"Packet received from Data Link Layer: "
            f"SRC_IP={packet.src_ip}, "
            f"DST_IP={packet.dst_ip}, "
            f"TTL={packet.ttl}"
        )

        self.log(
            "Layer 3",
            f"Destination IP read: {packet.dst_ip}"
        )

        old_ttl, new_ttl = packet.decrement_ttl()

        self.log(
            "Layer 3",
            f"TTL decremented: {old_ttl} → {new_ttl}"
        )

        if packet.is_expired():

            self.log(
                "Layer 3",
                "Packet dropped due to TTL expiry"
            )

            return

        self.log(
            "Layer 3",
            "Routing table lookup performed"
        )

        next_hop_ip, outgoing_interface = self.lookup_route(
            packet.dst_ip
        )

        self.log(
            "Layer 3",
            f"Next-hop IP determined: {next_hop_ip}"
        )

        self.log(
            "Layer 3",
            f"Outgoing interface selected "
            f"({outgoing_interface})"
        )

        self.log(
            "Layer 3",
            "Packet forwarded to Data Link Layer"
        )

        self.send_packet_to_data_link(
            packet,
            next_hop_ip,
            outgoing_interface,
        )

    # --------------------------------------------------------
    # Layer 2 Forwarding
    # --------------------------------------------------------

    def send_packet_to_data_link(
        self,
        packet,
        next_hop_ip,
        outgoing_interface,
    ):
        """
        Rebuilds Layer 2 frame and forwards packet.
        """

        if outgoing_interface not in self.interfaces:
            raise ValueError(
                f"Unknown outgoing interface: "
                f"{outgoing_interface}"
            )

        self.log(
            "Layer 2",
            "Packet received from Network Layer"
        )

        destination_mac = self.lookup_mac(next_hop_ip)

        self.log(
            "Layer 2",
            f"Destination MAC lookup for "
            f"next-hop IP ({next_hop_ip}) "
            f"→ {destination_mac}"
        )

        source_mac = self.interfaces[
            outgoing_interface
        ]["mac_address"]

        frame = Layer2Frame(
            src_mac=source_mac,
            dst_mac=destination_mac,
            payload=packet,
        )

        self.log(
            "Layer 2",
            f"Frame created: "
            f"SRC_MAC={frame.src_mac}, "
            f"DST_MAC={frame.dst_mac}"
        )

        self.log(
            "Layer 2",
            f"Frame forwarded on {outgoing_interface}"
        )

        connected_device = self.interfaces[
            outgoing_interface
        ]["connected_device"]

        if connected_device is None:
            raise RuntimeError(
                f"No device connected to "
                f"{outgoing_interface}"
            )

        connected_device.receive_frame(frame)