"""
config.py

Configuration module for the Mini Internet Protocol Stack Simulator.

This file keeps all fixed project values in one place so that the protocol
logic in the other files does not contain hard-coded addresses or constants.
It defines:
- protocol constants used by Layer 2, Layer 3, and Layer 4;
- IP and MAC addresses for Host A, Router R1, and Host B;
- interface names used by routing and logging;
- MAC lookup tables used by Layer 2;
- routing tables used by Layer 3.
"""


# Protocol constants

# Ethernet type value used in Layer 2 frames to indicate an IPv4-like payload.
ETHERNET_TYPE_IPV4 = 0x0800

# Protocol number used in Layer 3 packets to indicate a UDP-like payload.
IP_PROTOCOL_UDP = 17

# Default TTL for every new Layer 3 packet. Router R1 decrements this to 99.
DEFAULT_TTL = 100

# Layer 4 segment type values. DATA carries application data; ACK confirms data.
L4_TYPE_DATA = 0
L4_TYPE_ACK = 1

# Maximum amount of application data allowed in one Layer 4 DATA segment.
MAX_SEGMENT_DATA_SIZE = 500

# Simplified header sizes used to calculate segment, packet, and frame lengths.
TRANSPORT_HEADER_SIZE = 10
NETWORK_HEADER_SIZE = 12
DATA_LINK_HEADER_SIZE = 14



# IP addressing scheme
# These values match the project topology. Host A is on network 10.0.1.0/24,
# and Host B is on network 10.0.2.0/24. Router R1 connects the two networks.

HOST_A_IP = "10.0.1.10"
ROUTER_R1_INTERFACE_1_IP = "10.0.1.1"
ROUTER_R1_INTERFACE_2_IP = "10.0.2.1"
HOST_B_IP = "10.0.2.20"



# MAC addressing scheme
# MAC addresses are used by Layer 2 for local-link delivery. Router R1 has two
# MAC addresses because it has one interface on each subnet.

HOST_A_MAC = "AA:AA:AA:AA:AA:AA"
ROUTER_R1_INTERFACE_1_MAC = "BB:BB:BB:BB:BB:BB"
ROUTER_R1_INTERFACE_2_MAC = "CC:CC:CC:CC:CC:CC"
HOST_B_MAC = "DD:DD:DD:DD:DD:DD"



# Transport-layer ports
# These port values identify the simulated sending and receiving applications.

HOST_A_PORT = 5000
HOST_B_PORT = 80



# Interface labels used in routing tables and logs
# The host interface names are simple labels. Router interface names must match
# the project output format: Interface 1 and Interface 2.

HOST_A_INTERFACE = "Host A Interface"
HOST_B_INTERFACE = "Host B Interface"
ROUTER_INTERFACE_1 = "Interface 1"
ROUTER_INTERFACE_2 = "Interface 2"



# MAC lookup tables for Layer 2
# Layer 3 decides the next-hop IP address. Layer 2 then uses these tables to
# convert the next-hop IP into a destination MAC address for the local frame.
# This simulates ARP-style address resolution without implementing ARP.

# Host A sends traffic for Host B's network to Router R1 Interface 1.
HOST_A_MAC_TABLE = {
    ROUTER_R1_INTERFACE_1_IP: ROUTER_R1_INTERFACE_1_MAC,
}

# Host B sends ACK traffic for Host A's network to Router R1 Interface 2.
HOST_B_MAC_TABLE = {
    ROUTER_R1_INTERFACE_2_IP: ROUTER_R1_INTERFACE_2_MAC,
}

# Router R1 needs MAC entries for both directly connected hosts and interfaces.
ROUTER_R1_MAC_TABLE = {
    HOST_A_IP: HOST_A_MAC,
    HOST_B_IP: HOST_B_MAC,
    ROUTER_R1_INTERFACE_1_IP: ROUTER_R1_INTERFACE_1_MAC,
    ROUTER_R1_INTERFACE_2_IP: ROUTER_R1_INTERFACE_2_MAC,
}


# Routing tables for Layer 3
# Each route contains:
# - destination_network: the IP subnet being matched;
# - next_hop_ip: the next device to send the packet to;
# - outgoing_interface: the interface used to send the packet.
# If next_hop_ip is None, the destination is directly connected and the
# destination IP itself becomes the next hop.

HOST_A_ROUTING_TABLE = [
    {
        "destination_network": "10.0.2.0/24",
        "next_hop_ip": ROUTER_R1_INTERFACE_1_IP,
        "outgoing_interface": HOST_A_INTERFACE,
    },
    {
        "destination_network": "10.0.1.0/24",
        "next_hop_ip": None,
        "outgoing_interface": HOST_A_INTERFACE,
    },
]

HOST_B_ROUTING_TABLE = [
    {
        "destination_network": "10.0.1.0/24",
        "next_hop_ip": ROUTER_R1_INTERFACE_2_IP,
        "outgoing_interface": HOST_B_INTERFACE,
    },
    {
        "destination_network": "10.0.2.0/24",
        "next_hop_ip": None,
        "outgoing_interface": HOST_B_INTERFACE,
    },
]

ROUTER_R1_ROUTING_TABLE = [
    {
        "destination_network": "10.0.1.0/24",
        "next_hop_ip": HOST_A_IP,
        "outgoing_interface": ROUTER_INTERFACE_1,
    },
    {
        "destination_network": "10.0.2.0/24",
        "next_hop_ip": HOST_B_IP,
        "outgoing_interface": ROUTER_INTERFACE_2,
    },
]
