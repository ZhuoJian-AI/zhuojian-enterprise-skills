#!/usr/bin/env python3
"""Perform a SQL Server TDS PRELOGIN handshake without authentication or SQL."""

from __future__ import annotations

import argparse
import json
import socket
import struct
import sys


def build_prelogin_packet() -> bytes:
    # VERSION at offset 11 (6 bytes), ENCRYPTION at offset 17 (1 byte), terminator.
    payload = bytes.fromhex(
        "00 00 0b 00 06 "
        "01 00 11 00 01 "
        "ff "
        "00 00 00 00 00 00 "
        "00"
    )
    header = bytes((0x12, 0x01)) + struct.pack(">H", 8 + len(payload)) + bytes(4)
    return header + payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify that an endpoint responds as SQL Server without logging in."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=11433)
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()

    result = {
        "host": args.host,
        "port": args.port,
        "authenticated": False,
        "sqlExecuted": False,
    }
    try:
        with socket.create_connection((args.host, args.port), args.timeout) as connection:
            connection.settimeout(args.timeout)
            connection.sendall(build_prelogin_packet())
            response = connection.recv(512)
        passed = len(response) >= 8 and response[0] == 0x04
        result.update(
            status="pass" if passed else "fail",
            responseBytes=len(response),
            packetType=response[0] if response else None,
        )
    except (OSError, TimeoutError) as exc:
        passed = False
        result.update(status="fail", error=f"{type(exc).__name__}: {exc}")

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
