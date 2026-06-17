"""Tests for pyterm.serial_worker module."""

import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QThread

from pyterm.config import PortConfig
from pyterm.serial_worker import SerialWorker
from pyterm.utils import BUFFER_RECEPTION, POLL_DELAY_MS, TransportType


class TestSerialWorkerInit:
    def test_inherits_qthread(self):
        assert issubclass(SerialWorker, QThread)

    def test_initial_config_is_none(self, worker):
        assert worker._config is None

    def test_initial_port_is_none(self, worker):
        assert worker._port is None

    def test_initial_write_queue_empty(self, worker):
        assert worker._write_queue == bytearray()

    def test_initial_running_false(self, worker):
        assert worker._running is False

    def test_initial_stop_request_false(self, worker):
        assert worker._stop_request is False

    def test_mutex_exists(self, worker):
        assert worker._mutex is not None

    def test_write_cond_exists(self, worker):
        assert worker._write_cond is not None


class TestSerialWorkerSignals:
    def test_has_data_received_signal(self, worker):
        assert hasattr(worker, "data_received")

    def test_has_port_opened_signal(self, worker):
        assert hasattr(worker, "port_opened")

    def test_has_port_closed_signal(self, worker):
        assert hasattr(worker, "port_closed")

    def test_has_port_error_signal(self, worker):
        assert hasattr(worker, "port_error")

    def test_has_control_signals_changed_signal(self, worker):
        assert hasattr(worker, "control_signals_changed")


class TestSerialWorkerOpenPort:
    def test_open_port_stores_config(self, worker):
        config = PortConfig(port="/dev/ttyUSB0", baudrate=9600)
        worker.open_port(config)
        assert worker._config is config

    def test_open_port_with_serial_transport(self, worker):
        config = PortConfig(transport_type=TransportType.SERIAL)
        worker.open_port(config)
        assert worker._config.transport_type == TransportType.SERIAL

    def test_open_port_with_tcp_client(self, worker):
        config = PortConfig(transport_type=TransportType.TCP_CLIENT)
        worker.open_port(config)
        assert worker._config.transport_type == TransportType.TCP_CLIENT

    def test_open_port_with_tcp_server(self, worker):
        config = PortConfig(transport_type=TransportType.TCP_SERVER)
        worker.open_port(config)
        assert worker._config.transport_type == TransportType.TCP_SERVER


class TestSerialWorkerClosePort:
    def test_close_port_does_not_raise(self, worker):
        worker.close_port()


class TestSerialWorkerSendBytes:
    def test_send_bytes_does_not_raise(self, worker):
        worker.send_bytes(b"hello")

    def test_send_bytes_with_empty_data(self, worker):
        worker.send_bytes(b"")


class TestSerialWorkerSendBreak:
    def test_send_break_does_not_raise(self, worker):
        worker.send_break()


class TestSerialWorkerSetSignal:
    def test_set_signal_does_not_raise(self, worker):
        worker.set_signal(0)

    def test_set_signal_with_nonzero_mask(self, worker):
        worker.set_signal(0xFF)


class TestSerialWorkerApplyConfig:
    def test_apply_config_stores_config(self, worker):
        config = PortConfig(baudrate=9600)
        worker.apply_config(config)
        assert worker._config is config

    def test_apply_config_updates_config(self, worker):
        config1 = PortConfig(baudrate=9600)
        config2 = PortConfig(baudrate=115200)
        worker.apply_config(config1)
        worker.apply_config(config2)
        assert worker._config is config2


class TestSerialWorkerGetStatusString:
    def test_status_when_not_configured(self, worker):
        assert worker._get_status_string() == "Not configured"

    def test_status_when_configured(self, worker):
        worker._config = PortConfig(port="/dev/ttyUSB0")
        status = worker._get_status_string()
        assert "/dev/ttyUSB0" in status

    def test_status_contains_port_prefix(self, worker):
        worker._config = PortConfig(port="/dev/ttyS1")
        status = worker._get_status_string()
        assert "Port:" in status


class TestSerialWorkerPollControlSignals:
    def test_returns_zero_when_not_implemented(self, worker):
        assert worker._poll_control_signals() == 0


class TestSerialWorkerRun:
    def test_run_does_not_raise(self, worker):
        # Current implementation is a stub (pass)
        worker.run()


# Fixture to create a worker without starting the QApplication event loop
@pytest.fixture
def worker(qapp):
    return SerialWorker()
