"""
pyterm.main_window
==================
Main application window.

Architecture rules
------------------
* Zero blocking calls in this class – all I/O goes through SerialWorker.
* All worker interactions happen via Qt Signals/Slots only.
* UI state is driven by signals emitted by SerialWorker.

Ported from
-----------
* src/interface.c / src/interface.h  – create_main_window(), set_view(),
                                        put_text(), put_hexadecimal(),
                                        Set_status_message(), show_message(),
                                        clear_display(), Set_local_echo(),
                                        Set_crlfauto(), Set_timestamp(),
                                        send_serial(), rebuild_macro_buttons(),
                                        Set_window_title(),
                                        toggle_logging_pause_resume(),
                                        toggle_logging_sensitivity(),
                                        control_signals_read() (signal LEDs)
* src/term_config.c                  – Config_Port_Fenetre() (port config dialog)
                                        Config_Terminal() (terminal display dialog)
                                        select_config_callback(),
                                        save_config_callback(),
                                        delete_config_callback()
* src/files.c / src/files.h          – ASCII file send / receive
* src/logging.c / src/logging.h      – logging_start(), logging_stop(),
                                        logging_pause_resume()
* src/search.c / src/search.h        – search bar
* src/macros.c / src/macros.h        – rebuild_macro_buttons(), macro panel
"""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QColor, QFont, QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QDockWidget,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QToolBar,
    QWidget,
)

from pyterm.config import AppConfig, PortConfig
from pyterm.serial_worker import SerialWorker
from pyterm.utils import ViewMode, MsgSeverity, POLL_DELAY_MS

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    The application's single main window.

    Responsibilities
    ----------------
    * Host the terminal output widget (ASCII and hex views).
    * Host the macro panel (dock widget).
    * Host the hex-send bar.
    * Manage the toolbar and menu bar.
    * Display port status in the status bar and signal-line LEDs.
    * Own the :class:`SerialWorker` instance (moves it to a QThread).

    All blocking work is delegated to :class:`SerialWorker` via signals.
    """

    def __init__(self, app_config: AppConfig, parent: Optional[QWidget] = None) -> None:
        """
        Initialise the main window.

        Parameters
        ----------
        app_config:
            Pre-loaded application configuration (port settings, display
            settings, macros).  Produced by :func:`pyterm.config.load_config`.
        """
        super().__init__(parent)

        self._config: AppConfig = app_config
        self._view_mode: int    = ViewMode.ASCII
        self._echo_on:   bool   = app_config.port.echo
        self._crlfauto:  bool   = app_config.port.crlfauto
        self._timestamp: bool   = app_config.port.timestamp

        # --- Build UI skeleton ---
        self._setup_window_title()
        self._setup_central_widget()
        self._setup_toolbar()
        self._setup_menubar()
        self._setup_statusbar()
        self._setup_macro_dock()
        self._setup_hex_send_bar()

        # --- Create the serial worker ---
        self._worker = SerialWorker()
        self._worker.moveToThread(self._worker)  # Worker runs in its own thread
        self._connect_worker_signals()

        # --- Control-signal polling timer (mirrors POLL_DELAY in serial.h) ---
        self._signal_poll_timer = QTimer(self)
        self._signal_poll_timer.setInterval(POLL_DELAY_MS)
        # TODO (Junior): connect _signal_poll_timer.timeout to a slot that
        #                reads the latest control_signals_changed value and
        #                updates the LED indicators in the status bar.

        # --- Apply initial config to the UI ---
        self._apply_config_to_ui()

    # ------------------------------------------------------------------
    # Window / central widget
    # ------------------------------------------------------------------

    def _setup_window_title(self) -> None:
        """
        Set the initial window title.

        Mirrors ``Set_window_title()`` in src/interface.c.

        TODO (Junior): Format the title as "pyterm – <port> <baud> <params>"
                       once a port is open.  Reference: src/interface.c
                       Set_window_title().
        """
        self.setWindowTitle("pyterm")

    def _setup_central_widget(self) -> None:
        """
        Build the central area: a QSplitter that holds the terminal view
        (top) and the optional hex-send bar (bottom).

        Mirrors the GTK packing in ``create_main_window()`` in
        src/interface.c.

        TODO (Junior): Create the actual terminal widget here.
                       Recommended widget: QPlainTextEdit with a monospace
                       font and read-only flag cleared so key events
                       propagate.  Later the ANSI-escape handling can be
                       added by subclassing QPlainTextEdit.
                       Reference: src/interface.c  create_main_window()
                                  (VTE terminal setup section).
        """
        # Placeholder terminal output area
        self._terminal_view = QPlainTextEdit(self)
        self._terminal_view.setReadOnly(True)
        self._terminal_view.setFont(QFont(self._config.display.font))
        self._terminal_view.setObjectName("terminalView")

        # TODO (Junior): replace QPlainTextEdit with a proper ANSI-aware
        #                terminal widget and wire keyPressEvent → send_bytes.

        self.setCentralWidget(self._terminal_view)

    # ------------------------------------------------------------------
    # Toolbar  (src/interface.c  create_actions_and_menu())
    # ------------------------------------------------------------------

    def _setup_toolbar(self) -> None:
        """
        Build the main toolbar.

        TODO (Junior): Add the following actions (use QAction with icons):
            - Open / Close port  (signals_open_port / signals_close_port)
            - Clear display      (clear_display)
            - ASCII view toggle  (set_view ASCII_VIEW)
            - Hex view toggle    (set_view HEXADECIMAL_VIEW)
            - Local echo toggle  (echo_toggled_callback)
            - CR+LF auto toggle  (CR_LF_auto_toggled_callback)
            - Send break         (signals_send_break_callback)
            - Toggle DTR         (signals_toggle_DTR_callback)
            - Toggle RTS         (signals_toggle_RTS_callback)
        Reference: src/interface.c  create_actions_and_menu()
        """
        self._toolbar = QToolBar("Main Toolbar", self)
        self._toolbar.setObjectName("mainToolbar")
        self.addToolBar(self._toolbar)

        # --- Placeholder actions (Junior: replace with real implementations) ---

        # TODO (Junior): implement action: Open Port
        self._action_open_port = QAction("Open Port", self)
        self._action_open_port.setObjectName("actionOpenPort")
        # self._action_open_port.triggered.connect(self._on_open_port)
        self._toolbar.addAction(self._action_open_port)

        # TODO (Junior): implement action: Close Port
        self._action_close_port = QAction("Close Port", self)
        self._action_close_port.setObjectName("actionClosePort")
        # self._action_close_port.triggered.connect(self._on_close_port)
        self._toolbar.addAction(self._action_close_port)

        self._toolbar.addSeparator()

        # TODO (Junior): implement action: Clear Display
        self._action_clear = QAction("Clear", self)
        self._action_clear.setObjectName("actionClear")
        # self._action_clear.triggered.connect(self._on_clear_display)
        self._toolbar.addAction(self._action_clear)

        self._toolbar.addSeparator()

        # TODO (Junior): implement checkable action: ASCII View
        self._action_ascii_view = QAction("ASCII", self)
        self._action_ascii_view.setObjectName("actionAsciiView")
        self._action_ascii_view.setCheckable(True)
        self._action_ascii_view.setChecked(True)
        self._toolbar.addAction(self._action_ascii_view)

        # TODO (Junior): implement checkable action: Hex View
        self._action_hex_view = QAction("Hex", self)
        self._action_hex_view.setObjectName("actionHexView")
        self._action_hex_view.setCheckable(True)
        self._toolbar.addAction(self._action_hex_view)

        self._toolbar.addSeparator()

        # TODO (Junior): implement checkable action: Local Echo
        self._action_echo = QAction("Echo", self)
        self._action_echo.setObjectName("actionEcho")
        self._action_echo.setCheckable(True)
        self._action_echo.setChecked(self._echo_on)
        self._toolbar.addAction(self._action_echo)

        # TODO (Junior): implement checkable action: CR+LF Auto
        self._action_crlfauto = QAction("CR+LF", self)
        self._action_crlfauto.setObjectName("actionCrlfAuto")
        self._action_crlfauto.setCheckable(True)
        self._action_crlfauto.setChecked(self._crlfauto)
        self._toolbar.addAction(self._action_crlfauto)

    # ------------------------------------------------------------------
    # Menu bar  (src/interface.c  create_actions_and_menu())
    # ------------------------------------------------------------------

    def _setup_menubar(self) -> None:
        """
        Build the menu bar with File, Edit, View, Settings, Log, and Help menus.

        TODO (Junior): Populate each menu.  Use the action list from
                       src/interface.c  create_actions_and_menu() as the
                       authoritative reference for which items exist and
                       in which menu they appear.

        Menus to create
        ---------------
        File
            Open/Close port, Send ASCII file, Exit
        Edit
            Copy, Paste, Select All, Find, Clear scrollback
        View
            ASCII view, Hex view (with chars-per-line sub-items),
            Show index, Send hex bar, Macro panel
        Settings
            Port configuration (Config_Port_Fenetre),
            Terminal settings (Config_Terminal),
            Load/Save/Delete named config, Load/Save macro file
        Log
            Log to file, Pause/Resume, Stop, Clear log
        Signals
            Send Break, Toggle DTR, Toggle RTS
        Help
            About
        """
        mb = self.menuBar()

        # File menu
        menu_file = mb.addMenu("&File")
        # TODO (Junior): add actions to menu_file

        # Edit menu
        menu_edit = mb.addMenu("&Edit")
        # TODO (Junior): add actions to menu_edit

        # View menu
        menu_view = mb.addMenu("&View")
        # TODO (Junior): add actions to menu_view

        # Settings menu
        menu_settings = mb.addMenu("&Settings")
        # TODO (Junior): add actions to menu_settings

        # Log menu
        menu_log = mb.addMenu("&Log")
        # TODO (Junior): add actions to menu_log

        # Signals menu
        menu_signals = mb.addMenu("Si&gnals")
        # TODO (Junior): add actions to menu_signals

        # Help menu
        menu_help = mb.addMenu("&Help")
        # TODO (Junior): add About action to menu_help

    # ------------------------------------------------------------------
    # Status bar  (src/interface.h  Set_status_message(), signal LEDs)
    # ------------------------------------------------------------------

    def _setup_statusbar(self) -> None:
        """
        Build the status bar.

        Contains:
        - A text label for port status / messages (Set_status_message).
        - Six LED-style QLabel widgets for modem-control signal lines:
          CTS, DSR, DCD, RI, DTR, RTS.

        Mirrors the GTK status-bar + signal widgets in src/interface.c.

        TODO (Junior): Replace the plain QLabel LEDs with small coloured
                       QFrame or custom widgets that can be toggled green/grey
                       based on the bitmask from SerialWorker.control_signals_changed.
                       Reference: src/interface.c  control_signals_read(),
                                  the GtkWidget *signals[6] array.
        """
        self._statusbar = self.statusBar()

        # Port status label
        self._status_label = QLabel("No port open")
        self._statusbar.addWidget(self._status_label, stretch=1)

        # Modem-control signal LEDs  (mirrors signals[6] in interface.c)
        self._signal_labels: dict[str, QLabel] = {}
        for name in ("CTS", "DSR", "DCD", "RI", "DTR", "RTS"):
            lbl = QLabel(name)
            lbl.setObjectName(f"led_{name}")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setMinimumWidth(36)
            # TODO (Junior): style with QSS – grey = inactive, green = active
            self._signal_labels[name] = lbl
            self._statusbar.addPermanentWidget(lbl)

    # ------------------------------------------------------------------
    # Macro dock panel  (src/interface.c  create_macro_panel(),
    #                    rebuild_macro_buttons())
    # ------------------------------------------------------------------

    def _setup_macro_dock(self) -> None:
        """
        Create the macro panel as a QDockWidget on the right side.

        Mirrors the macro_panel / macro_notebook / macro_tab_flowbox
        construction in src/interface.c  create_macro_panel().

        TODO (Junior): Implement rebuild_macro_buttons() equivalent.
                       - Iterate self._config.macros.
                       - Group macros by MacroConfig.tab.
                       - Create a QTabWidget; one tab per group.
                       - Each macro becomes a QPushButton.
                       - Right-click on a button → polling context menu
                         (mirrors on_macro_button_right_click() in interface.c).
                       Reference: src/interface.c  rebuild_macro_buttons()
                                  (lines ~799 onwards).
        """
        self._macro_dock = QDockWidget("Macros", self)
        self._macro_dock.setObjectName("macroDock")
        self._macro_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )

        # Placeholder – Junior will replace with the real macro panel widget
        placeholder = QLabel("Macro panel – not yet implemented")
        placeholder.setAlignment(Qt.AlignCenter)
        self._macro_dock.setWidget(placeholder)

        self.addDockWidget(Qt.RightDockWidgetArea, self._macro_dock)
        self._macro_dock.hide()   # hidden by default, shown via View menu

    # ------------------------------------------------------------------
    # Hex-send bar  (src/interface.c  Send_Hexadecimal(), Hex_Box)
    # ------------------------------------------------------------------

    def _setup_hex_send_bar(self) -> None:
        """
        Create the hex-input send bar (the "Hex_Box" in interface.c).

        The bar sits below the terminal view and is hidden by default;
        the View → "Send hex bar" menu item toggles its visibility.

        TODO (Junior): Build a QWidget containing:
                       - A QLineEdit for hex input with history navigation
                         (up/down arrows – mirrors the hex_history GList).
                       - A "Send" QPushButton.
                       - Connect to SerialWorker.send_bytes via the hex parser.
                       Reference: src/interface.c  Send_Hexadecimal(),
                                  Hex_Box, hex_history, on_key_press().
        """
        # TODO (Junior): implement as a proper QWidget sub-layout
        self._hex_bar_visible = False   # toggled by View menu action

    # ------------------------------------------------------------------
    # Worker signal connections
    # ------------------------------------------------------------------

    def _connect_worker_signals(self) -> None:
        """
        Wire SerialWorker signals to MainWindow slots.

        TODO (Junior): Connect all signals listed in SerialWorker's class
                       docstring to their corresponding handler methods below.
        """
        self._worker.data_received.connect(self._on_data_received)
        self._worker.port_opened.connect(self._on_port_opened)
        self._worker.port_closed.connect(self._on_port_closed)
        self._worker.port_error.connect(self._on_port_error)
        self._worker.control_signals_changed.connect(self._on_control_signals_changed)

    # ------------------------------------------------------------------
    # Slots – Worker events
    # ------------------------------------------------------------------

    @Slot(bytes)
    def _on_data_received(self, data: bytes) -> None:
        """
        Called in the GUI thread whenever the worker receives data.

        In ASCII mode  : delegate to :meth:`_put_text`.
        In hex mode    : delegate to :meth:`_put_hexadecimal`.

        TODO (Junior): Implement ASCII and hex rendering.
                       - ASCII: feed bytes into a scrollback buffer,
                         append to self._terminal_view, handle echo,
                         crlfauto, timestamp, esc_clear_screen flags.
                         Reference: src/interface.c  put_text(),
                                    Got_Input() callback.
                       - Hex:   format bytes into 16-column hex+ASCII dump
                         (optionally with address index).
                         Reference: src/interface.c  put_hexadecimal(),
                                    bytes_per_line, show_index,
                                    virt_col_pos.
                       - Log received data if logging is active:
                         Reference: src/logging.c  log_chars().
        """
        # TODO (Junior): implement
        pass

    @Slot(str)
    def _on_port_opened(self, status: str) -> None:
        """
        Update the UI when the port opens successfully.

        Mirrors Set_status_message() + Set_window_title() in interface.c.

        TODO (Junior): implement
                       1. Set self._status_label.setText(status).
                       2. Set window title.
                       3. Enable port-dependent menu/toolbar actions.
                       4. Start self._signal_poll_timer.
                       Reference: src/interface.c  interface_open_port(),
                                  Set_status_message(), Set_window_title().
        """
        # TODO (Junior): implement
        self._status_label.setText(status)

    @Slot()
    def _on_port_closed(self) -> None:
        """
        Update the UI when the port closes (clean or lost).

        TODO (Junior): implement
                       1. Stop self._signal_poll_timer.
                       2. Update status label.
                       3. Grey out port-dependent actions.
                       4. Reset LED indicators to inactive.
                       Reference: src/interface.c  interface_close_port().
        """
        # TODO (Junior): implement
        self._status_label.setText("Port closed")

    @Slot(str)
    def _on_port_error(self, message: str) -> None:
        """
        Display a non-fatal error in the status bar.

        Mirrors ``show_message(message, MSG_ERR)`` in src/interface.c.

        TODO (Junior): Optionally show a QMessageBox for critical errors.
                       Reference: src/interface.c  show_message().
        """
        log.error("Port error: %s", message)
        self._status_label.setText(f"Error: {message}")

    @Slot(int)
    def _on_control_signals_changed(self, mask: int) -> None:
        """
        Update the modem-control signal LEDs in the status bar.

        *mask* bit layout mirrors ``transport_get_signals()`` in
        src/transport.c / src/serial.c  lis_sig().

        TODO (Junior): Decode *mask* bits and toggle the LED colours:
                       green = active, grey = inactive.
                       Bit positions must match those used in
                       src/transport.c  transport_get_signals().
                       Reference: src/interface.c  control_signals_read(),
                                  the signals[6] array.
        """
        # TODO (Junior): implement
        pass

    # ------------------------------------------------------------------
    # Slots – User actions (stubs for Junior to implement)
    # ------------------------------------------------------------------

    @Slot()
    def _on_open_port(self) -> None:
        """
        Open the port using the current configuration.

        TODO (Junior): Call self._worker.open_port(self._config.port)
                       via QMetaObject.invokeMethod or a direct signal.
                       Reference: src/interface.c  interface_open_port(),
                                  signals_open_port().
        """
        # TODO (Junior): implement
        pass

    @Slot()
    def _on_close_port(self) -> None:
        """
        Close the port.

        TODO (Junior): Call self._worker.close_port() safely.
                       Reference: src/interface.c  interface_close_port().
        """
        # TODO (Junior): implement
        pass

    @Slot()
    def _on_clear_display(self) -> None:
        """
        Clear the terminal view and the internal display buffer.

        Mirrors ``clear_display()`` in src/interface.c and
        ``clear_buffer()`` / ``clear_scrollback()`` in src/buffer.c
        and src/term_config.c.

        TODO (Junior): implement
                       self._terminal_view.clear()
                       Reference: src/interface.c  clear_display(),
                                  src/buffer.c  clear_buffer().
        """
        # TODO (Junior): implement
        pass

    @Slot()
    def _on_show_port_config_dialog(self) -> None:
        """
        Show the port-configuration dialog.

        The dialog mirrors ``Config_Port_Fenetre()`` in src/term_config.c
        and must expose:
          port device,  baud rate,  parity,  bits,  stop bits,  flow control,
          ASCII file-transfer delay,  RS-485 parameters,
          transport type (serial / TCP client / TCP server),
          TCP host & port.

        TODO (Junior): Create a QDialog (or a .ui file) with the same
                       layout as the GTK dialog.
                       Reference: src/term_config.c  Config_Port_Fenetre()
                                  (lines ~441-797).
        """
        # TODO (Junior): implement
        pass

    @Slot()
    def _on_show_terminal_config_dialog(self) -> None:
        """
        Show the terminal / display configuration dialog.

        Mirrors ``Config_Terminal()`` in src/term_config.c.

        TODO (Junior): Expose font chooser, foreground/background colour
                       pickers, rows, columns, scrollback, block cursor,
                       visual bell.
                       Reference: src/term_config.c  Config_Terminal().
        """
        # TODO (Junior): implement
        pass

    @Slot()
    def _on_send_break(self) -> None:
        """
        Send a serial BREAK.

        TODO (Junior): Call self._worker.send_break() via signal.
                       Reference: src/interface.c  signals_send_break_callback().
        """
        # TODO (Junior): implement
        pass

    @Slot()
    def _on_toggle_dtr(self) -> None:
        """
        Toggle the DTR modem-control line.

        TODO (Junior): Track current DTR state and call
                       self._worker.set_signal() with the correct bitmask.
                       Reference: src/interface.c  signals_toggle_DTR_callback().
        """
        # TODO (Junior): implement
        pass

    @Slot()
    def _on_toggle_rts(self) -> None:
        """
        Toggle the RTS modem-control line.

        TODO (Junior): Mirror _on_toggle_dtr for RTS.
                       Reference: src/interface.c  signals_toggle_RTS_callback().
        """
        # TODO (Junior): implement
        pass

    @Slot()
    def _on_about(self) -> None:
        """
        Show the About dialog.

        TODO (Junior): Build a QMessageBox.about() with application name,
                       version, and licence (GPL-3).
                       Reference: src/interface.c  help_about_callback().
        """
        QMessageBox.about(
            self,
            "About pyterm",
            "pyterm – A Python/PySide6 serial terminal\n\n"
            "Migrated from gtkTerm (GPLv3)."
        )

    # ------------------------------------------------------------------
    # Display helpers (stubs)
    # ------------------------------------------------------------------

    def _put_text(self, data: bytes) -> None:
        """
        Render *data* in ASCII / text mode.

        Mirrors ``put_text()`` in src/interface.c.

        TODO (Junior): Implement.
                       - Handle CR (0x0D), LF (0x0A), BS (0x08), DEL (0x7F).
                       - Handle crlfauto: append \\r\\n on bare \\n.
                       - Handle esc_clear_screen: clear on 0x1B.
                       - Prepend timestamp when self._timestamp is True.
                       - Append text to self._terminal_view.
                       Reference: src/interface.c  put_text().
        """
        # TODO (Junior): implement
        pass

    def _put_hexadecimal(self, data: bytes) -> None:
        """
        Render *data* in hex dump mode.

        Mirrors ``put_hexadecimal()`` in src/interface.c.

        TODO (Junior): Implement.
                       - Format bytes as a 16-column (configurable via
                         bytes_per_line) hex + ASCII side-by-side dump.
                       - Optionally prefix each line with a byte-offset
                         index when show_index is True.
                       - Track column position with an instance variable
                         (mirrors virt_col_pos in interface.c).
                       Reference: src/interface.c  put_hexadecimal()
                                  (lines ~1 – see interface.c,
                                  search for put_hexadecimal).
        """
        # TODO (Junior): implement
        pass

    def set_view(self, mode: int) -> None:
        """
        Switch between ASCII and hex display modes.

        Mirrors ``set_view()`` in src/interface.c.

        TODO (Junior): implement
                       1. Set self._view_mode = mode.
                       2. Call self._on_clear_display().
                       3. Enable/disable relevant toolbar/menu actions.
                       Reference: src/interface.c  set_view().
        """
        # TODO (Junior): implement
        self._view_mode = mode

    # ------------------------------------------------------------------
    # Config helpers
    # ------------------------------------------------------------------

    def _apply_config_to_ui(self) -> None:
        """
        Synchronise UI state (checkbox states, font, colours, etc.) with
        the current :attr:`_config`.

        Called once at startup and after loading a new configuration
        profile.  Mirrors ``ConfigFlags()`` in src/term_config.c.

        TODO (Junior): implement
                       - Set toolbar toggle actions from config flags.
                       - Apply font to _terminal_view.
                       - Set scrollback limit.
                       Reference: src/term_config.c  ConfigFlags(),
                                  src/interface.c  Set_local_echo(),
                                  Set_crlfauto(), Set_timestamp(), etc.
        """
        # TODO (Junior): implement
        pass

    # ------------------------------------------------------------------
    # Qt overrides
    # ------------------------------------------------------------------

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handle window close: stop worker thread, save config.

        TODO (Junior): implement
                       1. Call self._worker.close_port() and wait for thread.
                       2. Call pyterm.config.save_config(self._config).
                       3. Accept the event.
        """
        self._worker.close_port()
        self._worker.quit()
        if not self._worker.wait(3000):
            log.warning(
                "Worker thread did not stop within 3 s; terminating."
            )
            self._worker.terminate()
            self._worker.wait(1000)

        try:
            from pyterm.config import save_config
            save_config(self._config)
        except Exception as exc:
            log.error("Failed to save config on exit: %s", exc)

        event.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Forward key presses to the serial port when the terminal view
        has focus.

        Mirrors ``Envoie_car()`` / ``Got_Input()`` in src/interface.c.

        TODO (Junior): implement
                       - Encode the key text to bytes.
                       - Apply crlfauto (append \\r\\n on bare \\n).
                       - Call self._worker.send_bytes(data) via signal.
                       - If echo_on, also call self._put_text(data).
                       Reference: src/interface.c  Envoie_car(), Got_Input().
        """
        # TODO (Junior): implement
        super().keyPressEvent(event)
