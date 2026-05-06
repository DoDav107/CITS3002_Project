"""
config.py

Mini Internet Protocol Stack Simulator

This file stores all fixed configuration values used throughout the
simulation.

It includes:
- protocol constants
- IP addressing information
- MAC addressing information
- transport-layer settings
- interface definitions
- routing tables
- MAC lookup tables
- retransmission settings
"""

# ============================================================
# Protocol Constants
# ============================================================

ETHERNET_TYPE_IPV4 = 0x0800
IP_PROTOCOL_UDP = 17

DEFAULT_TTL = 100

L4_TYPE_DATA = 0
L4_TYPE_ACK = 1

L4_TYPE_NAMES = {
    L4_TYPE_DATA: "DATA",
    L4_TYPE_ACK: "ACK",
}

# ============================================================
# Transport Configuration
# ============================================================

MAX_SEGMENT_DATA_SIZE = 500

TRANSPORT_HEADER_SIZE = 10
NETWORK_HEADER_SIZE = 12
DATA_LINK_HEADER_SIZE = 14

CHECKSUM_MODULO = 0xFFFF

MAX_RETRANSMISSIONS = 3
ACK_TIMEOUT_SECONDS = 1

MAX_APPLICATION_MESSAGE_SIZE = 100000

# ============================================================
# Network Definitions
# ============================================================

NETWORK_1 = "10.0.1.0/24"
NETWORK_2 = "10.0.2.0/24"

NETWORK_PREFIX_LENGTH = 24

# ============================================================
# IP Addressing Scheme
# ============================================================

HOST_A_IP = "10.0.1.10"

ROUTER_R1_INTERFACE_1_IP = "10.0.1.1"
ROUTER_R1_INTERFACE_2_IP = "10.0.2.1"

HOST_B_IP = "10.0.2.20"

# ============================================================
# MAC Addressing Scheme
# ============================================================

HOST_A_MAC = "AA:AA:AA:AA:AA:AA"

ROUTER_R1_INTERFACE_1_MAC = "BB:BB:BB:BB:BB:BB"
ROUTER_R1_INTERFACE_2_MAC = "CC:CC:CC:CC:CC:CC"

HOST_B_MAC = "DD:DD:DD:DD:DD:DD"

# ============================================================
# Transport Layer Ports
# ============================================================

HOST_A_PORT = 5000
HOST_B_PORT = 80

# ============================================================
# Interface Names
# ============================================================

HOST_A_INTERFACE = "Host A Interface"
HOST_B_INTERFACE = "Host B Interface"

ROUTER_INTERFACE_1 = "Interface 1"
ROUTER_INTERFACE_2 = "Interface 2"

# ============================================================
# Device Metadata
# ============================================================

DEVICES = {
    "Host A": {
        "ip": HOST_A_IP,
        "mac": HOST_A_MAC,
        "port": HOST_A_PORT,
        "interface": HOST_A_INTERFACE,
    },

    "Host B": {
        "ip": HOST_B_IP,
        "mac": HOST_B_MAC,
        "port": HOST_B_PORT,
        "interface": HOST_B_INTERFACE,
    },

    "Router R1": {
        "interfaces": {
            ROUTER_INTERFACE_1: {
                "ip": ROUTER_R1_INTERFACE_1_IP,
                "mac": ROUTER_R1_INTERFACE_1_MAC,
            },

            ROUTER_INTERFACE_2: {
                "ip": ROUTER_R1_INTERFACE_2_IP,
                "mac": ROUTER_R1_INTERFACE_2_MAC,
            },
        }
    }
}

# ============================================================
# Router Interface Configuration
# ============================================================

ROUTER_INTERFACES = {
    ROUTER_INTERFACE_1: {
        "ip": ROUTER_R1_INTERFACE_1_IP,
        "mac": ROUTER_R1_INTERFACE_1_MAC,
    },

    ROUTER_INTERFACE_2: {
        "ip": ROUTER_R1_INTERFACE_2_IP,
        "mac": ROUTER_R1_INTERFACE_2_MAC,
    },
}

# ============================================================
# MAC Lookup Tables
#
# These tables map:
# next-hop IP address -> destination MAC address
#
# Layer 2 uses these tables to determine where frames
# should be sent locally.
# ============================================================

HOST_A_MAC_TABLE = {
    ROUTER_R1_INTERFACE_1_IP: ROUTER_R1_INTERFACE_1_MAC,
}

HOST_B_MAC_TABLE = {
    ROUTER_R1_INTERFACE_2_IP: ROUTER_R1_INTERFACE_2_MAC,
}

ROUTER_R1_MAC_TABLE = {
    HOST_A_IP: HOST_A_MAC,
    HOST_B_IP: HOST_B_MAC,

    ROUTER_R1_INTERFACE_1_IP: ROUTER_R1_INTERFACE_1_MAC,
    ROUTER_R1_INTERFACE_2_IP: ROUTER_R1_INTERFACE_2_MAC,
}

# ============================================================
# Routing Tables
#
# Each route entry defines:
# - destination network
# - next-hop IP address
# - outgoing interface
#
# If next_hop_ip is None:
# the destination is directly connected.
# ============================================================

HOST_A_ROUTING_TABLE = [
    {
        "destination_network": NETWORK_2,
        "next_hop_ip": ROUTER_R1_INTERFACE_1_IP,
        "outgoing_interface": HOST_A_INTERFACE,
    },

    {
        "destination_network": NETWORK_1,
        "next_hop_ip": None,
        "outgoing_interface": HOST_A_INTERFACE,
    },
]

HOST_B_ROUTING_TABLE = [
    {
        "destination_network": NETWORK_1,
        "next_hop_ip": ROUTER_R1_INTERFACE_2_IP,
        "outgoing_interface": HOST_B_INTERFACE,
    },

    {
        "destination_network": NETWORK_2,
        "next_hop_ip": None,
        "outgoing_interface": HOST_B_INTERFACE,
    },
]

ROUTER_R1_ROUTING_TABLE = [
    {
        "destination_network": NETWORK_1,
        "next_hop_ip": HOST_A_IP,
        "outgoing_interface": ROUTER_INTERFACE_1,
    },

    {
        "destination_network": NETWORK_2,
        "next_hop_ip": HOST_B_IP,
        "outgoing_interface": ROUTER_INTERFACE_2,
    },
]