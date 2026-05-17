"""
protocol.py

Protocol data structures for the Mini Internet Protocol Stack Simulator.

This file defines one class for each simulated protocol unit:
- Layer4Segment: UDP-like transport segment with DATA/ACK support;
- Layer3Packet: IP-like network packet;
- Layer2Frame: Ethernet-like data-link frame.

The classes do not perform real networking. They store header fields and
payloads so the Host and Router classes can demonstrate encapsulation and
forwarding through Layer 4, Layer 3, and Layer 2.
"""

from config import (
    DATA_LINK_HEADER_SIZE,
    DEFAULT_TTL,
    ETHERNET_TYPE_IPV4,
    IP_PROTOCOL_UDP,
    L4_TYPE_ACK,
    L4_TYPE_DATA,
    NETWORK_HEADER_SIZE,
    TRANSPORT_HEADER_SIZE,
)


class Layer4Segment:
    """
    Represent a UDP-like Layer 4 segment.

    Purpose:
        This class stores the transport-layer header fields and the application
        data payload. It is used for both DATA segments and ACK segments.

    Main fields:
        src_port: sending application port.
        dst_port: receiving application port.
        length: simplified header size plus data size.
        checksum: value used for error detection.
        segment_type: DATA or ACK.
        seq_num: alternating-bit sequence number, either 0 or 1.
        data: application payload bytes. ACK segments use empty data.
    """

    def __init__(self, src_port, dst_port, segment_type, seq_num, data=b"", checksum=None):
        """
        Create a Layer 4 segment and compute its checksum if needed.

        The project only provides a message size, so higher-level host logic
        creates dummy bytes. This constructor still accepts bytes, bytearray,
        strings, or None so the segment class remains safe and reusable.
        """

        # Store the transport header fields exactly as required by the project.
        self.src_port = src_port
        self.dst_port = dst_port
        self.segment_type = segment_type
        self.seq_num = seq_num

        # Convert supported input types into bytes. This makes checksum
        # calculation deterministic because the checksum always operates on
        # bytes rather than on mixed Python types.
        if data is None:
            self.data = b""
        elif isinstance(data, str):
            self.data = data.encode("utf-8")
        elif isinstance(data, bytearray):
            self.data = bytes(data)
        elif isinstance(data, bytes):
            self.data = data
        else:
            raise TypeError("Layer 4 data must be bytes, bytearray, string, or None")

        # The segment length includes the simplified Layer 4 header and payload.
        self.length = TRANSPORT_HEADER_SIZE + len(self.data)

        # A sender computes the checksum. A receiver can recompute it and compare
        # the value using verify_checksum().
        self.checksum = self.compute_checksum() if checksum is None else checksum

    def compute_checksum(self):
        """
        Compute a simple 16-bit one's-complement checksum.

        Purpose:
            Provides the required error-detection behaviour for Layer 4. This is
            a logical checksum for the simulator, not a full real UDP checksum.
        """

        # Include the key header fields and the payload in the checksum input.
        header_bytes = (
            f"{self.src_port}|{self.dst_port}|{self.length}|"
            f"{self.segment_type}|{self.seq_num}|"
        ).encode("utf-8")

        checksum_input = header_bytes + self.data
        total = 0

        # Add each byte and fold carry bits back into 16 bits. This keeps the
        # running sum inside the size of a 16-bit checksum.
        for byte in checksum_input:
            total += byte
            total = (total & 0xFFFF) + (total >> 16)

        # Return the one's complement of the folded sum.
        return (~total) & 0xFFFF

    def verify_checksum(self):
        """
        Check whether the segment is valid.

        Returns:
            True if the stored checksum equals the recomputed checksum;
            otherwise False, meaning the segment should be treated as corrupted.
        """

        return self.checksum == self.compute_checksum()

    def is_data(self):
        """Return True if this segment carries application DATA."""

        return self.segment_type == L4_TYPE_DATA

    def is_ack(self):
        """Return True if this segment is an ACK acknowledgement segment."""

        return self.segment_type == L4_TYPE_ACK

    def get_type_name(self):
        """Return a readable segment type name for logs and debugging."""

        if self.segment_type == L4_TYPE_DATA:
            return "DATA"
        if self.segment_type == L4_TYPE_ACK:
            return "ACK"
        return "UNKNOWN"

    def get_data_size(self):
        """Return the number of application-data bytes carried by this segment."""

        return len(self.data)

    def __repr__(self):
        """Return a concise developer-friendly representation of the segment."""

        return (
            "Layer4Segment("
            f"src_port={self.src_port}, "
            f"dst_port={self.dst_port}, "
            f"type={self.get_type_name()}, "
            f"seq={self.seq_num}, "
            f"length={self.length}, "
            f"checksum={self.checksum}, "
            f"data_size={len(self.data)}"
            ")"
        )


class Layer3Packet:
    """
    Represent an IP-like Layer 3 packet.

    Purpose:
        This class wraps a Layer 4 segment with source and destination IP
        addressing information. Routers inspect this object to make routing
        decisions and to decrement TTL.

    Main fields:
        src_ip: original sender IP address.
        dst_ip: final receiver IP address.
        ttl: time-to-live value, decremented at routers.
        protocol: protocol number for the Layer 4 payload.
        total_length: simplified Layer 3 header plus payload length.
        payload: the Layer 4 segment.
    """

    def __init__(self, src_ip, dst_ip, payload, ttl=DEFAULT_TTL, protocol=IP_PROTOCOL_UDP):
        """Create a Layer 3 packet around a Layer 4 segment."""

        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.ttl = ttl
        self.protocol = protocol
        self.payload = payload

        # Total length is the simplified IP-like header plus the Layer 4 length.
        self.total_length = NETWORK_HEADER_SIZE + payload.length

    def decrement_ttl(self):
        """
        Decrease TTL by one hop at a router.

        Returns:
            A tuple of (old_ttl, new_ttl) so Router R1 can print the exact TTL
            change required by the project output format.
        """

        old_ttl = self.ttl
        self.ttl -= 1
        return old_ttl, self.ttl

    def is_expired(self):
        """Return True if TTL has reached 0 or below and the packet must drop."""

        return self.ttl <= 0

    def __repr__(self):
        """Return a concise developer-friendly representation of the packet."""

        return (
            "Layer3Packet("
            f"src_ip={self.src_ip}, "
            f"dst_ip={self.dst_ip}, "
            f"ttl={self.ttl}, "
            f"protocol={self.protocol}, "
            f"total_length={self.total_length}"
            ")"
        )


class Layer2Frame:
    """
    Represent an Ethernet-like Layer 2 frame.

    Purpose:
        This class wraps a Layer 3 packet with local-link source and destination
        MAC addresses. A new Layer 2 frame is created for each hop.

    Main fields:
        src_mac: MAC address of the sending interface on the local link.
        dst_mac: MAC address of the receiving interface on the local link.
        frame_type: Ethernet type value, 0x0800 for IPv4-like payload.
        length: simplified Layer 2 header plus Layer 3 packet length.
        payload: the Layer 3 packet.
    """

    def __init__(self, src_mac, dst_mac, payload, frame_type=ETHERNET_TYPE_IPV4):
        """Create a Layer 2 frame around a Layer 3 packet."""

        self.src_mac = src_mac
        self.dst_mac = dst_mac
        self.frame_type = frame_type
        self.payload = payload

        # Frame length is tracked for completeness and easier debugging.
        self.length = DATA_LINK_HEADER_SIZE + payload.total_length

    def __repr__(self):
        """Return a concise developer-friendly representation of the frame."""

        return (
            "Layer2Frame("
            f"src_mac={self.src_mac}, "
            f"dst_mac={self.dst_mac}, "
            f"type={hex(self.frame_type)}, "
            f"length={self.length}"
            ")"
        )
