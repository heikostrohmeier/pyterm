"""
pyterm.serial_worker
====================
Thread-safe serial / TCP transport layer built on a ``QThread``.

Architecture rule
-----------------
**This module is the ONLY place where blocking I/O is allowed.**
The GUI thread must NEVER call ``serial.Serial.read/write`` directly.
All communication with :class:`MainWindow` happens exclusively through
Qt Signals (worker → GUI) and Slots / ``QMetaObject.invokeMethod``
(GUI → worker).

Ported from
-----------
* src/serial.c        – Send_chars(), Config_port(), Close_port(),
                         Set_signals(), lis_sig(), sendbreak(),
                         configure_echo(), configure_crlfauto(),
                         configure_autoreconnect_enable(),
                         configure_esc_clear_screen()
* src/transport.c/.h  – transport_open(), transport_close(),
                         transport_send(), transport_get_fd(),
                         transport_send_break(), transport_get_signals(),
                         transport_set_signal(), transport_get_status_string()
* src/serial.h        – BUFFER_RECEPTION, POLL_DELAY
* src/device_monitor.c– auto-reconnect / port-lost detection
"""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import (
    QMutex,
    QMutexLocker,
    QThread,
    QWaitCondition,
    Signal,
    Slot,
)

from pyterm.config import PortConfig
from pyterm.utils import BUFFER_RECEPTION, POLL_DELAY_MS, TransportType

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SerialWorker
# ---------------------------------------------------------------------------

class SerialWorker(QThread):
    """
    Owns the serial port (or TCP socket) and runs the I/O loop in a
    dedicated thread.

    Signals (worker → GUI)
    ----------------------
    data_received(bytes)
        Raw bytes just read from the port.  The GUI is responsible for
        decoding / buffering / displaying them.

    port_opened(str)
        Emitted after a successful ``open()``.  Carries the human-readable
        status string (mirrors ``transport_get_status_string()``).

    port_closed()
        Emitted after the port is closed (clean close OR unexpected loss).

    port_error(str)
        Non-fatal error message suitable for the status bar.

    control_signals_changed(int)
        Bitmask of current modem-control signals (CTS, DSR, DCD, RI, …).
        Emitted every POLL_DELAY_MS while the port is open.
        Mirrors ``transport_get_signals()`` / ``lis_sig()``.

    Slots (GUI → worker)
    --------------------
    open_port(PortConfig)   – Open / re-open the port with new settings.
    close_port()            – Close the port cleanly.
    send_bytes(bytes)       – Write bytes to the port.
    send_break()            – Transmit a serial break condition.
    set_signal(int)         – Set DTR/RTS control lines.
    apply_config(PortConfig)– Apply new port settings without full close/open.
    """

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    data_received         = Signal(bytes)   # raw RX data chunk
    port_opened           = Signal(str)     # human-readable status string
    port_closed           = Signal()        # port went away
    port_error            = Signal(str)     # non-fatal error text
    control_signals_changed = Signal(int)   # modem-control bitmask

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, parent=None) -> None:
        """
        Initialise the worker.  The port is NOT opened here; call
        :meth:`open_port` after moving the worker to its thread.
        """
        super().__init__(parent)

        # Current port configuration
        self._config: Optional[PortConfig] = None

        # pyserial Serial instance (or socket wrapper in TCP mode)
        # TODO (Junior): import serial at the top of this file once
        #                pyserial is confirmed installed.
        self._port = None   # type: Optional[serial.Serial]

        # Thread-safety primitives
        self._mutex        = QMutex()
        self._write_queue  = bytearray()          # bytes waiting to be sent
        self._write_cond   = QWaitCondition()     # wakes the run() loop

        # State flags (protected by _mutex)
        self._running      = False
        self._stop_request = False

    # ------------------------------------------------------------------
    # QThread.run()  –  the I/O loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """
        Main I/O loop executed in the worker thread.

        Responsibilities
        ----------------
        1. Poll for incoming data (``serial.Serial.read``).
        2. Flush the write queue (data enqueued by :meth:`send_bytes`).
        3. Poll modem-control signals every :data:`POLL_DELAY_MS` ms
           and emit :attr:`control_signals_changed` when they change.
        4. Detect unexpected port loss and emit :attr:`port_closed`
           (auto-reconnect if ``config.autoreconnect`` is True).

        TODO (Junior): Implement this method.
                       Step-by-step reference:
                       a. Loop while not self._stop_request.
                       b. Call self._port.read(BUFFER_RECEPTION) inside
                          a try/except serial.SerialException block.
                       c. If data received, emit self.data_received(data).
                       d. Under self._mutex lock, flush self._write_queue
                          via self._port.write().
                       e. Every POLL_DELAY_MS call self._port.getCTS() etc.
                          and emit self.control_signals_changed().
                       f. On SerialException (port lost), emit port_closed()
                          and optionally reconnect (see src/device_monitor.c).
                       Reference files: src/transport.c, src/serial.c,
                                        src/device_monitor.c
        """
        if self._port is None:
            log.error("run() called but no port is open; exiting I/O loop.")
            return
        log.warning("I/O loop not yet implemented; thread will exit immediately.")

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @Slot(object)
    def open_port(self, config: PortConfig) -> None:
        """
        Open (or re-open) the port described by *config*.

        Behaviour mirrors ``Config_port()`` → ``transport_open()`` in
        src/serial.c and src/transport.c.

        Steps (to be implemented by Junior):
        1. Close any currently open port (call :meth:`close_port` first).
        2. If ``config.transport_type == TransportType.SERIAL``:
               import serial
               self._port = serial.Serial(
                   port     = config.port,
                   baudrate = config.baudrate,
                   bytesize = config.bits,
                   parity   = PARITY_MAP[config.parity],
                   stopbits = config.stopbits,
                   timeout  = 0.1,
                   xonxoff  = (config.flow == 1),
                   rtscts   = (config.flow == 2),
               )
        3. If ``config.transport_type == TransportType.TCP_CLIENT``:
               Use ``socket`` or ``serial.serial_for_url()`` with
               ``socket://host:port``.
        4. If ``config.transport_type == TransportType.TCP_SERVER``:
               Listen on ``config.socket_port`` and accept one connection.
        5. On success, set self._running = True and emit port_opened().
        6. On failure, emit port_error() with the exception message.

        Reference files: src/transport.c  transport_open()
        TODO (Junior): implement
        """
        self._config = config
        # TODO (Junior): implement opening logic.
        log.warning(
            "open_port() not yet implemented; port %s will not be opened.",
            config.port,
        )
        self.port_error.emit(
            f"Cannot open {config.port}: open_port() not yet implemented."
        )

    @Slot()
    def close_port(self) -> None:
        """
        Close the port cleanly.

        Mirrors ``Close_port()`` / ``transport_close()`` in src/serial.c.

        TODO (Junior): implement
                       1. Set self._stop_request = True.
                       2. Wake the write condition so run() exits quickly.
                       3. Call self._port.close() inside try/except.
                       4. Emit self.port_closed().
                       Reference: src/serial.c  Close_port()
        """
        with QMutexLocker(self._mutex):
            self._stop_request = True
        self._write_cond.wakeAll()

        if self._port is not None:
            try:
                self._port.close()
            except Exception as exc:
                log.error("Error closing port: %s", exc)
            finally:
                self._port = None

        self.port_closed.emit()
        log.info("Port closed.")

    @Slot(bytes)
    def send_bytes(self, data: bytes) -> None:
        """
        Enqueue *data* for transmission on the serial port.

        Thread-safe: may be called from the GUI thread at any time.
        Mirrors ``Send_chars()`` / ``transport_send()`` in src/serial.c.

        The run() loop drains ``_write_queue`` on the worker thread so
        the GUI is never blocked.

        TODO (Junior): implement
                       1. Lock self._mutex.
                       2. Append data to self._write_queue.
                       3. Wake self._write_cond.
                       Reference: src/serial.c  Send_chars(),
                                  src/transport.c  transport_send()
        """
        if self._port is None:
            log.warning("send_bytes() called but no port is open; %d bytes dropped.", len(data))
            self.port_error.emit("Cannot send: port is not open.")
            return

        with QMutexLocker(self._mutex):
            self._write_queue.extend(data)
        self._write_cond.wakeAll()

    @Slot()
    def send_break(self) -> None:
        """
        Send a serial BREAK condition.

        Mirrors ``sendbreak()`` / ``transport_send_break()`` in src/serial.c.

        TODO (Junior): Call self._port.send_break() inside try/except.
                       Reference: src/serial.c  sendbreak()
        """
        if self._port is None:
            log.warning("send_break() called but no port is open.")
            self.port_error.emit("Cannot send break: port is not open.")
            return

        try:
            self._port.send_break()
        except Exception as exc:
            log.error("Failed to send break: %s", exc)
            self.port_error.emit(f"Send break failed: {exc}")

    @Slot(int)
    def set_signal(self, signal_mask: int) -> None:
        """
        Set modem-control output lines (DTR / RTS).

        *signal_mask* uses the same bitmask convention as the C function
        ``Set_signals()`` / ``transport_set_signal()`` in src/serial.c.

        TODO (Junior): Decode signal_mask and call
                       self._port.setDTR() / self._port.setRTS().
                       Reference: src/serial.c  Set_signals(),
                                  src/transport.c  transport_set_signal()
        """
        if self._port is None:
            log.warning("set_signal() called but no port is open.")
            self.port_error.emit("Cannot set signal: port is not open.")
            return

        # TODO (Junior): decode signal_mask and call setDTR()/setRTS().
        log.warning("set_signal() bitmask decoding not yet implemented.")

    @Slot(object)
    def apply_config(self, config: PortConfig) -> None:
        """
        Apply updated port settings (baud rate, parity, etc.) to an
        already-open port without a full close/open cycle.

        TODO (Junior): Use self._port.apply_settings() or set individual
                       attributes (self._port.baudrate = ..., etc.).
                       Fall back to close + reopen if the port is not
                       already open.
                       Reference: src/term_config.c  Lis_Config(),
                                  src/serial.c  Config_port()
        """
        self._config = config
        if self._port is None:
            log.warning(
                "apply_config() called but no port is open; "
                "settings will take effect on next open_port()."
            )
            return

        # TODO (Junior): call self._port.apply_settings() or set individual attrs.
        log.warning("apply_config() live-update not yet implemented.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_status_string(self) -> str:
        """
        Return a human-readable connection status string.

        Mirrors ``transport_get_status_string()`` in src/transport.c.

        TODO (Junior): Build a string like
                       "Serial: /dev/ttyS0  115200 8N1 (RTS/CTS)"
                       or "TCP Client: 192.168.1.1:2323 [connected]"
                       Reference: src/transport.c  transport_get_status_string()
        """
        # TODO (Junior): implement
        if self._config is None:
            return "Not configured"
        return f"Port: {self._config.port}"

    def _poll_control_signals(self) -> int:
        """
        Read current modem-control input lines and return a bitmask.

        Mirrors ``lis_sig()`` / ``transport_get_signals()`` in src/serial.c.

        TODO (Junior): Read self._port.getCTS(), getDSR(), getCD(), getRI()
                       and pack into a bitmask.
                       Reference: src/serial.c  lis_sig(),
                                  src/transport.c  transport_get_signals()
        """
        if self._port is None:
            return 0

        try:
            mask = 0
            # TODO (Junior): read self._port.getCTS() etc. and pack into bitmask.
            return mask
        except Exception as exc:
            log.error("Failed to read control signals: %s", exc)
            return 0
