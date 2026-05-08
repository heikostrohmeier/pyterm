"""
pyterm.config
=============
Dataclasses that mirror the C configuration structs from term_config.h,
plus load/save logic for the INI-style configuration file.

Ported from
-----------
* src/term_config.h   – struct configuration_port, display_config_t, DEFAULT_*
* src/term_config.c   – config_file_init(), Save_config_file(),
                         Load_configuration_from_file(), Copy_configuration()
* src/parsecfg.c/.h   – INI parser (replaced by Python's configparser)
"""

from __future__ import annotations

import configparser
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from pyterm.utils import (
    DEFAULT_BAUDRATE, DEFAULT_BITS, DEFAULT_CHAR, DEFAULT_COLUMNS,
    DEFAULT_DELAY, DEFAULT_FLOW, DEFAULT_FONT, DEFAULT_PARITY,
    DEFAULT_PORT, DEFAULT_ROWS, DEFAULT_SCROLLBACK, DEFAULT_STOPBITS,
    TransportType,
)

# ---------------------------------------------------------------------------
# Configuration filename  (src/term_config.c  CONFIGURATION_FILENAME)
# ---------------------------------------------------------------------------

CONFIG_FILENAME = "pytermrc"


# ---------------------------------------------------------------------------
# Port / transport configuration  (src/term_config.h  struct configuration_port)
# ---------------------------------------------------------------------------

@dataclass
class PortConfig:
    """
    Serial-port and transport configuration.

    Mirrors the C struct ``configuration_port`` from src/term_config.h.

    Fields
    ------
    port               : Device path, e.g. ``/dev/ttyS0``  (config.port)
    transport_type     : One of TransportType.SERIAL / TCP_CLIENT / TCP_SERVER
    socket_host        : TCP host when transport_type != SERIAL
    socket_port        : TCP port string when transport_type != SERIAL
    baudrate           : Baud rate (config.vitesse)
    bits               : Data bits 5-8 (config.bits)
    stopbits           : Stop bits 1 or 2 (config.stops)
    parity             : 0=None, 1=Odd, 2=Even (config.parite)
    flow               : 0=None, 1=Xon/Xoff, 2=RTS/CTS, 3=RS485 (config.flux)
    delay_ms           : End-of-line delay in ms for ASCII file transfer (config.delai)
    wait_char          : Wait-for-char ASCII code, -1 = disabled (config.car)
    rs485_rts_before   : RTS-on time before TX in ms (config.rs485_rts_time_before_transmit)
    rs485_rts_after    : RTS-on time after  TX in ms (config.rs485_rts_time_after_transmit)
    echo               : Local echo enabled (config.echo)
    crlfauto           : Automatic CR+LF on LF (config.crlfauto)
    autoreconnect      : Auto-reconnect on port loss (config.autoreconnect_enabled)
    esc_clear_screen   : Clear screen on ESC 0x1B (config.esc_clear_screen)
    timestamp          : Prepend timestamp to each line (config.timestamp)
    disable_port_lock  : Skip port-lock file (config.disable_port_lock)
    """

    port:             str  = DEFAULT_PORT
    transport_type:   int  = TransportType.SERIAL
    socket_host:      str  = "localhost"
    socket_port:      str  = "2323"
    baudrate:         int  = DEFAULT_BAUDRATE
    bits:             int  = DEFAULT_BITS
    stopbits:         int  = DEFAULT_STOPBITS
    parity:           int  = DEFAULT_PARITY
    flow:             int  = DEFAULT_FLOW
    delay_ms:         int  = DEFAULT_DELAY
    wait_char:        int  = DEFAULT_CHAR
    rs485_rts_before: int  = 30
    rs485_rts_after:  int  = 30
    echo:             bool = False
    crlfauto:         bool = False
    autoreconnect:    bool = False
    esc_clear_screen: bool = False
    timestamp:        bool = False
    disable_port_lock:bool = False


# ---------------------------------------------------------------------------
# Display / terminal configuration  (src/term_config.h  display_config_t)
# ---------------------------------------------------------------------------

@dataclass
class DisplayConfig:
    """
    VTE-terminal / display configuration.

    Mirrors the C typedef ``display_config_t`` from src/term_config.h.

    Fields
    ------
    font              : Pango font description string (term_conf.font)
    rows              : Terminal rows (term_conf.rows)
    columns           : Terminal columns (term_conf.columns)
    scrollback        : Scrollback lines (term_conf.scrollback)
    block_cursor      : Use block cursor (term_conf.block_cursor)
    visual_bell       : Flash instead of beep (term_conf.visual_bell)
    foreground_color  : RGBA tuple 0.0-1.0 (term_conf.foreground_color)
    background_color  : RGBA tuple 0.0-1.0 (term_conf.background_color)
    """

    font:             str              = DEFAULT_FONT
    rows:             int              = DEFAULT_ROWS
    columns:          int              = DEFAULT_COLUMNS
    scrollback:       int              = DEFAULT_SCROLLBACK
    block_cursor:     bool             = False
    visual_bell:      bool             = False
    # (r, g, b, a) each 0.0 – 1.0  (DEFAULT_FOREGROUNDCOLOR / DEFAULT_BACKGROUNDCOLOR)
    foreground_color: tuple            = field(default_factory=lambda: (0.0, 0.0, 0.0, 1.0))
    background_color: tuple            = field(default_factory=lambda: (1.0, 1.0, 1.0, 1.0))


# ---------------------------------------------------------------------------
# Macro definition  (src/macros.h  macro_t)
# ---------------------------------------------------------------------------

@dataclass
class MacroConfig:
    """
    A single user-defined macro / shortcut.

    Mirrors the C struct ``macro_t`` from src/macros.h.

    Fields
    ------
    label       : Button label shown in the macro panel
    shortcut    : Keyboard shortcut string (e.g. ``<Ctrl>F1``)
    action      : Byte string to send; may contain printf-style format specs
    tab         : Panel tab group name
    args        : Saved argument values for parameterised macros
    polling_enabled   : Whether periodic polling is active
    polling_period_ms : Polling interval in ms
    """

    label:             str             = ""
    shortcut:          str             = ""
    action:            str             = ""
    tab:               str             = "General"
    args:              list[str]       = field(default_factory=list)
    polling_enabled:   bool            = False
    polling_period_ms: int             = 1000


# ---------------------------------------------------------------------------
# Top-level application settings container
# ---------------------------------------------------------------------------

@dataclass
class AppConfig:
    """
    Aggregates all configuration objects into one object that can be
    passed around the application.
    """

    port:     PortConfig    = field(default_factory=PortConfig)
    display:  DisplayConfig = field(default_factory=DisplayConfig)
    macros:   list[MacroConfig] = field(default_factory=list)
    # Active config section name (mirrors active_config_name in term_config.c)
    active_section: str     = "default"


# ---------------------------------------------------------------------------
# Config-file path helpers  (src/term_config.c  config_file_init())
# ---------------------------------------------------------------------------

def get_config_path() -> Path:
    """
    Return the path to the configuration file.

    Logic mirrors ``config_file_init()`` in src/term_config.c:
    - New location : $XDG_CONFIG_HOME/pytermrc
    - Legacy migration from old ``$HOME/.gtktermrc`` is intentionally NOT
      handled here; that is a one-time migration task (see MIGRATION_TODO.md).

    TODO (Junior): Optionally add migration from $HOME/.gtktermrc if the
                   new path does not exist.  Reference: src/term_config.c
                   config_file_init().
    """
    xdg_config = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(xdg_config) / CONFIG_FILENAME


# ---------------------------------------------------------------------------
# Load  (src/term_config.c  Load_configuration_from_file(), cfgParse())
# ---------------------------------------------------------------------------

def load_config(section: str = "default", path: Optional[Path] = None) -> AppConfig:
    """
    Load configuration from *path* (defaults to ``get_config_path()``).

    Returns a fully populated :class:`AppConfig`; falls back to hard-coded
    defaults when the file or section is absent.

    TODO (Junior): Implement the full INI parsing.
                   - Use ``configparser.ConfigParser``.
                   - Map each INI key to the corresponding dataclass field.
                   - Reference: src/term_config.c cfg[] array (lines ~100-137)
                     for the authoritative list of key names and types.
                   - Handle the legacy ``show_rxtx`` key by ignoring it
                     (backward compat – see the C comment in cfg[]).
    """
    # TODO (Junior): implement – stub returns hard defaults
    pass


# ---------------------------------------------------------------------------
# Save  (src/term_config.c  Save_config_file(), Copy_configuration(),
#         save_config_silent(), cfgDump())
# ---------------------------------------------------------------------------

def save_config(cfg: AppConfig, section: str = "default",
                path: Optional[Path] = None) -> None:
    """
    Persist *cfg* to *path* under *section*.

    TODO (Junior): Implement.
                   - Use ``configparser.ConfigParser``.
                   - Mirror the key names from the C cfg[] array.
                   - Convert booleans to ``0``/``1`` strings for compatibility
                     with the existing ``.gtktermrc`` format.
                   - Reference: src/term_config.c Copy_configuration(),
                     cfgDump(), save_config_silent().
    """
    # TODO (Junior): implement
    pass


# ---------------------------------------------------------------------------
# Hard defaults  (src/term_config.c  Hard_default_configuration())
# ---------------------------------------------------------------------------

def hard_default_config() -> AppConfig:
    """
    Return a fresh :class:`AppConfig` populated entirely from the compile-time
    defaults defined in ``utils.py``.

    Equivalent to ``Hard_default_configuration()`` in src/term_config.c.
    """
    return AppConfig()
