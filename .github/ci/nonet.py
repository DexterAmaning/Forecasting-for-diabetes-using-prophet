"""Pytest plugin used by CI: any outbound network connection fails the run.

The tests read only the data committed in data/raw/, so they must pass offline.
"""

import socket

_connect = socket.socket.connect
_connect_ex = socket.socket.connect_ex


def _refuse(sock, address):
    if sock.family in (socket.AF_INET, socket.AF_INET6):
        raise RuntimeError(f"network access is blocked during tests: {address!r}")


def _guarded_connect(self, address):
    _refuse(self, address)
    return _connect(self, address)


def _guarded_connect_ex(self, address):
    _refuse(self, address)
    return _connect_ex(self, address)


socket.socket.connect = _guarded_connect
socket.socket.connect_ex = _guarded_connect_ex
