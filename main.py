"""
main.py

Mini Internet Protocol Stack Simulator

Main entry point for the simulation.

This file:
- reads the application message size from the command line
- validates user input
- creates Host A, Router R1, and Host B
- builds the logical network topology
- starts end-to-end data transmission
- prints simulation statistics

Run with:
    python main.py 100
"""

import sys
from math import ceil
from datetime import datetime

from config import (
    HOST_A_IP,
    HOST_A_MAC,
    HOST_B_IP,
    HOST_B_MAC,

    ROUTER_R1_INTERFACE_1_IP,
    ROUTER_R1_INTERFACE_1_MAC,

    ROUTER_R1_INTERFACE_2_IP,
    ROUTER_R1_INTERFACE_2_MAC,

    HOST_A_ROUTING_TABLE,
    HOST_B_ROUTING_TABLE,
    ROUTER_R1_ROUTING_TABLE,

    HOST_A_MAC_TABLE,
    HOST_B_MAC_TABLE,
    ROUTER_R1_MAC_TABLE,

    ROUTER_INTERFACE_1,
    ROUTER_INTERFACE_2,

    MAX_SEGMENT_DATA_SIZE,
    MAX_APPLICATION_MESSAGE_SIZE,
)

from devices import Host, Router


# ============================================================
# Command-Line Utilities
# ============================================================

def print_usage():
    """
    Prints correct program usage instructions.
    """

    print("Usage: python main.py <message_size_in_bytes>")
    print("Example: python main.py 100")


def parse_message_size():
    """
    Reads and validates the application message size
    from the command line.

    Requirements:
    - must be an integer
    - must be greater than 0
    - must not exceed maximum supported size
    """

    if len(sys.argv) != 2:

        print(
            "Error: You must provide exactly one "
            "message size argument."
        )

        print_usage()
        sys.exit(1)

    try:
        message_size = int(sys.argv[1])

    except ValueError:

        print("Error: Message size must be an integer.")
        print_usage()
        sys.exit(1)

    if message_size <= 0:

        print(
            "Error: Message size must be greater than 0."
        )

        print_usage()
        sys.exit(1)

    if message_size > MAX_APPLICATION_MESSAGE_SIZE:

        print(
            f"Error: Maximum supported message size is "
            f"{MAX_APPLICATION_MESSAGE_SIZE} bytes."
        )

        sys.exit(1)

    return message_size


# ============================================================
# Network Construction
# ============================================================

def build_network():
    """
    Builds the logical network topology:

        Host A ---- Router R1 ---- Host B

    Host A connects to Router R1 Interface 1.
    Host B connects to Router R1 Interface 2.

    The design is modular so additional hosts,
    routers, or links can be added in future
    extensions of the simulator.
    """

    # --------------------------------------------------------
    # Create Host A
    # --------------------------------------------------------

    host_a = Host(
        name="Host A",
        ip_address=HOST_A_IP,
        mac_address=HOST_A_MAC,
        routing_table=HOST_A_ROUTING_TABLE,
        mac_table=HOST_A_MAC_TABLE,
    )

    # --------------------------------------------------------
    # Create Host B
    # --------------------------------------------------------

    host_b = Host(
        name="Host B",
        ip_address=HOST_B_IP,
        mac_address=HOST_B_MAC,
        routing_table=HOST_B_ROUTING_TABLE,
        mac_table=HOST_B_MAC_TABLE,
    )

    # --------------------------------------------------------
    # Create Router R1
    # --------------------------------------------------------

    router_r1 = Router(
        name="Router R1",
        routing_table=ROUTER_R1_ROUTING_TABLE,
        mac_table=ROUTER_R1_MAC_TABLE,
    )

    # --------------------------------------------------------
    # Add Router Interfaces
    # --------------------------------------------------------

    router_r1.add_interface(
        interface_name=ROUTER_INTERFACE_1,
        ip_address=ROUTER_R1_INTERFACE_1_IP,
        mac_address=ROUTER_R1_INTERFACE_1_MAC,
    )

    router_r1.add_interface(
        interface_name=ROUTER_INTERFACE_2,
        ip_address=ROUTER_R1_INTERFACE_2_IP,
        mac_address=ROUTER_R1_INTERFACE_2_MAC,
    )

    # --------------------------------------------------------
    # Connect Host A
    # --------------------------------------------------------

    host_a.connect_to_router(
        router=router_r1,
        router_interface=ROUTER_INTERFACE_1,
    )

    router_r1.connect_interface(
        interface_name=ROUTER_INTERFACE_1,
        connected_device=host_a,
    )

    # --------------------------------------------------------
    # Connect Host B
    # --------------------------------------------------------

    host_b.connect_to_router(
        router=router_r1,
        router_interface=ROUTER_INTERFACE_2,
    )

    router_r1.connect_interface(
        interface_name=ROUTER_INTERFACE_2,
        connected_device=host_b,
    )

    return host_a, router_r1, host_b


# ============================================================
# Main Simulation
# ============================================================

def main():
    """
    Runs the full protocol stack simulation.
    """

    message_size = parse_message_size()

    expected_segments = ceil(
        message_size / MAX_SEGMENT_DATA_SIZE
    )

    host_a, router_r1, host_b = build_network()

    # --------------------------------------------------------
    # Simulation Header
    # --------------------------------------------------------

    print("Mini Internet Protocol Stack Simulator")
    print("--------------------------------------")

    print(
        f"Simulation started at: "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print("--------------------------------------")

    print("Network Topology:")
    print("Host A ---- Router R1 ---- Host B")

    print("--------------------------------------")

    print(
        f"Application message size: "
        f"{message_size} bytes"
    )

    print(f"Expected transport segments: {expected_segments}")

    print("Source: Host A")
    print("Destination: Host B")

    print("--------------------------------------")

    # --------------------------------------------------------
    # Start Transmission
    # --------------------------------------------------------

    try:

        host_a.send_application_data(
            data_size=message_size,
            destination_ip=HOST_B_IP,
        )

    except Exception as error:

        print("--------------------------------------")
        print(f"Simulation failed: {error}")
        sys.exit(1)

    # --------------------------------------------------------
    # Simulation Statistics
    # --------------------------------------------------------

    print("--------------------------------------")
    print("Simulation Statistics")
    print("--------------------------------------")

    print(
        f"Total DATA segments sent: "
        f"{host_a.total_segments_sent}"
    )

    print(
        f"Total ACKs received: "
        f"{host_a.total_acks_received}"
    )

    print(
        f"Total retransmissions: "
        f"{host_a.total_retransmissions}"
    )

    print("--------------------------------------")

    print(
        "Simulation complete successfully."
    )

    print(
        "All application data delivered reliably."
    )


# ============================================================
# Program Entry Point
# ============================================================

if __name__ == "__main__":
    main()