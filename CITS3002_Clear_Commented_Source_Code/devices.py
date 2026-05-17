"""
devices.py

Device behaviour for the Mini Internet Protocol Stack Simulator.

This file implements the simulated network devices required by the project:
- Device: shared helper behaviour for hosts and routers;
- Host: behaviour for Host A and Host B;
- Router: behaviour for Router R1.

The devices exchange protocol objects directly through method calls. This means
there are no sockets, threads, or real network interfaces. The goal is to model
how Layer 2, Layer 3, and Layer 4 interact in a deterministic and readable way.
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
    Provide behaviour shared by Host and Router.

    Purpose:
        This base class avoids duplicating common logic. Both hosts and routers
        need a device name for logging, a routing table for Layer 3 decisions,
        a MAC lookup table for Layer 2 delivery, and a learned MAC table for
        source-MAC learning.
    """

    def __init__(self, name, routing_table, mac_table):
        """
        Initialise shared device state.

        Args:
            name: display name used at the start of every log line.
            routing_table: list of Layer 3 routes for this device.
            mac_table: mapping from next-hop IP address to MAC address.
        """

        self.name = name
        self.routing_table = routing_table
        self.mac_table = dict(mac_table)
        self.learned_mac_table = {}

    def log(self, layer, message):
        """
        Print one structured log line.

        The format matches the assignment's expected output style:
        Device Name: Layer X: operation message
        """

        print(f"{self.name}: {layer}: {message}")

    def lookup_route(self, destination_ip):
        """
        Find the next-hop IP and outgoing interface for a destination IP.

        Purpose:
            Implements the Layer 3 routing-table lookup used by Host and Router.
            The first route whose destination network contains the destination IP
            is selected.

        Returns:
            (next_hop_ip, outgoing_interface)
        """

        destination = ipaddress.ip_address(destination_ip)

        for route in self.routing_table:
            network = ipaddress.ip_network(route["destination_network"], strict=False)

            if destination in network:
                next_hop_ip = route["next_hop_ip"]

                # Directly connected routes store None as the next hop. In that
                # case, the destination IP itself is the next-hop IP.
                if next_hop_ip is None:
                    next_hop_ip = destination_ip

                return next_hop_ip, route["outgoing_interface"]

        raise ValueError(f"No route found from {self.name} to {destination_ip}")

    def lookup_mac(self, next_hop_ip):
        """
        Find the destination MAC address for a next-hop IP address.

        Purpose:
            Implements the Layer 2 MAC lookup step after Layer 3 has already
            decided the next-hop IP address.
        """

        if next_hop_ip in self.mac_table:
            return self.mac_table[next_hop_ip]

        raise ValueError(f"No MAC address found for next-hop IP {next_hop_ip}")


class Host(Device):
    """
    Simulate an end host such as Host A or Host B.

    Purpose:
        A Host performs the end-to-end transport behaviour. It can receive data
        from the application layer, split it into Layer 4 DATA segments, send the
        segments down through Layer 3 and Layer 2, receive incoming DATA/ACK
        segments, verify checksums, deliver valid data, and send ACKs.
    """

    def __init__(self, name, ip_address, mac_address, routing_table, mac_table):
        """
        Initialise a host with its IP address, MAC address, and protocol state.

        The sequence-number fields support the rdt2.2 alternating-bit protocol.
        """

        super().__init__(name, routing_table, mac_table)
        self.ip_address = ip_address
        self.mac_address = mac_address

        # These fields represent the host's single connection to Router R1.
        self.connected_router = None
        self.connected_router_interface = None

        # Layer 4 alternating-bit protocol state.
        self.next_send_seq = 0
        self.expected_receive_seq = 0
        self.last_ack_received = None
        self.last_ack_sent = None

    def connect_to_router(self, router, router_interface):
        """
        Connect this host to one router interface in the logical topology.

        This does not create a real network link. It stores object references so
        the host can pass a Layer 2 frame to the router's receive_frame() method.
        """

        self.connected_router = router
        self.connected_router_interface = router_interface

    # Layer 4 sending logic

    def send_application_data(
        self,
        data_size,
        destination_ip,
        source_port=HOST_A_PORT,
        destination_port=HOST_B_PORT,
    ):
        """
        Receive application data and send it reliably to another host.

        Purpose:
            This is the main Layer 4 sending method. The assignment input is a
            message size rather than actual text, so the simulator creates dummy
            bytes of that size. If the message is larger than 500 bytes, it is
            split into multiple DATA segments.
        """

        self.log("Layer 4", f"Data received from Application Layer. Data size={data_size}")

        remaining = data_size

        # Stop when all application bytes have been placed into DATA segments.
        while remaining > 0:
            # Limit each DATA segment to the maximum application data size.
            segment_data_size = min(MAX_SEGMENT_DATA_SIZE, remaining)

            # Use dummy bytes because the assignment tests by size, not content.
            data = b"X" * segment_data_size

            # Use the current alternating-bit sequence number for this segment.
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

            # Send this DATA segment and do not continue until the correct ACK.
            self._send_data_segment_until_ack(segment, destination_ip)

            # Only alternate sequence number after correct ACK has arrived.
            self.next_send_seq = 1 - self.next_send_seq
            remaining -= segment_data_size

    def _send_data_segment_until_ack(self, segment, destination_ip):
        """
        Send one DATA segment until the matching ACK is received.

        Purpose:
            Models the sender side of rdt2.2. The project assumes deterministic
            delivery with no loss, so the first send should normally succeed.
            The retransmission branch is still present to show the required
            behaviour if an incorrect or duplicate ACK is observed.
        """

        while True:
            # Clear the previous ACK state before sending the current segment.
            self.last_ack_received = None

            self.log("Layer 4", "Segment sent to Network Layer")
            self.send_segment_to_network(segment, destination_ip)

            # Correct ACK means this segment is complete.
            if self.last_ack_received == segment.seq_num:
                return

            # Incorrect/missing ACK means retransmit this same segment.
            self.log(
                "Layer 4",
                f"Segment retransmitted due to incorrect ACK. Expected ACK seq={segment.seq_num}",
            )

    def send_segment_to_network(self, segment, destination_ip):
        """
        Encapsulate a Layer 4 segment inside a Layer 3 packet.

        Purpose:
            This method is the boundary from Layer 4 down to Layer 3. It creates
            the IP-like packet, performs route lookup, and passes the packet to
            Layer 2 for framing.
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

        # Layer 3 decides the next hop and outgoing interface.
        next_hop_ip, outgoing_interface = self.lookup_route(packet.dst_ip)

        self.log("Layer 3", f"Next-hop IP determined: {next_hop_ip}")
        self.log("Layer 3", "Outgoing interface selected")
        self.log("Layer 3", "Packet forwarded to Data Link Layer")

        self.send_packet_to_data_link(packet, next_hop_ip, outgoing_interface)

    # ------------------------------------------------------------------
    # Layer 2 sending and receiving logic
    # ------------------------------------------------------------------

    def send_packet_to_data_link(self, packet, next_hop_ip, outgoing_interface):
        """
        Encapsulate a Layer 3 packet in a Layer 2 frame and send it.

        Purpose:
            This method is the boundary from Layer 3 down to Layer 2. It uses
            the next-hop IP address from Layer 3 to find the local destination
            MAC address, then creates the Ethernet-like frame.
        """

        self.log("Layer 2", "Packet received from Network Layer")

        # Resolve the next-hop IP address to a destination MAC address.
        destination_mac = self.lookup_mac(next_hop_ip)
        self.log(
            "Layer 2",
            f"Destination MAC lookup for next-hop IP ({next_hop_ip}) → {destination_mac}",
        )

        # The host's own MAC is the source MAC for this local-link frame.
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

        # Deliver the frame to Router R1 on the connected router interface.
        self.connected_router.receive_frame(frame, self.connected_router_interface)

    def receive_frame(self, frame):
        """
        Receive a Layer 2 frame from Router R1.

        Purpose:
            This method models a host receiving a local-link frame. The host only
            accepts the frame if the destination MAC address matches its own MAC.
            Accepted frames are decapsulated and passed up to Layer 3.
        """

        self.log("Layer 2", "Frame received")

        # Discard frames not addressed to this host's MAC address.
        if frame.dst_mac != self.mac_address:
            self.log("Layer 2", "Frame discarded because destination MAC does not match")
            return

        # Learn the source MAC address from the incoming frame.
        self.learned_mac_table[frame.src_mac] = "local-link"
        self.log("Layer 2", f"Source MAC learned: {frame.src_mac}")
        self.log("Layer 2", "Packet delivered to Network Layer")

        # Remove the Layer 2 frame and pass the Layer 3 packet upward.
        self.receive_packet_from_data_link(frame.payload)

    # ------------------------------------------------------------------
    # Layer 3 receiving logic
    # ------------------------------------------------------------------

    def receive_packet_from_data_link(self, packet):
        """
        Receive a Layer 3 packet from Layer 2 and check local delivery.

        Purpose:
            Hosts do not forward packets. They only accept packets whose
            destination IP matches their own IP address. Valid local packets are
            decapsulated and delivered to Layer 4.
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


    # Layer 4 receiving logic

    def receive_segment_from_network(self, segment, source_ip):
        """
        Receive a Layer 4 segment and process DATA or ACK behaviour.

        Purpose:
            This method is the top of the protocol stack. It verifies the
            checksum, handles ACKs for previously sent DATA, delivers valid DATA
            to the application layer, and sends ACKs back to the sender.
        """

        self.log("Layer 4", "Segment received from Network Layer")

        # Corrupted segments are discarded. rdt2.2 resends the last ACK if there
        # is one, because the sender needs to know the last valid sequence.
        if not segment.verify_checksum():
            self.log("Layer 4", "Segment discarded due to checksum error")

            if self.last_ack_sent is not None:
                self._send_ack(self.last_ack_sent, source_ip, segment.dst_port, segment.src_port)

            return

        self.log("Layer 4", "Checksum verified")

        # ACK segments complete the sender's waiting loop.
        if segment.is_ack():
            self.last_ack_received = segment.seq_num
            self.log("Layer 4", f"ACK received: seq={segment.seq_num}")
            return

        # DATA segments carry application data and require an ACK in response.
        if segment.is_data():
            if segment.seq_num == self.expected_receive_seq:
                self.log(
                    "Layer 4",
                    f"DATA segment delivered to Application Layer. Data size={segment.get_data_size()}",
                )

                # Store the ACK number and update the next expected DATA seq.
                self.last_ack_sent = segment.seq_num
                self.expected_receive_seq = 1 - self.expected_receive_seq

                # Send ACK with the same sequence number as the DATA segment.
                self._send_ack(
                    seq_num=segment.seq_num,
                    destination_ip=source_ip,
                    source_port=segment.dst_port,
                    destination_port=segment.src_port,
                )
            else:
                # Duplicate DATA is not delivered again; the receiver repeats
                # the last ACK so the sender can recover.
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
        Create and send an ACK segment back to the DATA sender.

        Purpose:
            ACKs are Layer 4 segments with no application data. The ACK uses the
            same sequence number as the DATA segment that was correctly received.
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

        # ACKs travel back through the normal Layer 3 and Layer 2 process.
        self.send_segment_to_network(ack_segment, destination_ip)


class Router(Device):
    """
    Simulate Router R1.

    Purpose:
        Router R1 connects Network 1 and Network 2. It receives Layer 2 frames,
        learns source MAC addresses, extracts Layer 3 packets, decrements TTL,
        performs routing lookup, and creates new Layer 2 frames for forwarding.
    """

    def __init__(self, name, routing_table, mac_table):
        """Initialise the router and prepare an empty interface table."""

        super().__init__(name, routing_table, mac_table)
        self.interfaces = {}

    def add_interface(self, interface_name, ip_address, mac_address):
        """
        Register a router interface with its IP address and MAC address.

        Purpose:
            Router R1 has two interfaces. Each interface needs its own IP and
            MAC address so the router can validate received frames and choose
            the correct source MAC when forwarding frames.
        """

        self.interfaces[interface_name] = {
            "ip_address": ip_address,
            "mac_address": mac_address,
            "connected_device": None,
        }

    def connect_interface(self, interface_name, connected_device):
        """
        Connect a router interface to a host object.

        Purpose:
            Stores the object reference needed to deliver forwarded Layer 2
            frames to Host A or Host B in the logical simulation.
        """

        if interface_name not in self.interfaces:
            raise ValueError(f"Unknown router interface: {interface_name}")

        self.interfaces[interface_name]["connected_device"] = connected_device

    def receive_frame(self, frame, incoming_interface):
        """
        Receive and validate a Layer 2 frame on a router interface.

        Purpose:
            This method models the router receiving a local-link frame. The
            router accepts only frames addressed to the MAC address of the
            incoming interface. Accepted frames are decapsulated and passed up
            to Layer 3 for routing.
        """

        self.log("Layer 2", f"Frame received on {incoming_interface}")

        if incoming_interface not in self.interfaces:
            self.log("Layer 2", "Frame discarded because incoming interface is unknown")
            return

        expected_mac = self.interfaces[incoming_interface]["mac_address"]

        # Discard frames that were not addressed to this router interface.
        if frame.dst_mac != expected_mac:
            self.log("Layer 2", "Frame discarded because destination MAC does not match incoming interface")
            return

        # Learn which interface the source MAC was seen on.
        self.learned_mac_table[frame.src_mac] = incoming_interface
        self.log("Layer 2", f"Source MAC learned: {frame.src_mac} on {incoming_interface}")
        self.log("Layer 2", "Packet delivered to Network Layer")

        # Remove the Layer 2 frame and pass the Layer 3 packet upward.
        self.receive_packet_from_data_link(frame.payload)

    def receive_packet_from_data_link(self, packet):
        """
        Apply Layer 3 router processing and forward the packet.

        Purpose:
            Router R1 is responsible for forwarding packets between networks. It
            decrements TTL, drops expired packets, performs route lookup, and
            sends valid packets back down to Layer 2 for forwarding.
        """

        self.log(
            "Layer 3",
            f"Packet received from Data Link Layer: SRC_IP={packet.src_ip}, DST_IP={packet.dst_ip}, TTL={packet.ttl}",
        )
        self.log("Layer 3", f"Destination IP read: {packet.dst_ip}")

        # Routers reduce TTL by one to prevent endless forwarding loops.
        old_ttl, new_ttl = packet.decrement_ttl()
        self.log("Layer 3", f"TTL decremented: {old_ttl} → {new_ttl}")

        if packet.is_expired():
            self.log("Layer 3", "Packet dropped due to TTL expiry")
            return

        self.log("Layer 3", "Routing table lookup performed")

        # Decide the outgoing interface and next-hop IP for the destination.
        next_hop_ip, outgoing_interface = self.lookup_route(packet.dst_ip)

        self.log("Layer 3", f"Next-hop IP determined: {next_hop_ip}")
        self.log("Layer 3", f"Outgoing interface selected ({outgoing_interface})")
        self.log("Layer 3", "Packet forwarded to Data Link Layer")

        self.send_packet_to_data_link(packet, next_hop_ip, outgoing_interface)

    def send_packet_to_data_link(self, packet, next_hop_ip, outgoing_interface):
        """
        Create a new Layer 2 frame and forward it out of one interface.

        Purpose:
            The router does not reuse the incoming Layer 2 frame. It creates a
            fresh outgoing frame with the source MAC of the outgoing interface
            and the destination MAC of the next-hop device.
        """

        if outgoing_interface not in self.interfaces:
            raise ValueError(f"Unknown outgoing interface: {outgoing_interface}")

        self.log("Layer 2", "Packet received from Network Layer")

        # Resolve next-hop IP to destination MAC for the outgoing local link.
        destination_mac = self.lookup_mac(next_hop_ip)
        self.log(
            "Layer 2",
            f"Destination MAC lookup for next-hop IP ({next_hop_ip}) → {destination_mac}",
        )

        # Source MAC must be the MAC address of the selected outgoing interface.
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

        # Deliver the outgoing frame to the connected host object.
        connected_device.receive_frame(frame)
