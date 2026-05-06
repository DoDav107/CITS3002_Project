"""
protocol.py

Mini Internet Protocol Stack Simulator

Defines the protocol data structures used throughout the
simulation.

Implemented Protocol Layers:
- Layer 2: Ethernet-like Frame
- Layer 3: IP-like Packet
- Layer 4: UDP-like Segment with ACK support

Features:
- encapsulation
- checksum generation
- checksum verification
- TTL handling
- segmentation support
- alternating-bit protocol support
"""

from config import (
    ETHERNET_TYPE_IPV4,
    IP_PROTOCOL_UDP,
    DEFAULT_TTL,

    L4_TYPE_DATA,
    L4_TYPE_ACK,
    L4_TYPE_NAMES,

    TRANSPORT_HEADER_SIZE,
    NETWORK_HEADER_SIZE,
    DATA_LINK_HEADER_SIZE,

    CHECKSUM_MODULO,
)


# ============================================================
# Layer 4 Segment
# ============================================================

class Layer4Segment:
    """
    Represents a simplified UDP-like transport segment.

    Header fields:
    - source port
    - destination port
    - length
    - checksum
    - type (DATA or ACK)
    - sequence number
    - application data
    """

    def __init__(
        self,
        src_port,
        dst_port,
        segment_type,
        seq_num,
        data=b"",
        checksum=None,
    ):

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if segment_type not in (
            L4_TYPE_DATA,
            L4_TYPE_ACK,
        ):
            raise ValueError(
                "Invalid Layer 4 segment type"
            )

        if seq_num not in (0, 1):
            raise ValueError(
                "Sequence number must be 0 or 1"
            )

        # ----------------------------------------------------
        # Header Fields
        # ----------------------------------------------------

        self.src_port = src_port
        self.dst_port = dst_port

        self.segment_type = segment_type
        self.seq_num = seq_num

        # ----------------------------------------------------
        # Data Handling
        # ----------------------------------------------------

        if data is None:
            self.data = b""

        elif isinstance(data, str):
            self.data = data.encode("utf-8")

        elif isinstance(data, bytearray):
            self.data = bytes(data)

        elif isinstance(data, bytes):
            self.data = data

        else:
            raise TypeError(
                "Layer 4 data must be bytes or string"
            )

        # ----------------------------------------------------
        # Length Calculation
        # ----------------------------------------------------

        self.length = (
            TRANSPORT_HEADER_SIZE +
            len(self.data)
        )

        # ----------------------------------------------------
        # Checksum
        # ----------------------------------------------------

        if checksum is None:
            self.checksum = self.compute_checksum()

        else:
            self.checksum = checksum

    # --------------------------------------------------------
    # Checksum Handling
    # --------------------------------------------------------

    def compute_checksum(self):
        """
        Computes a simple 16-bit checksum.
        """

        header_bytes = (
            f"{self.src_port}|"
            f"{self.dst_port}|"
            f"{self.length}|"
            f"{self.segment_type}|"
            f"{self.seq_num}|"
        ).encode("utf-8")

        checksum_data = header_bytes + self.data

        total = 0

        for byte in checksum_data:

            total += byte

            # Keep value inside 16 bits
            total = (
                (total & CHECKSUM_MODULO) +
                (total >> 16)
            )

        # One's complement checksum
        return (~total) & CHECKSUM_MODULO

    def verify_checksum(self):
        """
        Verifies checksum correctness.
        """

        return (
            self.checksum ==
            self.compute_checksum()
        )

    def corrupt(self):
        """
        Intentionally corrupts the segment checksum.

        Useful for testing retransmission logic.
        """

        self.checksum ^= CHECKSUM_MODULO

    # --------------------------------------------------------
    # Helper Methods
    # --------------------------------------------------------

    def is_data(self):
        """
        Returns True if segment is DATA.
        """

        return (
            self.segment_type ==
            L4_TYPE_DATA
        )

    def is_ack(self):
        """
        Returns True if segment is ACK.
        """

        return (
            self.segment_type ==
            L4_TYPE_ACK
        )

    def get_type_name(self):
        """
        Returns readable segment type.
        """

        return L4_TYPE_NAMES.get(
            self.segment_type,
            "UNKNOWN"
        )

    def get_data_size(self):
        """
        Returns application data size.
        """

        return len(self.data)

    # --------------------------------------------------------
    # Debugging / Representation
    # --------------------------------------------------------

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

    def __str__(self):

        return (
            f"[L4 {self.get_type_name()} "
            f"SEQ={self.seq_num} "
            f"LEN={self.length}]"
        )


# ============================================================
# Layer 3 Packet
# ============================================================

class Layer3Packet:
    """
    Represents a simplified IP-like packet.

    Header fields:
    - source IP
    - destination IP
    - TTL
    - protocol
    - total length
    - payload (Layer 4 segment)
    """

    def __init__(
        self,
        src_ip,
        dst_ip,
        payload,
        ttl=DEFAULT_TTL,
        protocol=IP_PROTOCOL_UDP,
    ):

        if ttl < 0:
            raise ValueError(
                "TTL cannot be negative"
            )

        self.src_ip = src_ip
        self.dst_ip = dst_ip

        self.ttl = ttl
        self.protocol = protocol

        self.payload = payload

        # Total packet size
        self.total_length = (
            NETWORK_HEADER_SIZE +
            payload.length
        )

    # --------------------------------------------------------
    # TTL Handling
    # --------------------------------------------------------

    def decrement_ttl(self):
        """
        Decrements TTL by 1.
        """

        old_ttl = self.ttl
        self.ttl -= 1

        return old_ttl, self.ttl

    def is_expired(self):
        """
        Returns True if TTL has expired.
        """

        return self.ttl <= 0

    # --------------------------------------------------------
    # Debugging / Representation
    # --------------------------------------------------------

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

    def __str__(self):

        return (
            f"[L3 "
            f"{self.src_ip} -> "
            f"{self.dst_ip} "
            f"TTL={self.ttl}]"
        )


# ============================================================
# Layer 2 Frame
# ============================================================

class Layer2Frame:
    """
    Represents a simplified Ethernet-like frame.

    Header fields:
    - destination MAC
    - source MAC
    - type
    - payload (Layer 3 packet)
    """

    def __init__(
        self,
        src_mac,
        dst_mac,
        payload,
        frame_type=ETHERNET_TYPE_IPV4,
    ):

        if payload is None:
            raise ValueError(
                "Layer 2 payload cannot be None"
            )

        self.src_mac = src_mac
        self.dst_mac = dst_mac

        self.frame_type = frame_type

        self.payload = payload

        # Total frame size
        self.frame_length = (
            DATA_LINK_HEADER_SIZE +
            payload.total_length
        )

    # --------------------------------------------------------
    # Debugging / Representation
    # --------------------------------------------------------

    def __repr__(self):

        return (
            f"Layer2Frame("
            f"src_mac={self.src_mac}, "
            f"dst_mac={self.dst_mac}, "
            f"type={hex(self.frame_type)}, "
            f"frame_length={self.frame_length}"
            f")"
        )

    def __str__(self):

        return (
            f"[L2 "
            f"{self.src_mac} -> "
            f"{self.dst_mac}]"
        )