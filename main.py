# read the agrument 
# create Host A, Router R1, and Host B
# connect them logically
# start sending data from Host A to Host B 

"""
main.py

Main entry point for the Mini Internet Protocol Stack Simulator.

This file:
- reads the application message size from the command line
- creates Host A, Router R1, and Host B
- connects the devices together logically
- starts the end-to-end transmission from Host A to Host B

Run with:
    python main.py 100
"""

import sys

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
)

from devices import Host, Router


def print_usage():
    """
    Prints correct program usage.
    """

    print("Usage: python main.py <message_size_in_bytes>")
    print("Example: python main.py 100")


def parse_message_size():
    """
    Reads and validates the message size from the command line.

    The message size must be a positive integer.
    """

    if len(sys.argv) != 2:
        print("Error: You must provide exactly one message size argument.")
        print_usage()
        sys.exit(1)

    try:
        message_size = int(sys.argv[1])
    except ValueError:
        print("Error: Message size must be an integer.")
        print_usage()
        sys.exit(1)

    if message_size <= 0:
        print("Error: Message size must be greater than 0.")
        print_usage()
        sys.exit(1)

    return message_size


def build_network():
    """
    Creates the logical network topology:

        Host A ---- Router R1 ---- Host B

    Host A is connected to Router R1 Interface 1.
    Host B is connected to Router R1 Interface 2.
    """

    # Create Host A.
    host_a = Host(
        name="Host A",
        ip_address=HOST_A_IP,
        mac_address=HOST_A_MAC,
        routing_table=HOST_A_ROUTING_TABLE,
        mac_table=HOST_A_MAC_TABLE,
    )

    # Create Host B.
    host_b = Host(
        name="Host B",
        ip_address=HOST_B_IP,
        mac_address=HOST_B_MAC,
        routing_table=HOST_B_ROUTING_TABLE,
        mac_table=HOST_B_MAC_TABLE,
    )

    # Create Router R1.
    router_r1 = Router(
        name="Router R1",
        routing_table=ROUTER_R1_ROUTING_TABLE,
        mac_table=ROUTER_R1_MAC_TABLE,
    )

    # Add Router R1 interfaces.
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

    # Connect Host A to Router R1 Interface 1.
    host_a.connect_to_router(
        router=router_r1,
        router_interface=ROUTER_INTERFACE_1,
    )

    router_r1.connect_interface(
        interface_name=ROUTER_INTERFACE_1,
        connected_device=host_a,
    )

    # Connect Host B to Router R1 Interface 2.
    host_b.connect_to_router(
        router=router_r1,
        router_interface=ROUTER_INTERFACE_2,
    )

    router_r1.connect_interface(
        interface_name=ROUTER_INTERFACE_2,
        connected_device=host_b,
    )

    return host_a, router_r1, host_b


def main():
    """
    Runs the full simulation.
    """

    message_size = parse_message_size()

    host_a, router_r1, host_b = build_network()

    print("Mini Internet Protocol Stack Simulator")
    print("--------------------------------------")
    print(f"Application message size: {message_size} bytes")
    print("Source: Host A")
    print("Destination: Host B")
    print("--------------------------------------")

    # Start the end-to-end transmission from Host A to Host B.
    host_a.send_application_data(
        data_size=message_size,
        destination_ip=HOST_B_IP,
    )

    print("--------------------------------------")
    print("Simulation complete.")


if __name__ == "__main__":
    main()