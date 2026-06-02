"""Run the relayer + ibc_attestor binaries as managed sidecars and build their
configs, so an integration test can stand up the proof API and talk to it via the
stubs. process/relayer are pure stdlib; attestor imports eth-utils.
"""

from __future__ import annotations

import socket
import time


def free_port() -> int:
    """Bind to an ephemeral port, close, return the number."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for_port(port: int, host: str = "127.0.0.1", timeout: float = 40.0) -> None:
    start = time.perf_counter()
    while True:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return
        except OSError as ex:
            time.sleep(0.1)
            if time.perf_counter() - start >= timeout:
                raise TimeoutError(
                    f"Waited too long for {host}:{port} to accept connections."
                ) from ex
