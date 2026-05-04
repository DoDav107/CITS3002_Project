# Stores fixed values 
#IP addresses
#MAC addresses
#Routing tables
#MAC lookup tables
#Port numbers
#Default TTL
#Maximum segment size

"""
config.py

This file stores all fixed configuration values for the mini Internet
protocol stack simulator.

It includes:
- IP addresses
- MAC addresses
- port numbers
- default TTL
- maximum segment size
- MAC lookup tables
- routing tables
"""

# ------------------------------------------------------------
# General protocol constants
# ------------------------------------------------------------

ETHERNET_TYPE_IPV4 = 0x0800
IP_PROTOCOL_UDP = 17

DEFAULT_TTL = 4

L4_TYPE_DATA = 0
L4_TYPE_ACK = 1

MAX_SEGMENT_DATA_SIZE = 500

TRANSPORT_HEADER_SIZE = 10
NETWORK_HEADER_SIZE = 12
DATA_LINK_HEADER_SIZE = 14


# ------------------------------------------------------------
# IP addressing scheme
# ------------------------------------------------------------

HOST_A_IP = "10.0.1.10"
ROUTER_R1_INTERFACE_1_IP = "10.0.1.1"
ROUTER_R1_INTERFACE_2_IP = "10.0.2.1"
HOST_B_IP = "10.0.2.20"


# ------------------------------------------------------------
# MAC addressing scheme
# ------------------------------------------------------------

HOST_A_MAC = "AA:AA:AA:AA:AA:AA"
ROUTER_R1_INTERFACE_1_MAC = "BB:BB:BB:BB:BB:BB"
ROUTER_R1_INTERFACE_2_MAC = "CC:CC:CC:CC:CC:CC"
HOST_B_MAC = "DD:DD:DD:DD:DD:DD"


# ------------------------------------------------------------
# Transport layer ports
# ------------------------------------------------------------

HOST_A_PORT = 5000
HOST_B_PORT = 80


# ------------------------------------------------------------
# Interface names
# ------------------------------------------------------------

HOST_A_INTERFACE = "Host A Interface"
HOST_B_INTERFACE = "Host B Interface"

ROUTER_INTERFACE_1 = "Interface 1"
ROUTER_INTERFACE_2 = "Interface 2"


# ------------------------------------------------------------
# MAC lookup tables
# These map next-hop IP addresses to MAC addresses.
# Layer 2 uses these tables to decide the destination MAC.
# ------------------------------------------------------------

HOST_A_MAC_TABLE = {
    ROUTER_R1_INTERFACE_1_IP: ROUTER_R1_INTERFACE_1_MAC
}

HOST_B_MAC_TABLE = {
    ROUTER_R1_INTERFACE_2_IP: ROUTER_R1_INTERFACE_2_MAC
}

ROUTER_R1_MAC_TABLE = {
    HOST_A_IP: HOST_A_MAC,
    HOST_B_IP: HOST_B_MAC,
    ROUTER_R1_INTERFACE_1_IP: ROUTER_R1_INTERFACE_1_MAC,
    ROUTER_R1_INTERFACE_2_IP: ROUTER_R1_INTERFACE_2_MAC
}


# ------------------------------------------------------------
# Routing tables
#
# Each entry maps a destination network to:
# - next_hop_ip
# - outgoing_interface
#
# For directly connected destinations, the next-hop IP is the
# destination host itself.
# ------------------------------------------------------------

HOST_A_ROUTING_TABLE = [
    {
        "destination_network": "10.0.2.0/24",
        "next_hop_ip": ROUTER_R1_INTERFACE_1_IP,
        "outgoing_interface": HOST_A_INTERFACE
    },
    {
        "destination_network": "10.0.1.0/24",
        "next_hop_ip": None,
        "outgoing_interface": HOST_A_INTERFACE
    }
]

HOST_B_ROUTING_TABLE = [
    {
        "destination_network": "10.0.1.0/24",
        "next_hop_ip": ROUTER_R1_INTERFACE_2_IP,
        "outgoing_interface": HOST_B_INTERFACE
    },
    {
        "destination_network": "10.0.2.0/24",
        "next_hop_ip": None,
        "outgoing_interface": HOST_B_INTERFACE
    }
]

ROUTER_R1_ROUTING_TABLE = [
    {
        "destination_network": "10.0.1.0/24",
        "next_hop_ip": HOST_A_IP,
        "outgoing_interface": ROUTER_INTERFACE_1
    },
    {
        "destination_network": "10.0.2.0/24",
        "next_hop_ip": HOST_B_IP,
        "outgoing_interface": ROUTER_INTERFACE_2
    }
]
