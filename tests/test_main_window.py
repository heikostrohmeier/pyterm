"""Tests for pyterm.main_window module."""

import pytest

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QMainWindow, QPlainTextEdit, QToolBar

from pyterm.config import AppConfig, PortConfig
from pyterm.main_window import MainWindow
from pyterm.serial_worker import SerialWorker
from pyterm.utils import ViewMode


@pytest.fixture
def app_config():
    return AppConfig()


@pytest.fixture
def window(qapp, app_config):
    win = MainWindow(app_config)
    yield win
    win.close()


class TestMainWindowInit:
    def test_inherits_qmainwindow(self):
        assert issubclass(MainWindow, QMainWindow)

    def test_window_title(self, window):
        assert window.windowTitle() == "pyterm"

    def test_config_stored(self, window, app_config):
        assert window._config is app_config

    def test_initial_view_mode_ascii(self, window):
        assert window._view_mode == ViewMode.ASCII

    def test_initial_echo_matches_config(self, window, app_config):
        assert window._echo_on == app_config.port.echo

    def test_initial_crlfauto_matches_config(self, window, app_config):
        assert window._crlfauto == app_config.port.crlfauto

    def test_initial_timestamp_matches_config(self, window, app_config):
        assert window._timestamp == app_config.port.timestamp


class TestMainWindowCentralWidget:
    def test_central_widget_exists(self, window):
        assert window.centralWidget() is not None

    def test_central_widget_is_plaintextedit(self, window):
        assert isinstance(window.centralWidget(), QPlainTextEdit)

    def test_terminal_view_is_readonly(self, window):
        assert window._terminal_view.isReadOnly() is True

    def test_terminal_view_object_name(self, window):
        assert window._terminal_view.objectName() == "terminalView"


class TestMainWindowToolbar:
    def test_toolbar_exists(self, window):
        assert window._toolbar is not None

    def test_toolbar_is_qtoolbar(self, window):
        assert isinstance(window._toolbar, QToolBar)

    def test_toolbar_object_name(self, window):
        assert window._toolbar.objectName() == "mainToolbar"

    def test_action_open_port_exists(self, window):
        assert window._action_open_port is not None
        assert window._action_open_port.text() == "Open Port"

    def test_action_close_port_exists(self, window):
        assert window._action_close_port is not None
        assert window._action_close_port.text() == "Close Port"

    def test_action_clear_exists(self, window):
        assert window._action_clear is not None
        assert window._action_clear.text() == "Clear"

    def test_action_ascii_view_checkable(self, window):
        assert window._action_ascii_view.isCheckable() is True
        assert window._action_ascii_view.isChecked() is True

    def test_action_hex_view_checkable(self, window):
        assert window._action_hex_view.isCheckable() is True
        assert window._action_hex_view.isChecked() is False

    def test_action_echo_checkable(self, window):
        assert window._action_echo.isCheckable() is True

    def test_action_crlfauto_checkable(self, window):
        assert window._action_crlfauto.isCheckable() is True


class TestMainWindowStatusBar:
    def test_statusbar_exists(self, window):
        assert window._statusbar is not None

    def test_status_label_initial_text(self, window):
        assert window._status_label.text() == "No port open"

    def test_signal_labels_present(self, window):
        expected_signals = {"CTS", "DSR", "DCD", "RI", "DTR", "RTS"}
        assert set(window._signal_labels.keys()) == expected_signals

    def test_signal_label_object_names(self, window):
        for name, label in window._signal_labels.items():
            assert label.objectName() == f"led_{name}"


class TestMainWindowMacroDock:
    def test_macro_dock_exists(self, window):
        assert window._macro_dock is not None

    def test_macro_dock_is_qdockwidget(self, window):
        assert isinstance(window._macro_dock, QDockWidget)

    def test_macro_dock_object_name(self, window):
        assert window._macro_dock.objectName() == "macroDock"

    def test_macro_dock_hidden_by_default(self, window):
        assert window._macro_dock.isVisible() is False


class TestMainWindowWorker:
    def test_worker_exists(self, window):
        assert window._worker is not None

    def test_worker_is_serial_worker(self, window):
        assert isinstance(window._worker, SerialWorker)


class TestMainWindowSlots:
    def test_on_port_opened_updates_label(self, window):
        window._on_port_opened("Serial: /dev/ttyS0 115200 8N1")
        assert window._status_label.text() == "Serial: /dev/ttyS0 115200 8N1"

    def test_on_port_closed_updates_label(self, window):
        window._on_port_closed()
        assert window._status_label.text() == "Port closed"

    def test_on_port_error_updates_label(self, window):
        window._on_port_error("Connection refused")
        assert "Connection refused" in window._status_label.text()

    def test_on_data_received_does_not_raise(self, window):
        window._on_data_received(b"hello")

    def test_on_control_signals_changed_does_not_raise(self, window):
        window._on_control_signals_changed(0xFF)


class TestMainWindowSetView:
    def test_set_view_ascii(self, window):
        window.set_view(ViewMode.ASCII)
        assert window._view_mode == ViewMode.ASCII

    def test_set_view_hex(self, window):
        window.set_view(ViewMode.HEXADECIMAL)
        assert window._view_mode == ViewMode.HEXADECIMAL


class TestMainWindowActions:
    def test_on_open_port_does_not_raise(self, window):
        window._on_open_port()

    def test_on_close_port_does_not_raise(self, window):
        window._on_close_port()

    def test_on_clear_display_does_not_raise(self, window):
        window._on_clear_display()

    def test_on_send_break_does_not_raise(self, window):
        window._on_send_break()

    def test_on_toggle_dtr_does_not_raise(self, window):
        window._on_toggle_dtr()

    def test_on_toggle_rts_does_not_raise(self, window):
        window._on_toggle_rts()

    def test_on_show_port_config_dialog_does_not_raise(self, window):
        window._on_show_port_config_dialog()

    def test_on_show_terminal_config_dialog_does_not_raise(self, window):
        window._on_show_terminal_config_dialog()


class TestMainWindowDisplayHelpers:
    def test_put_text_does_not_raise(self, window):
        window._put_text(b"test data")

    def test_put_hexadecimal_does_not_raise(self, window):
        window._put_hexadecimal(b"\x00\x01\x02\x03")
