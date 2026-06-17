"""Tests for pyterm.utils module."""

from pyterm.utils import (
    BUFFER_EMISSION,
    BUFFER_RECEPTION,
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
    DISPLAY_BUFFER_SIZE,
    FLOW_LABELS,
    LINE_FEED,
    PARITY_LABELS,
    PARITY_MAP,
    POLL_DELAY_MS,
    STANDARD_BAUDRATES,
    MsgSeverity,
    TransportType,
    ViewMode,
    is_standard_baudrate,
)


class TestTransportType:
    def test_serial_value(self):
        assert TransportType.SERIAL == 0

    def test_tcp_client_value(self):
        assert TransportType.TCP_CLIENT == 1

    def test_tcp_server_value(self):
        assert TransportType.TCP_SERVER == 2


class TestViewMode:
    def test_ascii_value(self):
        assert ViewMode.ASCII == 0

    def test_hexadecimal_value(self):
        assert ViewMode.HEXADECIMAL == 1


class TestMsgSeverity:
    def test_warning_value(self):
        assert MsgSeverity.WARNING == 0

    def test_error_value(self):
        assert MsgSeverity.ERROR == 1


class TestBufferConstants:
    def test_buffer_reception_size(self):
        assert BUFFER_RECEPTION == 8192

    def test_buffer_emission_size(self):
        assert BUFFER_EMISSION == 4096

    def test_line_feed_value(self):
        assert LINE_FEED == 0x0A

    def test_poll_delay_ms(self):
        assert POLL_DELAY_MS == 100

    def test_display_buffer_size(self):
        assert DISPLAY_BUFFER_SIZE == 128 * 1024


class TestDefaultPortConfig:
    def test_default_port(self):
        assert DEFAULT_PORT == "/dev/ttyS0"

    def test_default_baudrate(self):
        assert DEFAULT_BAUDRATE == 115200

    def test_default_parity(self):
        assert DEFAULT_PARITY == 0

    def test_default_bits(self):
        assert DEFAULT_BITS == 8

    def test_default_stopbits(self):
        assert DEFAULT_STOPBITS == 1

    def test_default_flow(self):
        assert DEFAULT_FLOW == 0

    def test_default_delay(self):
        assert DEFAULT_DELAY == 0

    def test_default_char(self):
        assert DEFAULT_CHAR == -1


class TestDefaultDisplayConfig:
    def test_default_font(self):
        assert DEFAULT_FONT == "Monospace 12"

    def test_default_scrollback(self):
        assert DEFAULT_SCROLLBACK == 10_000

    def test_default_rows(self):
        assert DEFAULT_ROWS == 24

    def test_default_columns(self):
        assert DEFAULT_COLUMNS == 80


class TestStandardBaudrates:
    def test_is_list(self):
        assert isinstance(STANDARD_BAUDRATES, list)

    def test_not_empty(self):
        assert len(STANDARD_BAUDRATES) > 0

    def test_sorted_ascending(self):
        assert STANDARD_BAUDRATES == sorted(STANDARD_BAUDRATES)

    def test_contains_common_rates(self):
        common = [9600, 19200, 38400, 57600, 115200]
        for rate in common:
            assert rate in STANDARD_BAUDRATES

    def test_all_positive(self):
        for rate in STANDARD_BAUDRATES:
            assert rate > 0

    def test_no_duplicates(self):
        assert len(STANDARD_BAUDRATES) == len(set(STANDARD_BAUDRATES))


class TestParityMap:
    def test_none_parity(self):
        assert PARITY_MAP[0] == "N"

    def test_odd_parity(self):
        assert PARITY_MAP[1] == "O"

    def test_even_parity(self):
        assert PARITY_MAP[2] == "E"

    def test_all_keys_present(self):
        assert set(PARITY_MAP.keys()) == {0, 1, 2}


class TestParityLabels:
    def test_none_label(self):
        assert PARITY_LABELS[0] == "None"

    def test_odd_label(self):
        assert PARITY_LABELS[1] == "Odd"

    def test_even_label(self):
        assert PARITY_LABELS[2] == "Even"

    def test_all_keys_present(self):
        assert set(PARITY_LABELS.keys()) == {0, 1, 2}


class TestFlowLabels:
    def test_none_flow(self):
        assert FLOW_LABELS[0] == "None"

    def test_xonxoff_flow(self):
        assert FLOW_LABELS[1] == "Xon/Xoff"

    def test_rtscts_flow(self):
        assert FLOW_LABELS[2] == "RTS/CTS"

    def test_rs485_flow(self):
        assert FLOW_LABELS[3] == "RS-485 Half-Duplex (RTS)"

    def test_all_keys_present(self):
        assert set(FLOW_LABELS.keys()) == {0, 1, 2, 3}


class TestIsStandardBaudrate:
    def test_valid_standard_rate(self):
        assert is_standard_baudrate(115200) is True

    def test_valid_low_rate(self):
        assert is_standard_baudrate(50) is True

    def test_valid_high_rate(self):
        assert is_standard_baudrate(4000000) is True

    def test_invalid_rate(self):
        assert is_standard_baudrate(12345) is False

    def test_zero_rate(self):
        assert is_standard_baudrate(0) is False

    def test_negative_rate(self):
        assert is_standard_baudrate(-1) is False

    def test_all_standard_rates_valid(self):
        for rate in STANDARD_BAUDRATES:
            assert is_standard_baudrate(rate) is True
