"""
main.py

Required entry point for the Mini Internet Protocol Stack Simulator.

This file is intentionally small because the project structure separates setup,
configuration, protocol data classes, and device behaviour. The marker runs this
file with a message-size argument, for example:

    python main.py 100

main.py validates the input, builds the topology
Host A ---- Router R1 ---- Host B, and starts the end-to-end transmission from
Host A to Host B.
"""

import sys

from config import (
    HOST_A_IP,
    HOST_A_MAC,
    HOST_A_MAC_TABLE,
    HOST_A_ROUTING_TABLE,
    HOST_B_IP,
    HOST_B_MAC,
    HOST_B_MAC_TABLE,
    HOST_B_ROUTING_TABLE,
    ROUTER_INTERFACE_1,
    ROUTER_INTERFACE_2,
    ROUTER_R1_INTERFACE_1_IP,
    ROUTER_R1_INTERFACE_1_MAC,
    ROUTER_R1_INTERFACE_2_IP,
    ROUTER_R1_INTERFACE_2_MAC,
    ROUTER_R1_MAC_TABLE,
    ROUTER_R1_ROUTING_TABLE,
)
from devices import Host, Router


def print_usage():
    """
    Print the correct command-line format.

    Purpose:
        Helps the user or marker run the program correctly if the message-size
        argument is missing or invalid.
    """

    print("Usage: python main.py <message_size_in_bytes>")
    print("Example: python main.py 100")


def parse_message_size():
    """
    Read and validate the application message size from the command line.

    Purpose:
        The project requires main.py to accept the message size as a command-line
        argument. This function protects the rest of the simulator from invalid
        inputs by only returning a positive integer.
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
    Create and connect Host A, Router R1, and Host B.

    Purpose:
        Builds the exact logical topology required by the assignment:
        Host A connects to Router R1 Interface 1, and Host B connects to Router
        R1 Interface 2. The returned objects are then used to start simulation.
    """

    # Create Host A using its fixed IP, MAC, routing table, and MAC table.
    host_a = Host(
        name="Host A",
        ip_address=HOST_A_IP,
        mac_address=HOST_A_MAC,
        routing_table=HOST_A_ROUTING_TABLE,
        mac_table=HOST_A_MAC_TABLE,
    )

    # Create Host B using its fixed IP, MAC, routing table, and MAC table.
    host_b = Host(
        name="Host B",
        ip_address=HOST_B_IP,
        mac_address=HOST_B_MAC,
        routing_table=HOST_B_ROUTING_TABLE,
        mac_table=HOST_B_MAC_TABLE,
    )

    # Create Router R1 with its routing table and MAC lookup table.
    router_r1 = Router(
        name="Router R1",
        routing_table=ROUTER_R1_ROUTING_TABLE,
        mac_table=ROUTER_R1_MAC_TABLE,
    )

    # Register Router R1 Interface 1 on Network 1.
    router_r1.add_interface(
        interface_name=ROUTER_INTERFACE_1,
        ip_address=ROUTER_R1_INTERFACE_1_IP,
        mac_address=ROUTER_R1_INTERFACE_1_MAC,
    )

    # Register Router R1 Interface 2 on Network 2.
    router_r1.add_interface(
        interface_name=ROUTER_INTERFACE_2,
        ip_address=ROUTER_R1_INTERFACE_2_IP,
        mac_address=ROUTER_R1_INTERFACE_2_MAC,
    )

    # Connect both sides of the Host A <-> Router R1 Interface 1 link.
    host_a.connect_to_router(
        router=router_r1,
        router_interface=ROUTER_INTERFACE_1,
    )
    router_r1.connect_interface(
        interface_name=ROUTER_INTERFACE_1,
        connected_device=host_a,
    )

    # Connect both sides of the Host B <-> Router R1 Interface 2 link.
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
    Run the complete simulation.

    Purpose:
        Coordinates the high-level workflow: parse input, build topology, print a
        short header, start Host A's transmission, and print completion.
    """

    message_size = parse_message_size()
    host_a, router_r1, host_b = build_network()

    # The router and Host B objects are created inside build_network(). They are
    # used indirectly when Host A sends frames through the connected topology.
    _ = router_r1, host_b

    print("Mini Internet Protocol Stack Simulator")
    print("--------------------------------------")
    print(f"Application message size: {message_size} bytes")
    print("Source: Host A")
    print("Destination: Host B")
    print("--------------------------------------")

    # Start the required data flow: Host A sends application data to Host B.
    host_a.send_application_data(
        data_size=message_size,
        destination_ip=HOST_B_IP,
    )

    print("--------------------------------------")
    print("Simulation complete.")


if __name__ == "__main__":
    main()
