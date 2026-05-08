"""
pyterm – A Python/PySide6 rewrite of gtkTerm.

Package structure
-----------------
pyterm/
  __init__.py       – This file; package metadata.
  config.py         – Dataclasses that mirror the C structs (configuration_port,
                       display_config_t) and INI-file persistence.
  utils.py          – Shared constants: baud-rate table, parity map, flow-control
                       map, transport types.
  serial_worker.py  – QThread subclass that owns the pyserial port.  All blocking
                       I/O happens here; it communicates with the GUI exclusively
                       through Qt Signals/Slots.
  main_window.py    – QMainWindow subclass: toolbar, terminal view, hex view,
                       macro panel, status bar.  Zero blocking calls allowed.
"""

__version__ = "0.1.0"
__author__  = "pyterm contributors"
