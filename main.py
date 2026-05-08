#!/usr/bin/env python3
"""
pyterm – entry point
====================
Launches the PySide6 application.

High-DPI scaling is configured BEFORE QApplication is instantiated, as
required by Qt6.  This mirrors the Qt6 best-practice for crisp rendering on
HiDPI / Retina displays.

Ported from
-----------
* src/gtkterm.c  – main(), gtk_init(), command-line argument parsing
* src/cmdline.c  – command-line option handling
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from pyterm.config import load_config, hard_default_config
from pyterm.main_window import MainWindow


# ---------------------------------------------------------------------------
# High-DPI policy – must be set before QApplication()
# Qt6 doc: QApplication::setHighDpiScaleFactorRoundingPolicy
# ---------------------------------------------------------------------------
QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)


def parse_args(app: QApplication) -> dict:
    """
    Parse command-line arguments.

    Mirrors ``cmdline_get_options()`` / the GOptionEntry table in
    src/cmdline.c.  Returns a dict that overrides the loaded configuration.

    TODO (Junior): Implement using ``argparse``.
                   Expose the following flags (reference: src/cmdline.c):
                   --port  (-p)  : serial device path
                   --baud  (-s)  : baud rate
                   --bits  (-b)  : data bits
                   --parity (-a) : parity (none / odd / even)
                   --stopbits(-t): stop bits
                   --flow  (-f)  : flow control
                   --echo  (-e)  : local echo
                   --noportlock  : disable port lock
                   --config      : load named config section
                   Reference: src/cmdline.c  cmdline_get_options()
    """
    # TODO (Junior): implement with argparse
    return {}


def apply_cli_overrides(cfg, overrides: dict):
    """
    Merge *overrides* (from command-line arguments) into *cfg*.

    TODO (Junior): for each key in overrides that is not None, set the
                   corresponding attribute on cfg.port or cfg.display.
                   Reference: src/cmdline.c, src/term_config.c
                               Verify_configuration().
    """
    # TODO (Junior): implement
    return cfg


def main() -> int:
    """
    Application entry point.

    Execution order mirrors src/gtkterm.c  main():
    1. Create QApplication.
    2. Parse command-line arguments.
    3. Load configuration from file (fall back to hard defaults on error).
    4. Apply CLI overrides.
    5. Create and show the main window.
    6. Start the Qt event loop.

    Returns the exit code from QApplication.exec().
    """
    app = QApplication(sys.argv)
    app.setApplicationName("pyterm")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("pyterm")

    # --- Load configuration ---
    # TODO (Junior): wire parse_args() result to apply_cli_overrides().
    #               Reference: src/gtkterm.c  main(),
    #                          src/term_config.c  config_file_init(),
    #                          Load_configuration_from_file().
    overrides = parse_args(app)

    try:
        cfg = load_config()
        if cfg is None:
            # load_config() returns None when not yet implemented (stub)
            cfg = hard_default_config()
    except Exception as exc:
        # Graceful fallback to hard defaults on any config-load error.
        # This mirrors Hard_default_configuration() in term_config.c.
        print(f"[pyterm] Warning: could not load config ({exc}); using defaults.")
        cfg = hard_default_config()

    cfg = apply_cli_overrides(cfg, overrides)

    # --- Create main window ---
    window = MainWindow(cfg)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
