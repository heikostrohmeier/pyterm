"""Tests for pyterm.config module."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from pyterm.config import (
    CONFIG_FILENAME,
    AppConfig,
    DisplayConfig,
    MacroConfig,
    PortConfig,
    get_config_path,
    hard_default_config,
    load_config,
    save_config,
)
from pyterm.utils import (
    DEFAULT_BAUDRATE,
    DEFAULT_BITS,
    DEFAULT_CHAR,
    DEFAULT_COLUMNS,
    DEFAULT_DELAY,
    DEFAULT_FLOW,
    DEFAULT_FONT,
    DEFAULT_PARITY,
    DEFAULT_PORT,
    DEFAULT_ROWS,
    DEFAULT_SCROLLBACK,
    DEFAULT_STOPBITS,
    TransportType,
)


class TestConfigFilename:
    def test_config_filename_value(self):
        assert CONFIG_FILENAME == "pytermrc"


class TestPortConfig:
    def test_default_port(self):
        cfg = PortConfig()
        assert cfg.port == DEFAULT_PORT

    def test_default_transport_type(self):
        cfg = PortConfig()
        assert cfg.transport_type == TransportType.SERIAL

    def test_default_socket_host(self):
        cfg = PortConfig()
        assert cfg.socket_host == "localhost"

    def test_default_socket_port(self):
        cfg = PortConfig()
        assert cfg.socket_port == "2323"

    def test_default_baudrate(self):
        cfg = PortConfig()
        assert cfg.baudrate == DEFAULT_BAUDRATE

    def test_default_bits(self):
        cfg = PortConfig()
        assert cfg.bits == DEFAULT_BITS

    def test_default_stopbits(self):
        cfg = PortConfig()
        assert cfg.stopbits == DEFAULT_STOPBITS

    def test_default_parity(self):
        cfg = PortConfig()
        assert cfg.parity == DEFAULT_PARITY

    def test_default_flow(self):
        cfg = PortConfig()
        assert cfg.flow == DEFAULT_FLOW

    def test_default_delay_ms(self):
        cfg = PortConfig()
        assert cfg.delay_ms == DEFAULT_DELAY

    def test_default_wait_char(self):
        cfg = PortConfig()
        assert cfg.wait_char == DEFAULT_CHAR

    def test_default_rs485_rts_before(self):
        cfg = PortConfig()
        assert cfg.rs485_rts_before == 30

    def test_default_rs485_rts_after(self):
        cfg = PortConfig()
        assert cfg.rs485_rts_after == 30

    def test_default_echo(self):
        cfg = PortConfig()
        assert cfg.echo is False

    def test_default_crlfauto(self):
        cfg = PortConfig()
        assert cfg.crlfauto is False

    def test_default_autoreconnect(self):
        cfg = PortConfig()
        assert cfg.autoreconnect is False

    def test_default_esc_clear_screen(self):
        cfg = PortConfig()
        assert cfg.esc_clear_screen is False

    def test_default_timestamp(self):
        cfg = PortConfig()
        assert cfg.timestamp is False

    def test_default_disable_port_lock(self):
        cfg = PortConfig()
        assert cfg.disable_port_lock is False

    def test_custom_values(self):
        cfg = PortConfig(
            port="/dev/ttyUSB0",
            baudrate=9600,
            bits=7,
            stopbits=2,
            parity=1,
            flow=2,
            echo=True,
        )
        assert cfg.port == "/dev/ttyUSB0"
        assert cfg.baudrate == 9600
        assert cfg.bits == 7
        assert cfg.stopbits == 2
        assert cfg.parity == 1
        assert cfg.flow == 2
        assert cfg.echo is True


class TestDisplayConfig:
    def test_default_font(self):
        cfg = DisplayConfig()
        assert cfg.font == DEFAULT_FONT

    def test_default_rows(self):
        cfg = DisplayConfig()
        assert cfg.rows == DEFAULT_ROWS

    def test_default_columns(self):
        cfg = DisplayConfig()
        assert cfg.columns == DEFAULT_COLUMNS

    def test_default_scrollback(self):
        cfg = DisplayConfig()
        assert cfg.scrollback == DEFAULT_SCROLLBACK

    def test_default_block_cursor(self):
        cfg = DisplayConfig()
        assert cfg.block_cursor is False

    def test_default_visual_bell(self):
        cfg = DisplayConfig()
        assert cfg.visual_bell is False

    def test_default_foreground_color(self):
        cfg = DisplayConfig()
        assert cfg.foreground_color == (0.0, 0.0, 0.0, 1.0)

    def test_default_background_color(self):
        cfg = DisplayConfig()
        assert cfg.background_color == (1.0, 1.0, 1.0, 1.0)

    def test_custom_values(self):
        cfg = DisplayConfig(
            font="Courier 14",
            rows=40,
            columns=132,
            scrollback=5000,
            block_cursor=True,
            visual_bell=True,
        )
        assert cfg.font == "Courier 14"
        assert cfg.rows == 40
        assert cfg.columns == 132
        assert cfg.scrollback == 5000
        assert cfg.block_cursor is True
        assert cfg.visual_bell is True


class TestMacroConfig:
    def test_default_label(self):
        cfg = MacroConfig()
        assert cfg.label == ""

    def test_default_shortcut(self):
        cfg = MacroConfig()
        assert cfg.shortcut == ""

    def test_default_action(self):
        cfg = MacroConfig()
        assert cfg.action == ""

    def test_default_tab(self):
        cfg = MacroConfig()
        assert cfg.tab == "General"

    def test_default_args(self):
        cfg = MacroConfig()
        assert cfg.args == []

    def test_default_polling_enabled(self):
        cfg = MacroConfig()
        assert cfg.polling_enabled is False

    def test_default_polling_period_ms(self):
        cfg = MacroConfig()
        assert cfg.polling_period_ms == 1000

    def test_custom_values(self):
        cfg = MacroConfig(
            label="Reset",
            shortcut="<Ctrl>F1",
            action="AT+RESET\r\n",
            tab="Commands",
            args=["arg1"],
            polling_enabled=True,
            polling_period_ms=500,
        )
        assert cfg.label == "Reset"
        assert cfg.shortcut == "<Ctrl>F1"
        assert cfg.action == "AT+RESET\r\n"
        assert cfg.tab == "Commands"
        assert cfg.args == ["arg1"]
        assert cfg.polling_enabled is True
        assert cfg.polling_period_ms == 500

    def test_args_are_independent_instances(self):
        cfg1 = MacroConfig()
        cfg2 = MacroConfig()
        cfg1.args.append("x")
        assert cfg2.args == []


class TestAppConfig:
    def test_default_port_config(self):
        cfg = AppConfig()
        assert isinstance(cfg.port, PortConfig)

    def test_default_display_config(self):
        cfg = AppConfig()
        assert isinstance(cfg.display, DisplayConfig)

    def test_default_macros_empty(self):
        cfg = AppConfig()
        assert cfg.macros == []

    def test_default_active_section(self):
        cfg = AppConfig()
        assert cfg.active_section == "default"

    def test_macros_are_independent_instances(self):
        cfg1 = AppConfig()
        cfg2 = AppConfig()
        cfg1.macros.append(MacroConfig(label="test"))
        assert cfg2.macros == []

    def test_custom_section(self):
        cfg = AppConfig(active_section="custom")
        assert cfg.active_section == "custom"


class TestGetConfigPath:
    def test_returns_path_object(self):
        path = get_config_path()
        assert isinstance(path, Path)

    def test_filename_is_pytermrc(self):
        path = get_config_path()
        assert path.name == CONFIG_FILENAME

    def test_uses_xdg_config_home_when_set(self):
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/tmp/test_config"}):
            path = get_config_path()
            assert path == Path("/tmp/test_config") / CONFIG_FILENAME

    def test_falls_back_to_home_dot_config(self):
        with patch.dict(os.environ, {}, clear=True):
            # Remove XDG_CONFIG_HOME to test fallback
            env = os.environ.copy()
            env.pop("XDG_CONFIG_HOME", None)
            with patch.dict(os.environ, env, clear=True):
                path = get_config_path()
                expected = Path.home() / ".config" / CONFIG_FILENAME
                assert path == expected


class TestLoadConfig:
    def test_returns_none_stub(self):
        # Current implementation is a stub returning None (pass)
        result = load_config()
        assert result is None

    def test_accepts_section_parameter(self):
        result = load_config(section="custom")
        assert result is None

    def test_accepts_path_parameter(self):
        result = load_config(path=Path("/tmp/nonexistent"))
        assert result is None


class TestSaveConfig:
    def test_save_does_not_raise(self):
        cfg = AppConfig()
        # Current implementation is a stub (pass), should not raise
        save_config(cfg)

    def test_save_accepts_section(self):
        cfg = AppConfig()
        save_config(cfg, section="custom")

    def test_save_accepts_path(self):
        cfg = AppConfig()
        save_config(cfg, path=Path("/tmp/test_save"))


class TestHardDefaultConfig:
    def test_returns_app_config(self):
        cfg = hard_default_config()
        assert isinstance(cfg, AppConfig)

    def test_port_has_defaults(self):
        cfg = hard_default_config()
        assert cfg.port.port == DEFAULT_PORT
        assert cfg.port.baudrate == DEFAULT_BAUDRATE
        assert cfg.port.bits == DEFAULT_BITS
        assert cfg.port.stopbits == DEFAULT_STOPBITS
        assert cfg.port.parity == DEFAULT_PARITY
        assert cfg.port.flow == DEFAULT_FLOW

    def test_display_has_defaults(self):
        cfg = hard_default_config()
        assert cfg.display.font == DEFAULT_FONT
        assert cfg.display.rows == DEFAULT_ROWS
        assert cfg.display.columns == DEFAULT_COLUMNS
        assert cfg.display.scrollback == DEFAULT_SCROLLBACK

    def test_macros_empty(self):
        cfg = hard_default_config()
        assert cfg.macros == []

    def test_active_section_is_default(self):
        cfg = hard_default_config()
        assert cfg.active_section == "default"

    def test_returns_fresh_instance_each_call(self):
        cfg1 = hard_default_config()
        cfg2 = hard_default_config()
        assert cfg1 is not cfg2
        cfg1.port.baudrate = 9600
        assert cfg2.port.baudrate == DEFAULT_BAUDRATE
