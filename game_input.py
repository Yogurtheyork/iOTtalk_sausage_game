"""Validated, bounded localhost-only sensor transport."""
import json
import math
import os
import socket


def configured_port():
    port = int(os.environ.get('SAUSAGE_PORT', '8765'))
    if not 1 <= port <= 65535:
        raise ValueError('SAUSAGE_PORT must be 1..65535')
    return port


def parse_axes(data):
    if isinstance(data, (list, tuple)) and len(data) == 1:
        data = data[0]
    if not isinstance(data, (list, tuple)) or len(data) != 3:
        return None
    if any(type(v) not in (int, float) or not -1e6 <= v <= 1e6 for v in data):
        return None
    return tuple(float(v) for v in data)


def send_axes(axes, port):
    axes = parse_axes(axes)
    if axes is None:
        return
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
        try:
            sender.sendto(json.dumps(axes).encode(), ('127.0.0.1', port))
        except OSError:
            pass  # The game may not be running yet.


class SensorReceiver:
    def __init__(self, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.socket.bind(('127.0.0.1', port))
            self.socket.setblocking(False)
        except OSError:
            self.socket.close()
            raise

    def poll(self, now):
        latest = None
        for _ in range(64):
            try:
                data, _ = self.socket.recvfrom(257)
            except BlockingIOError:
                break
            if len(data) > 256:
                continue
            try:
                axes = parse_axes(json.loads(data))
            except (ValueError, UnicodeError, RecursionError):
                continue
            if axes is not None:
                latest = axes
        else:
            # Rebinding drops queued old motion without an unbounded drain loop.
            port = self.socket.getsockname()[1]
            self.close()
            self.__init__(port)
            return []
        return [] if latest is None else [(now, latest)]

    def close(self):
        self.socket.close()
