# Mini Internet Protocol Stack Simulator

This project implements a logical Python simulation of data delivery from
Host A to Host B through Router R1. It demonstrates the required Layer 2,
Layer 3, and Layer 4 behaviours from the CITS3002 project specification.

## Topology

```text
Host A ---- Router R1 ---- Host B
```

The topology contains two /24 networks:

- Network 1: `10.0.1.0/24`
- Network 2: `10.0.2.0/24`

## Addressing

| Device/interface | IP address | MAC address |
| --- | --- | --- |
| Host A | `10.0.1.10` | `AA:AA:AA:AA:AA:AA` |
| Router R1 Interface 1 | `10.0.1.1` | `BB:BB:BB:BB:BB:BB` |
| Router R1 Interface 2 | `10.0.2.1` | `CC:CC:CC:CC:CC:CC` |
| Host B | `10.0.2.20` | `DD:DD:DD:DD:DD:DD` |

## Files

- `main.py` is the required entry point. It validates the message size,
  builds the topology, starts the transmission, and prints structured protocol logs.
- `config.py` stores fixed constants, IP/MAC addresses, routing tables,
  MAC lookup tables, header sizes, and transport limits.
- `protocol.py` defines the Layer 2 frame, Layer 3 packet, and Layer 4
  segment classes.
- `devices.py` implements the shared device logic, the `Host` class, and
  the `Router` class.

## Implemented requirements

### Layer 2: Data Link

- Creates Ethernet-like frames with source MAC, destination MAC, type, and
  Layer 3 payload.
- Uses next-hop IP to destination MAC lookup tables.
- Learns source MAC addresses from received frames.
- Forwards frames across Router R1 interfaces.
- Delivers valid Layer 3 packets upward.

### Layer 3: Network

- Creates IP-like packets with source IP, destination IP, TTL, protocol, and
  total length.
- Uses routing tables to choose next-hop IP addresses and outgoing interfaces.
- Performs subnet matching manually with bitwise masking (no address-handling
  library), so routing relies only on basic Python arithmetic.
- Decrements TTL at Router R1.
- Drops packets if TTL expires.
- Delivers local packets to the transport layer.

### Layer 4: Transport

- Segments application data into payloads of at most 500 bytes.
- Creates UDP-like DATA and ACK segments.
- Computes segment length as header plus payload data.
- Computes and verifies a simple 16-bit checksum.
- Uses alternating sequence numbers `0` and `1`, flipping the sender's send
  bit only after a correct ACK and the receiver's expected bit only after an
  in-order DATA segment. The alternation is visible across multiple segments
  through the per-segment `(DATA, seq=...)` and `ACK ... seq=...` log lines
  (for example a 1200-byte message shows seq `0 -> 1 -> 0`).
- A correct ACK carries the same sequence number as the DATA segment it
  acknowledges; a duplicate DATA segment causes the receiver to re-send its
  last ACK, and an incorrect/duplicate ACK causes the sender to retransmit the
  current segment with the same sequence number.
- Waits for the correct ACK before sending the next DATA segment.

## Running the simulator

Run the program from this directory:

```bash
python main.py <message_size_in_bytes>
```

Example:

```bash
python main.py 100
```

The message size must be a positive integer. Messages larger than 500 bytes
are automatically segmented into multiple DATA segments.


## Suggested tests

```bash
python main.py 1
python main.py 10
python main.py 500
python main.py 501
python main.py 1200
```

These tests cover minimum payload delivery, the sample 10-byte transfer,
the 500-byte segmentation boundary, the 501-byte edge case, and a
multi-segment transfer.

## Notes

The simulator is deterministic and uses only the Python standard library. The
only import outside the project's own modules is `sys` (for reading the
command-line argument); subnet matching and all protocol logic are implemented
directly. It does not use sockets, real network interfaces, external packages,
threads, or packet loss. All transmissions are simulated through method calls so
the logs clearly show the flow of data through each protocol layer.
