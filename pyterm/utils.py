"""
pyterm.utils
============
Shared, application-wide constants and pure helper functions.

Ported from
-----------
* src/baudrates.c / src/baudrates.h  – baud-rate list
* src/serial.h                       – BUFFER_RECEPTION, BUFFER_EMISSION,
                                       LINE_FEED, POLL_DELAY
* src/transport.h                    – transport-type enum
* src/interface.h                    – ASCII_VIEW / HEXADECIMAL_VIEW
* src/term_config.h                  – DEFAULT_* constants, parity / flow maps
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Transport types  (src/transport.h)
# ---------------------------------------------------------------------------

class TransportType:
    """Integer constants mirroring the anonymous C enum in transport.h."""
    SERIAL     = 0
    TCP_CLIENT = 1
    TCP_SERVER = 2


# ---------------------------------------------------------------------------
# View modes  (src/interface.h)
# ---------------------------------------------------------------------------

class ViewMode:
    """Terminal display modes."""
    ASCII       = 0   # MSG_ASCII / ASCII_VIEW
    HEXADECIMAL = 1   # HEXADECIMAL_VIEW


# ---------------------------------------------------------------------------
# Message severity  (src/interface.h)
# ---------------------------------------------------------------------------

class MsgSeverity:
    WARNING = 0   # MSG_WRN
    ERROR   = 1   # MSG_ERR


# ---------------------------------------------------------------------------
# Serial buffer sizes  (src/serial.h)
# ---------------------------------------------------------------------------

BUFFER_RECEPTION = 8192    # bytes; read() chunk size for the serial thread
BUFFER_EMISSION  = 4096    # bytes; write() buffer size
LINE_FEED        = 0x0A    # ASCII LF
POLL_DELAY_MS    = 100     # ms; control-signal polling interval

# Ring buffer for received data   (src/buffer.h  BUFFER_SIZE)
DISPLAY_BUFFER_SIZE = 128 * 1024   # 128 KiB


# ---------------------------------------------------------------------------
# Default port configuration  (src/term_config.h  DEFAULT_*)
# ---------------------------------------------------------------------------

DEFAULT_PORT     = "/dev/ttyS0"
DEFAULT_BAUDRATE = 115200
DEFAULT_PARITY   = 0      # none
DEFAULT_BITS     = 8
DEFAULT_STOPBITS = 1
DEFAULT_FLOW     = 0      # none
DEFAULT_DELAY    = 0      # ms, end-of-line delay for ASCII file transfer
DEFAULT_CHAR     = -1     # wait-for-char disabled


# ---------------------------------------------------------------------------
# Default display / terminal configuration  (src/term_config.h)
# ---------------------------------------------------------------------------

DEFAULT_FONT       = "Monospace 12"
DEFAULT_SCROLLBACK = 10_000   # lines
DEFAULT_ROWS       = 24
DEFAULT_COLUMNS    = 80


# ---------------------------------------------------------------------------
# Standard baud-rate list  (src/baudrates.c / src/baudrates.h)
#
# TODO (Junior): Keep this list in sync with baudrates.h.
#       Look at  src/baudrates.h  for the authoritative sorted list of
#       { baud, speed_t } pairs and expand / trim the tuple list below.
#       Each entry is (baud_integer,).  pyserial accepts the integer directly.
# ---------------------------------------------------------------------------

STANDARD_BAUDRATES: list[int] = [
    50, 75, 110, 134, 150, 200, 300, 600, 1200, 1800, 2400, 4800,
    9600, 19200, 38400, 57600, 115200, 230400, 460800, 500000,
    576000, 921600, 1000000, 1152000, 1500000, 2000000, 2500000,
    3000000, 3500000, 4000000,
]


# ---------------------------------------------------------------------------
# Parity mapping  (src/term_config.c  Lis_Config() switch-case)
#
# C encoding: 0 = none, 1 = odd, 2 = even
# pyserial   : serial.PARITY_NONE / ODD / EVEN
# ---------------------------------------------------------------------------

# TODO (Junior): Import serial (pyserial) and replace the string literals
#               with the proper serial.PARITY_* constants.
#               Reference: src/term_config.c  Lis_Config() parity block.
PARITY_MAP: dict[int, str] = {
    0: "N",   # serial.PARITY_NONE
    1: "O",   # serial.PARITY_ODD
    2: "E",   # serial.PARITY_EVEN
}

PARITY_LABELS: dict[int, str] = {
    0: "None",
    1: "Odd",
    2: "Even",
}


# ---------------------------------------------------------------------------
# Flow-control mapping  (src/term_config.c  Lis_Config() flow block)
#
# C encoding: 0 = none, 1 = Xon/Xoff, 2 = RTS/CTS, 3 = RS-485 half-duplex
# ---------------------------------------------------------------------------

FLOW_LABELS: dict[int, str] = {
    0: "None",
    1: "Xon/Xoff",
    2: "RTS/CTS",
    3: "RS-485 Half-Duplex (RTS)",
}


# ---------------------------------------------------------------------------
# Helper: validate baud rate
# ---------------------------------------------------------------------------

def is_standard_baudrate(baud: int) -> bool:
    """Return True when *baud* is in the standard list."""
    # TODO (Junior): no logic needed here beyond the membership test.
    return baud in STANDARD_BAUDRATES
