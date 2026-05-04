# This file defines how frames, pakcets, and segments are created 
"""
protocol.py

This file defines the protocol data structures used in the mini Internet
Protocol Stack Simulator.

It contains:
- Layer2Frame: Ethernet-like frame
- Layer3Packet: IP-like packet
- Layer4Segment: UDP-like segment with ACK support
"""

from config import (
    ETHERNET_TYPE_IPV4,
    IP_PROTOCOL_UDP,
    DEFAULT_TTL,
    L4_TYPE_DATA,
    L4_TYPE_ACK,
    TRANSPORT_HEADER_SIZE,
    NETWORK_HEADER_SIZE,
)


class Layer4Segment:
    """
    Represents a simplified UDP-like transport layer segment.

    Header fields:
    - Source port
    - Destination port
    - Length
    - Checksum
    - Type: DATA or ACK
    - Sequence number
    - Data
    """

    def __init__(self, src_port, dst_port, segment_type, seq_num, data=b"", checksum=None):
        self.src_port = src_port
        self.dst_port = dst_port
        self.segment_type = segment_type
        self.seq_num = seq_num

        # Make sure data is stored as bytes.
        if data is None:
            self.data = b""
        elif isinstance(data, str):
            self.data = data.encode("utf-8")
        elif isinstance(data, bytearray):
            self.data = bytes(data)
        elif isinstance(data, bytes):
            self.data = data
        else:
            raise TypeError("Layer 4 data must be bytes or string")

        # Transport length = header size + data size.
        self.length = TRANSPORT_HEADER_SIZE + len(self.data)

        # If no checksum is given, compute it automatically.
        if checksum is None:
            self.checksum = self.compute_checksum()
        else:
            self.checksum = checksum

    def compute_checksum(self):
        """
        Computes a simple 16-bit checksum for error detection.

        This is a logical simulation, so the checksum only needs to be
        consistent between sender and receiver.
        """

        header_bytes = (
            f"{self.src_port}|{self.dst_port}|{self.length}|"
            f"{self.segment_type}|{self.seq_num}|"
        ).encode("utf-8")

        checksum_data = header_bytes + self.data

        total = 0

        for byte in checksum_data:
            total += byte

            # Keep the value inside 16 bits.
            total = (total & 0xFFFF) + (total >> 16)

        # One's complement.
        return (~total) & 0xFFFF

    def verify_checksum(self):
        """
        Verifies whether the stored checksum matches the recomputed checksum.
        """

        return self.checksum == self.compute_checksum()

    def is_data(self):
        """
        Returns True if this segment is a DATA segment.
        """

        return self.segment_type == L4_TYPE_DATA

    def is_ack(self):
        """
        Returns True if this segment is an ACK segment.
        """

        return self.segment_type == L4_TYPE_ACK

    def get_type_name(self):
        """
        Returns a readable name for the segment type.
        """

        if self.segment_type == L4_TYPE_DATA:
            return "DATA"

        if self.segment_type == L4_TYPE_ACK:
            return "ACK"

        return "UNKNOWN"

    def get_data_size(self):
        """
        Returns the size of the application data in bytes.
        """

        return len(self.data)

    def __repr__(self):
        return (
            f"Layer4Segment("
            f"src_port={self.src_port}, "
            f"dst_port={self.dst_port}, "
            f"type={self.get_type_name()}, "
            f"seq={self.seq_num}, "
            f"length={self.length}, "
            f"checksum={self.checksum}, "
            f"data_size={len(self.data)}"
            f")"
        )


class Layer3Packet:
    """
    Represents a simplified IP-like network layer packet.

    Header fields:
    - Source IP
    - Destination IP
    - TTL
    - Protocol
    - Total length
    - Payload, which contains the Layer 4 segment
    """

    def __init__(self, src_ip, dst_ip, payload, ttl=DEFAULT_TTL, protocol=IP_PROTOCOL_UDP):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.ttl = ttl
        self.protocol = protocol
        self.payload = payload

        # Network total length = network header size + transport segment length.
        self.total_length = NETWORK_HEADER_SIZE + payload.length

    def decrement_ttl(self):
        """
        Decreases TTL by 1 when the packet passes through a router.
        """

        old_ttl = self.ttl
        self.ttl -= 1
        return old_ttl, self.ttl

    def is_expired(self):
        """
        Returns True if TTL has reached 0 or below.
        """

        return self.ttl <= 0

    def __repr__(self):
        return (
            f"Layer3Packet("
            f"src_ip={self.src_ip}, "
            f"dst_ip={self.dst_ip}, "
            f"ttl={self.ttl}, "
            f"protocol={self.protocol}, "
            f"total_length={self.total_length}"
            f")"
        )


class Layer2Frame:
    """
    Represents a simplified Ethernet-like data link layer frame.

    Header fields:
    - Destination MAC
    - Source MAC
    - Type
    - Payload, which contains the Layer 3 packet
    """

    def __init__(self, src_mac, dst_mac, payload, frame_type=ETHERNET_TYPE_IPV4):
        self.src_mac = src_mac
        self.dst_mac = dst_mac
        self.frame_type = frame_type
        self.payload = payload

    def __repr__(self):
        return (
            f"Layer2Frame("
            f"src_mac={self.src_mac}, "
            f"dst_mac={self.dst_mac}, "
            f"type={hex(self.frame_type)}"
            f")"
        )