"""DTLS transport for newer Wi-Fi/LAN Kit-20 dongles.

Newer Kit-20 firmware (some dongle revisions marketed as "Cyber Security
dongle") moves the local Modbus port from plaintext UDP/8899 to DTLS-protected
UDP/8899. The standard ``WIFIKIT-214028-READ`` discovery probe to UDP/48899
returns ``dtls_port:8899`` for affected dongles, while the existing
:class:`UdpInverterProtocol` silently times out against them.

This module adds an opt-in transport that runs the unchanged Modbus RTU
framing over DTLS. Application protocol (frames, register layout, slave
addresses, response prefix) is identical to the plaintext path; only the
transport layer is different.

Empirically observed handshake parameters:
    - DTLS 1.2 negotiated by default with OpenSSL 3.0+ defaults
      (cipher ECDHE-RSA-AES256-GCM-SHA384 in our test). DTLS 1.0 also accepted.
    - The dongle presents a self-signed placeholder certificate, so peer
      verification must be disabled (``SSL_VERIFY_NONE``).
    - The dongle accepts only one concurrent DTLS session.

Sessions are opened lazily on first request and reused (``keep_alive=True``).
On transient UDP loss the session is preserved and the request is retried
once on the same session after draining any stale buffered data; only
persistent failures tear the session down.

Requires pyOpenSSL — install via ``pip install goodwe[dtls]``.
"""

from __future__ import annotations

import asyncio
import logging
import select
import socket
import time
from asyncio.futures import Future
from typing import Optional

from .exceptions import RequestFailedException
from .protocol import (
    InverterProtocol,
    ModbusRtuReadCommand,
    ModbusRtuWriteCommand,
    ModbusRtuWriteMultiCommand,
    ProtocolCommand,
)

logger = logging.getLogger(__name__)

try:
    from OpenSSL import SSL
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "DTLS transport requires pyOpenSSL. Install with: pip install goodwe[dtls]"
    ) from exc


class DTLSInverterProtocol(InverterProtocol):
    """Modbus-over-DTLS transport for newer GoodWe Kit-20 firmware.

    Drop-in replacement for :class:`UdpInverterProtocol` when the dongle
    speaks DTLS on UDP/8899. Same Modbus RTU framing, same register layout —
    only the transport is encrypted.
    """

    #: OpenSSL cipher selection. ``@SECLEVEL=0`` accepts the dongle's
    #: self-signed cert; the rest is the OpenSSL default list. Subclass and
    #: override this attribute if a different firmware revision needs a
    #: different cipher set.
    DEFAULT_CIPHER_LIST = b"DEFAULT:@SECLEVEL=0"

    def __init__(self, host: str, port: int, comm_addr: int,
                 timeout: int = 2, retries: int = 3):
        super().__init__(host, port, comm_addr, timeout, retries)
        # The DTLS handshake is expensive (~1 s); reuse the session.
        self.keep_alive = True
        self._sock: Optional[socket.socket] = None
        self._conn: Optional["SSL.Connection"] = None

    # ----- command factories (identical to UDP/RTU path) -----

    def read_command(self, offset: int, count: int) -> ProtocolCommand:
        return ModbusRtuReadCommand(self._comm_addr, offset, count)

    def write_command(self, register: int, value: int) -> ProtocolCommand:
        return ModbusRtuWriteCommand(self._comm_addr, register, value)

    def write_multi_command(self, offset: int, values: bytes) -> ProtocolCommand:
        return ModbusRtuWriteMultiCommand(self._comm_addr, offset, values)

    # ----- async I/O -----

    async def send_request(self, command: ProtocolCommand) -> Future:
        """Send `command` over DTLS, return a Future with the response.

        Retries up to ``self.retries`` times. Behaviour on retry:
          - On validation failure (response decoded but didn't match the
            command — typically a stale frame from a previous request that
            arrived late), the session is **preserved** and the next attempt
            drains stale buffered data before sending again.
          - On a genuine I/O / SSL exception the session is torn down before
            the next attempt, since it's likely no longer usable.
        """
        loop = asyncio.get_running_loop()
        await self._ensure_lock().acquire()
        try:
            self.command = command
            payload = command.request_bytes()
            for attempt in range(self.retries + 1):
                if attempt > 0:
                    logger.debug("Retry #%d/%d for %s", attempt, self.retries, command)
                try:
                    raw = await loop.run_in_executor(
                        None, self._send_recv_blocking, payload
                    )
                except Exception as err:  # noqa: BLE001 — broad: anything from socket/SSL
                    logger.debug("DTLS send/recv attempt %d failed: %s",
                                 attempt + 1, err)
                    # Real I/O / SSL failure → session may be unusable.
                    await loop.run_in_executor(None, self._close_session)
                    continue

                if command.validator(raw):
                    fut = loop.create_future()
                    # Caller (ProtocolCommand.execute) wraps raw bytes in
                    # ProtocolResponse itself — match the UDP path's contract.
                    fut.set_result(raw)
                    return fut

                # Validation failed → likely a stale leftover from a previous
                # timed-out request. Don't close the session; the drain at the
                # start of the next _send_recv_blocking will discard the rest.
                logger.debug("Response failed validation (stale), retrying on same session.")

            return self._max_retries_reached()
        finally:
            if self._lock and self._lock.locked():
                self._lock.release()
            if not self.keep_alive:
                await loop.run_in_executor(None, self._close_session)

    async def close(self) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._close_session)

    def _close_transport(self) -> None:
        # Sync flavour invoked by base class on errors.
        self._close_session()
        if self.response_future and not self.response_future.done():
            self.response_future.cancel()

    # ----- sync internals (run inside an executor) -----

    def _send_recv_blocking(self, payload: bytes) -> bytes:
        if self._conn is None or self._sock is None:
            self._connect_blocking()
        # Drain any leftover bytes from a previous (timed-out) request — without
        # this they would surface as the response to the new request.
        self._drain_stale()
        self._conn.send(payload)
        deadline = time.monotonic() + self.timeout
        self._flush_outbound(deadline)

        while True:
            try:
                return self._conn.recv(4096)
            except (SSL.WantReadError, SSL.WantWriteError):
                if time.monotonic() >= deadline:
                    raise RequestFailedException(
                        f"No DTLS response within {self.timeout}s", 0
                    )
                self._pump(deadline)

    def _connect_blocking(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect((self._host, self._port))
        sock.setblocking(False)

        ctx = SSL.Context(SSL.DTLS_METHOD)
        ctx.set_verify(SSL.VERIFY_NONE, lambda *_: True)
        ctx.set_cipher_list(self.DEFAULT_CIPHER_LIST)

        conn = SSL.Connection(ctx, None)  # memory BIOs
        conn.set_connect_state()

        # Handshake budget = 5x the per-request timeout, capped at >= 5s.
        deadline = time.monotonic() + max(self.timeout * 5, 5.0)
        self._sock = sock
        self._conn = conn
        while True:
            try:
                conn.do_handshake()
                break
            except (SSL.WantReadError, SSL.WantWriteError):
                self._pump(deadline)
            if time.monotonic() >= deadline:
                self._close_session()
                # The dongle accepts only one concurrent DTLS session in our
                # observation, so a hung handshake is most often another
                # client (e.g. the vendor's mobile app) holding the slot.
                raise RequestFailedException(
                    f"DTLS handshake to {self._host}:{self._port} timed out "
                    "(dongle may already have a client connected)", 0
                )

        logger.debug("DTLS connected to %s:%d cipher=%s proto=%s",
                     self._host, self._port,
                     conn.get_cipher_name(),
                     conn.get_protocol_version_name())

    def _close_session(self) -> None:
        conn, self._conn = self._conn, None
        sock, self._sock = self._sock, None
        if conn is not None:
            try:
                conn.shutdown()
            except Exception:  # noqa: BLE001
                pass
        if sock is not None:
            try:
                sock.close()
            except Exception:  # noqa: BLE001
                pass

    def _drain_stale(self) -> None:
        """Pull any pending bytes off the socket+BIO and discard them."""
        try:
            while True:
                data = self._sock.recv(4096)
                if not data:
                    break
                self._conn.bio_write(data)
        except (BlockingIOError, OSError):
            pass
        while True:
            try:
                stale = self._conn.recv(4096)
                if not stale:
                    break
            except (SSL.WantReadError, SSL.WantWriteError):
                break

    def _flush_outbound(self, deadline: float) -> None:
        while True:
            try:
                out = self._conn.bio_read(4096)
            except SSL.WantReadError:
                return
            if not out:
                return
            self._sock.send(out)
            if time.monotonic() >= deadline:
                return

    def _pump(self, deadline: float) -> None:
        self._flush_outbound(deadline)
        wait = max(0.0, min(0.5, deadline - time.monotonic()))
        rlist, _, _ = select.select([self._sock], [], [], wait)
        if rlist:
            data = self._sock.recv(4096)
            if data:
                self._conn.bio_write(data)
