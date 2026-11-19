# Improv Serial protocol (https://www.improv-wifi.com/serial/): builds packets and reads them out of the byte stream,
# where they arrive mixed with the device's log lines. Pure: no serial port here (board.py does the I/O).
import re

HEADER = b"IMPROV"
VERSION = 1
TYPE_STATE, TYPE_ERROR, TYPE_RPC, TYPE_RESULT = 0x01, 0x02, 0x03, 0x04
CMD_WIFI, CMD_STATE, CMD_INFO, CMD_SCAN = 0x01, 0x02, 0x03, 0x04
STATE_READY, STATE_PROVISIONING, STATE_PROVISIONED = 0x02, 0x03, 0x04
ERRORS = {0x01: "E_IMPROV_RPC", 0x02: "E_IMPROV_RPC", 0x03: "E_IMPROV_AUTH", 0xFF: "E_IMPROV_UNKNOWN"}
IP_IN_LOG = re.compile(rb"IP Address: (\d+\.\d+\.\d+\.\d+)")


def _strings(*values: bytes) -> bytes:
    return b"".join(bytes([len(v)]) + v for v in values)


def packet(kind: int, data: bytes) -> bytes:
    body = HEADER + bytes([VERSION, kind, len(data)]) + data
    return body + bytes([sum(body) & 0xFF]) + b"\n"


def rpc(command: int, data: bytes = b"") -> bytes:
    return packet(TYPE_RPC, bytes([command, len(data)]) + data)


def wifi_rpc(ssid: str, password: str) -> bytes:
    return rpc(CMD_WIFI, _strings(ssid.encode("utf-8"), password.encode("utf-8")))


def parse(buffer: bytes) -> tuple[list[tuple[int, bytes]], bytes]:
    """Complete packets [(type, data)] found in buffer, and the bytes to keep for the next read."""
    found = []
    while (start := buffer.find(HEADER)) >= 0:
        head = start + len(HEADER)
        if len(buffer) < head + 3:
            return found, buffer[start:]
        kind, size = buffer[head + 1], buffer[head + 2]
        end = head + 3 + size
        if len(buffer) < end + 1:
            return found, buffer[start:]
        if sum(buffer[start:end]) & 0xFF == buffer[end]:
            found.append((kind, buffer[head + 3:end]))
            buffer = buffer[end + 1:]
        else:
            buffer = buffer[head:]  # bad checksum: skip this header and keep looking
    return found, buffer[-len(HEADER):]


def result_strings(data: bytes) -> tuple[int, list[str]]:
    """RPC result: (command, [strings])."""
    command, size, values, pos = data[0], data[1], [], 2
    while pos < 2 + size:
        length = data[pos]
        values.append(data[pos + 1:pos + 1 + length].decode("utf-8", "replace"))
        pos += 1 + length
    return command, values


def ip_from_log(text: bytes) -> str | None:
    match = IP_IN_LOG.search(text)
    return match.group(1).decode() if match else None
