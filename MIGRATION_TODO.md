# pyterm Migration TODO

> **Audience:** Local 14B LLM acting as Junior Developer.
>
> **Rules for every task:**
> 1. Read the referenced C file(s) first. Do not guess.
> 2. Edit **only** the Python file(s) listed in the task.
> 3. Replace every `# TODO (Junior): implement` comment with real code.
> 4. Do **not** introduce new dependencies without updating `requirements.txt`.
> 5. Keep every change isolated – one task at a time.
> 6. After every task, verify the app still starts: `python main.py --help` (or
>    the stub equivalent until the real parser is in place).

---

## Phase 0 – Environment Setup

- [ ] **0.1 – Create `requirements.txt`**
  - File to edit: `requirements.txt` (create it)
  - Add the following lines:
    ```
    PySide6>=6.5
    pyserial>=3.5
    ```
  - No C reference needed.

- [ ] **0.2 – Verify imports**
  - Run `python -c "from pyterm.config import AppConfig; print('OK')"`.
  - Fix any import errors before proceeding.
  - No C reference needed.

---

## Phase 1 – Configuration (`pyterm/config.py`)

### 1.1 – `get_config_path()` – legacy migration
- [ ] **Task:** Add optional migration from `$HOME/.gtktermrc` to the new
  XDG path.
  - **C reference:** `src/term_config.c` → `config_file_init()` (lines ~168-184)
  - **Python file:** `pyterm/config.py` → function `get_config_path()`
  - **Logic:**
    1. Compute `old_path = Path.home() / ".gtktermrc"`.
    2. Compute `new_path` via existing XDG logic.
    3. If `new_path` does not exist **and** `old_path` exists, move the file
       with `old_path.rename(new_path)`.
    4. Return `new_path`.

### 1.2 – `load_config()` – implement INI parsing
- [ ] **Task:** Implement full config loading.
  - **C reference:** `src/term_config.c` → `Load_configuration_from_file()`,
    the `cfg[]` array (lines ~100-137), `cfgParse()` from `src/parsecfg.c`
  - **Python file:** `pyterm/config.py` → function `load_config()`
  - **Logic:**
    1. If the file does not exist, return `hard_default_config()`.
    2. Use `configparser.ConfigParser()`. Call `parser.read(str(path))`.
    3. Read the `[section]` block (default: `"default"`).
    4. For each key in the C `cfg[]` array, read the value and set the
       corresponding `PortConfig` or `DisplayConfig` field. Key-name mapping:

       | INI key                    | Python field                          | Type  |
       |----------------------------|---------------------------------------|-------|
       | `port`                     | `cfg.port.port`                       | str   |
       | `speed`                    | `cfg.port.baudrate`                   | int   |
       | `bits`                     | `cfg.port.bits`                       | int   |
       | `stopbits`                 | `cfg.port.stopbits`                   | int   |
       | `parity`                   | `cfg.port.parity` (map "none"→0, "odd"→1, "even"→2) | int |
       | `flow`                     | `cfg.port.flow` (map "none"→0, "xonxoff"→1, "rtscts"→2, "rs485"→3) | int |
       | `wait_delay`               | `cfg.port.delay_ms`                   | int   |
       | `wait_char`                | `cfg.port.wait_char`                  | int   |
       | `rs485_rts_time_before_tx` | `cfg.port.rs485_rts_before`           | int   |
       | `rs485_rts_time_after_tx`  | `cfg.port.rs485_rts_after`            | int   |
       | `echo`                     | `cfg.port.echo`                       | bool  |
       | `crlfauto`                 | `cfg.port.crlfauto`                   | bool  |
       | `autoreconnect_enabled`    | `cfg.port.autoreconnect`              | bool  |
       | `esc_clear_screen`         | `cfg.port.esc_clear_screen`           | bool  |
       | `timestamp`                | `cfg.port.timestamp`                  | bool  |
       | `font`                     | `cfg.display.font`                    | str   |
       | `term_block_cursor`        | `cfg.display.block_cursor`            | bool  |
       | `term_rows`                | `cfg.display.rows`                    | int   |
       | `term_columns`             | `cfg.display.columns`                 | int   |
       | `term_scrollback`          | `cfg.display.scrollback`              | int   |
       | `term_visual_bell`         | `cfg.display.visual_bell`             | bool  |
       | `term_foreground_red/green/blue/alpha` | `cfg.display.foreground_color` tuple | float |
       | `term_background_red/green/blue/alpha` | `cfg.display.background_color` tuple | float |
       | `transport_type`           | `cfg.port.transport_type`             | int   |
       | `socket_host`              | `cfg.port.socket_host`                | str   |
       | `socket_port`              | `cfg.port.socket_port`                | str   |
       | `show_rxtx`                | **ignore** (backward compat)          | –     |

    5. Wrap in `try/except` and fall back to `hard_default_config()` on error.

### 1.3 – `save_config()` – implement INI writing
- [ ] **Task:** Implement config persistence.
  - **C reference:** `src/term_config.c` → `Copy_configuration()`,
    `save_config_silent()`, `cfgDump()`
  - **Python file:** `pyterm/config.py` → function `save_config()`
  - **Logic:**
    1. Create `path.parent` if it does not exist.
    2. Load existing file into `configparser.ConfigParser` (so other sections
       are preserved).
    3. Write all fields from the table in task 1.2 into `parser[section]`.
    4. Encode booleans as `"1"` / `"0"` for compatibility with the old
       `.gtktermrc` format.
    5. Write the file with `parser.write(open(path, "w"))`.

---

## Phase 2 – Utilities (`pyterm/utils.py`)

### 2.1 – Baud-rate list sync
- [ ] **Task:** Verify `STANDARD_BAUDRATES` matches `src/baudrates.h`.
  - **C reference:** `src/baudrates.h` (generated file; look for `B300`, `B600`, etc.)
  - **Python file:** `pyterm/utils.py` → `STANDARD_BAUDRATES` list
  - **Logic:** Open `src/baudrates.h`, extract all `{ <baud>, B<baud> }` entries.
    Add any missing values; remove values not present in the file.

### 2.2 – Replace parity string literals with pyserial constants
- [ ] **Task:** Replace `"N"`, `"O"`, `"E"` strings with `serial.PARITY_*`.
  - **C reference:** `src/term_config.c` → `Lis_Config()` parity block (~lines 834-841)
  - **Python file:** `pyterm/utils.py` → `PARITY_MAP`
  - **Logic:**
    ```python
    import serial
    PARITY_MAP = {
        0: serial.PARITY_NONE,
        1: serial.PARITY_ODD,
        2: serial.PARITY_EVEN,
    }
    ```

---

## Phase 3 – Serial Worker (`pyterm/serial_worker.py`)

### 3.1 – `open_port()` – serial transport
- [ ] **Task:** Implement opening a serial port.
  - **C reference:** `src/transport.c` → `transport_open()` (serial branch)
  - **Python file:** `pyterm/serial_worker.py` → `SerialWorker.open_port()`
  - **Logic:**
    1. `import serial` at the top of the file.
    2. If `self._port` is not `None` and `self._port.is_open`, call
       `self._port.close()`.
    3. If `config.transport_type == TransportType.SERIAL`:
       ```python
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
       ```
    4. Set `self._running = True`, `self._stop_request = False`.
    5. Emit `self.port_opened(self._get_status_string())`.
    6. Wrap all of the above in `try/except serial.SerialException as e:`
       and emit `self.port_error(str(e))` on failure.

### 3.2 – `open_port()` – TCP client transport
- [ ] **Task:** Implement opening a TCP client connection.
  - **C reference:** `src/transport.c` → `transport_open()` (TCP client branch)
  - **Python file:** `pyterm/serial_worker.py` → `SerialWorker.open_port()`
  - **Logic:** (add after the SERIAL branch)
    ```python
    elif config.transport_type == TransportType.TCP_CLIENT:
        url = f"socket://{config.socket_host}:{config.socket_port}"
        self._port = serial.serial_for_url(url, timeout=0.1)
    ```

### 3.3 – `open_port()` – TCP server transport
- [ ] **Task:** Implement a simple single-client TCP server.
  - **C reference:** `src/transport.c` → `transport_open()` (TCP server branch)
  - **Python file:** `pyterm/serial_worker.py` → `SerialWorker.open_port()`
  - **Logic:**
    ```python
    elif config.transport_type == TransportType.TCP_SERVER:
        import socket as _socket
        srv = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        srv.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
        srv.bind(("", int(config.socket_port)))
        srv.listen(1)
        conn, _ = srv.accept()   # blocking; acceptable – called from worker thread
        self._port = serial.serial_for_url(
            f"socket://localhost:{config.socket_port}", timeout=0.1
        )
    ```
    > Note: A cleaner implementation may wrap the raw socket; adjust as needed
    > based on what pyserial supports on the target platform.

### 3.4 – `close_port()`
- [ ] **Task:** Implement clean port shutdown.
  - **C reference:** `src/serial.c` → `Close_port()`,
    `src/transport.c` → `transport_close()`
  - **Python file:** `pyterm/serial_worker.py` → `SerialWorker.close_port()`
  - **Logic:**
    1. `with QMutexLocker(self._mutex): self._stop_request = True`
    2. `self._write_cond.wakeAll()`
    3. ```python
       if self._port and self._port.is_open:
           try:
               self._port.close()
           except Exception:
               pass
       ```
    4. `self.port_closed.emit()`

### 3.5 – `run()` – main I/O loop
- [ ] **Task:** Implement the read/write polling loop.
  - **C reference:** `src/transport.c` (the GLib I/O channel callback),
    `src/serial.c`, `src/device_monitor.c`
  - **Python file:** `pyterm/serial_worker.py` → `SerialWorker.run()`
  - **Logic (skeleton):**
    ```python
    import serial, time
    last_poll_time = time.monotonic()

    while True:
        with QMutexLocker(self._mutex):
            if self._stop_request:
                break
            to_send = bytes(self._write_queue)
            self._write_queue.clear()

        # --- Write ---
        if to_send and self._port and self._port.is_open:
            try:
                self._port.write(to_send)
            except serial.SerialException as e:
                self.port_error.emit(str(e))

        # --- Read ---
        if self._port and self._port.is_open:
            try:
                data = self._port.read(BUFFER_RECEPTION)
                if data:
                    self.data_received.emit(data)
            except serial.SerialException:
                self.port_closed.emit()
                if self._config and self._config.autoreconnect:
                    # TODO (Junior): implement reconnect loop (see task 3.6)
                    pass
                break

        # --- Control-signal poll (every POLL_DELAY_MS) ---
        now = time.monotonic()
        if (now - last_poll_time) * 1000 >= POLL_DELAY_MS:
            mask = self._poll_control_signals()
            self.control_signals_changed.emit(mask)
            last_poll_time = now
    ```

### 3.6 – Auto-reconnect
- [ ] **Task:** Implement auto-reconnect on port loss.
  - **C reference:** `src/device_monitor.c`, `src/serial.c`
    `configure_autoreconnect_enable()`
  - **Python file:** `pyterm/serial_worker.py` → inside `run()` error handler
  - **Logic:**
    ```python
    # Inside the except serial.SerialException block in run():
    if self._config and self._config.autoreconnect:
        self.port_error.emit("Port lost – attempting reconnect…")
        for _ in range(10):   # retry up to 10 times
            time.sleep(2)
            try:
                self.open_port(self._config)
                break
            except Exception:
                pass
        else:
            self.port_closed.emit()
    else:
        self.port_closed.emit()
    ```

### 3.7 – `send_bytes()` – thread-safe write queue
- [ ] **Task:** Implement the write-queue enqueue.
  - **C reference:** `src/serial.c` → `Send_chars()`,
    `src/transport.c` → `transport_send()`
  - **Python file:** `pyterm/serial_worker.py` → `SerialWorker.send_bytes()`
  - **Logic:**
    ```python
    with QMutexLocker(self._mutex):
        self._write_queue.extend(data)
        self._write_cond.wakeOne()
    ```

### 3.8 – `send_break()`
- [ ] **Task:** Implement serial BREAK.
  - **C reference:** `src/serial.c` → `sendbreak()`,
    `src/transport.c` → `transport_send_break()`
  - **Python file:** `pyterm/serial_worker.py` → `SerialWorker.send_break()`
  - **Logic:**
    ```python
    if self._port and self._port.is_open:
        try:
            self._port.send_break()
        except Exception as e:
            self.port_error.emit(str(e))
    ```

### 3.9 – `set_signal()` – DTR / RTS
- [ ] **Task:** Decode the signal bitmask and drive DTR/RTS.
  - **C reference:** `src/serial.c` → `Set_signals()`,
    `src/transport.c` → `transport_set_signal()`
  - **Python file:** `pyterm/serial_worker.py` → `SerialWorker.set_signal()`
  - **Logic:**
    Read the C source to identify which bit represents DTR and which RTS.
    Then:
    ```python
    if self._port and self._port.is_open:
        self._port.dtr = bool(signal_mask & DTR_BIT)
        self._port.rts = bool(signal_mask & RTS_BIT)
    ```

### 3.10 – `_poll_control_signals()` – read CTS/DSR/DCD/RI
- [ ] **Task:** Read input modem-control lines and pack into a bitmask.
  - **C reference:** `src/transport.c` → `transport_get_signals()`
  - **Python file:** `pyterm/serial_worker.py` → `SerialWorker._poll_control_signals()`
  - **Logic:**
    Read the C source for which bits correspond to CTS, DSR, DCD, RI.  Then:
    ```python
    if not (self._port and self._port.is_open):
        return 0
    mask = 0
    if self._port.cts:  mask |= CTS_BIT
    if self._port.dsr:  mask |= DSR_BIT
    if self._port.dcd:  mask |= DCD_BIT
    if self._port.ri:   mask |= RI_BIT
    return mask
    ```

### 3.11 – `_get_status_string()`
- [ ] **Task:** Build a human-readable connection status string.
  - **C reference:** `src/transport.c` → `transport_get_status_string()`
  - **Python file:** `pyterm/serial_worker.py` → `SerialWorker._get_status_string()`
  - **Logic:** Produce a string like:
    - Serial: `"/dev/ttyS0  115200 8N1 (RTS/CTS)"`
    - TCP client: `"TCP Client: host:port [connected]"`
    - TCP server: `"TCP Server: listening on port <port>"`

### 3.12 – `apply_config()` – hot-apply settings
- [ ] **Task:** Apply new port settings without a full close/open.
  - **C reference:** `src/term_config.c` → `Lis_Config()`,
    `src/serial.c` → `Config_port()`
  - **Python file:** `pyterm/serial_worker.py` → `SerialWorker.apply_config()`
  - **Logic:**
    ```python
    self._config = config
    if self._port and self._port.is_open:
        self._port.baudrate = config.baudrate
        self._port.bytesize = config.bits
        self._port.parity   = PARITY_MAP[config.parity]
        self._port.stopbits = config.stopbits
        self._port.xonxoff  = (config.flow == 1)
        self._port.rtscts   = (config.flow == 2)
    else:
        self.open_port(config)
    ```

---

## Phase 4 – Main Window: Actions & Connections (`pyterm/main_window.py`)

### 4.1 – Wire toolbar actions to slots
- [ ] **Task:** Uncomment (and complete) all `triggered.connect(...)` lines in
  `_setup_toolbar()`.
  - **C reference:** `src/interface.c` → `create_actions_and_menu()`
  - **Python file:** `pyterm/main_window.py` → `_setup_toolbar()`
  - **Logic:**
    ```python
    self._action_open_port.triggered.connect(self._on_open_port)
    self._action_close_port.triggered.connect(self._on_close_port)
    self._action_clear.triggered.connect(self._on_clear_display)
    self._action_ascii_view.triggered.connect(lambda: self.set_view(ViewMode.ASCII))
    self._action_hex_view.triggered.connect(lambda: self.set_view(ViewMode.HEXADECIMAL))
    self._action_echo.toggled.connect(self._on_echo_toggled)
    self._action_crlfauto.toggled.connect(self._on_crlfauto_toggled)
    ```

### 4.2 – Populate File menu
- [ ] **Task:** Add actions to `menu_file`.
  - **C reference:** `src/interface.c` → `create_actions_and_menu()` (File menu entries)
  - **Python file:** `pyterm/main_window.py` → `_setup_menubar()` File section
  - **Actions to add:**
    - Open Port → `self._on_open_port`
    - Close Port → `self._on_close_port`
    - Separator
    - Send ASCII file → `self._on_send_ascii_file`  (stub: `pass`)
    - Separator
    - Exit → `self.close`

### 4.3 – Populate Edit menu
- [ ] **Task:** Add actions to `menu_edit`.
  - **C reference:** `src/interface.c` → `create_actions_and_menu()` (Edit menu)
  - **Python file:** `pyterm/main_window.py` → `_setup_menubar()` Edit section
  - **Actions to add:**
    - Copy → `self._terminal_view.copy`
    - Paste → `self._on_paste`  (stub; calls `send_bytes` with clipboard text)
    - Select All → `self._terminal_view.selectAll`
    - Find → show `QPlainTextEdit.find()` toolbar (stub: `pass`)
    - Separator
    - Clear scrollback → `self._on_clear_display`

### 4.4 – Populate View menu
- [ ] **Task:** Add actions to `menu_view`.
  - **C reference:** `src/interface.c` → `create_actions_and_menu()` (View menu)
  - **Python file:** `pyterm/main_window.py` → `_setup_menubar()` View section
  - **Actions to add:**
    - ASCII View (checkable, radio group with Hex View)
    - Hex View (checkable)
    - Sub-menu: "Hex chars per line" → 8, 16 (default), 24, 32 items
    - Checkable: Show index → `self._on_show_index_toggled`  (stub: `pass`)
    - Separator
    - Checkable: Send hex bar → toggles `_hex_bar_visible`
    - Checkable: Macro panel → `self._macro_dock.setVisible`

### 4.5 – Populate Settings menu
- [ ] **Task:** Add actions to `menu_settings`.
  - **C reference:** `src/interface.c` → `create_actions_and_menu()`,
    `src/term_config.c` → `Config_Port_Fenetre()`, `Config_Terminal()`
  - **Python file:** `pyterm/main_window.py` → `_setup_menubar()` Settings section
  - **Actions to add:**
    - Port configuration → `self._on_show_port_config_dialog`
    - Terminal settings  → `self._on_show_terminal_config_dialog`
    - Separator
    - Load configuration → stub `pass`
    - Save configuration → stub `pass`
    - Delete configuration → stub `pass`
    - Separator
    - Load macro file → stub `pass`
    - Save macro file → stub `pass`

### 4.6 – Populate Log menu
- [ ] **Task:** Add actions to `menu_log`.
  - **C reference:** `src/interface.c` → `create_actions_and_menu()` (Log menu),
    `src/logging.h` → `logging_start()`, `logging_pause_resume()`, `logging_stop()`
  - **Python file:** `pyterm/main_window.py` → `_setup_menubar()` Log section
  - **Actions to add:**
    - Log to file     → stub `pass`
    - Pause / Resume  → stub `pass`  (label must toggle, see `toggle_logging_pause_resume`)
    - Stop            → stub `pass`
    - Clear log       → stub `pass`

### 4.7 – Populate Signals menu
- [ ] **Task:** Add actions to `menu_signals`.
  - **C reference:** `src/interface.c` → `create_actions_and_menu()` (Signals menu)
  - **Python file:** `pyterm/main_window.py` → `_setup_menubar()` Signals section
  - **Actions to add:**
    - Send Break  → `self._on_send_break`
    - Toggle DTR  → `self._on_toggle_dtr`
    - Toggle RTS  → `self._on_toggle_rts`

### 4.8 – Populate Help menu
- [ ] **Task:** Add About action.
  - **C reference:** `src/interface.c` → `help_about_callback()`
  - **Python file:** `pyterm/main_window.py` → `_setup_menubar()` Help section
  - **Logic:** `menu_help.addAction("About", self._on_about)`

---

## Phase 5 – Main Window: Port Control

### 5.1 – `_on_open_port()` – open port from GUI
- [ ] **Task:** Implement the Open Port action.
  - **C reference:** `src/interface.c` → `interface_open_port()`,
    `signals_open_port()`
  - **Python file:** `pyterm/main_window.py` → `_on_open_port()`
  - **Logic:**
    ```python
    from PySide6.QtCore import QMetaObject, Qt
    QMetaObject.invokeMethod(
        self._worker, "open_port",
        Qt.ConnectionType.QueuedConnection,
        self._config.port,
    )
    self._worker.start()   # start the thread if not running
    ```

### 5.2 – `_on_close_port()`
- [ ] **Task:** Implement the Close Port action.
  - **C reference:** `src/interface.c` → `interface_close_port()`
  - **Python file:** `pyterm/main_window.py` → `_on_close_port()`
  - **Logic:**
    ```python
    QMetaObject.invokeMethod(self._worker, "close_port",
                             Qt.ConnectionType.QueuedConnection)
    ```

### 5.3 – `_on_port_opened()` – enable UI
- [ ] **Task:** Enable port-dependent actions and start the poll timer.
  - **C reference:** `src/interface.c` → `interface_open_port()`,
    `Set_status_message()`, `Set_window_title()`
  - **Python file:** `pyterm/main_window.py` → `_on_port_opened()`
  - **Logic:**
    1. `self._status_label.setText(status)`
    2. `self.setWindowTitle(f"pyterm – {status}")`
    3. Enable Send Break, Toggle DTR, Toggle RTS actions.
    4. `self._signal_poll_timer.start()`

### 5.4 – `_on_port_closed()` – disable UI
- [ ] **Task:** Grey out port-dependent actions on close.
  - **C reference:** `src/interface.c` → `interface_close_port()`
  - **Python file:** `pyterm/main_window.py` → `_on_port_closed()`
  - **Logic:**
    1. `self._signal_poll_timer.stop()`
    2. `self._status_label.setText("Port closed")`
    3. `self.setWindowTitle("pyterm")`
    4. Disable Send Break, Toggle DTR, Toggle RTS actions.
    5. Reset all LED labels to inactive style.

---

## Phase 6 – Main Window: Display (`pyterm/main_window.py`)

### 6.1 – `_on_clear_display()`
- [ ] **Task:** Clear the terminal view.
  - **C reference:** `src/interface.c` → `clear_display()`,
    `src/buffer.c` → `clear_buffer()`
  - **Python file:** `pyterm/main_window.py` → `_on_clear_display()`
  - **Logic:**
    ```python
    self._terminal_view.clear()
    self._total_bytes = 0      # reset hex-view byte counter
    self._virt_col_pos = 0     # reset hex-view column tracker
    ```

### 6.2 – `_put_text()` – ASCII rendering
- [ ] **Task:** Implement ASCII byte-stream display.
  - **C reference:** `src/interface.c` → `put_text()` (search for the function)
  - **Python file:** `pyterm/main_window.py` → `_put_text()`
  - **Logic (step by step):**
    1. Decode `data` as Latin-1 (never fails on arbitrary bytes).
    2. If `self._crlfauto`: replace bare `\n` (not preceded by `\r`) with `\r\n`.
    3. If `self._esc_clear_screen`: on `\x1b` character call `self._on_clear_display()`.
    4. If `self._timestamp`: prepend `datetime.now().strftime("[%H:%M:%S.%f] ")`
       to each line.
    5. Move the cursor to the end of `self._terminal_view` and `insertPlainText`.
    6. Scroll to the bottom with `self._terminal_view.ensureCursorVisible()`.

### 6.3 – Add internal state variables for hex view
- [ ] **Task:** Add instance variables for the hex-display state.
  - **C reference:** `src/interface.c` → `bytes_per_line`, `total_bytes`,
    `virt_col_pos`, `show_index`
  - **Python file:** `pyterm/main_window.py` → `__init__()` (after the config lines)
  - **Add:**
    ```python
    self._bytes_per_line: int  = 16
    self._total_bytes:    int  = 0
    self._virt_col_pos:   int  = 0
    self._show_index:     bool = False
    self._esc_clear_screen: bool = app_config.port.esc_clear_screen
    ```

### 6.4 – `_put_hexadecimal()` – hex dump rendering
- [ ] **Task:** Implement hex dump display.
  - **C reference:** `src/interface.c` → `put_hexadecimal()`.
    Pay close attention to the `virt_col_pos` tracking and blank-padding logic.
  - **Python file:** `pyterm/main_window.py` → `_put_hexadecimal()`
  - **Logic outline:**
    ```
    for each byte b in data:
        if self._virt_col_pos == 0 and self._show_index:
            append "  {self._total_bytes:08X}  " to line
        append "{b:02X} " to hex part
        append chr(b) if 0x20 <= b < 0x7F else '.' to ascii part
        self._virt_col_pos += 1
        self._total_bytes  += 1
        if self._virt_col_pos == self._bytes_per_line:
            flush line (hex + "  " + ascii + "\n") to terminal view
            self._virt_col_pos = 0
    ```

### 6.5 – `_on_data_received()` – dispatch to correct renderer
- [ ] **Task:** Route received data to the correct display function.
  - **C reference:** `src/interface.c` → `put_chars()` in `src/buffer.c`,
    `set_display_func()`, `put_text()` / `put_hexadecimal()`
  - **Python file:** `pyterm/main_window.py` → `_on_data_received()`
  - **Logic:**
    ```python
    if self._view_mode == ViewMode.ASCII:
        self._put_text(data)
    else:
        self._put_hexadecimal(data)
    # TODO (Phase 8): also pass data to the logging subsystem
    ```

### 6.6 – `set_view()` – switch display mode
- [ ] **Task:** Implement view-mode switching.
  - **C reference:** `src/interface.c` → `set_view()`
  - **Python file:** `pyterm/main_window.py` → `set_view()`
  - **Logic:**
    ```python
    self._view_mode = mode
    self._on_clear_display()
    # Toggle action checked states:
    self._action_ascii_view.setChecked(mode == ViewMode.ASCII)
    self._action_hex_view.setChecked(mode == ViewMode.HEXADECIMAL)
    # Enable/disable hex-only menu items:
    show_index_action.setEnabled(mode == ViewMode.HEXADECIMAL)
    ```

### 6.7 – `_apply_config_to_ui()`
- [ ] **Task:** Sync UI toggles to the loaded config.
  - **C reference:** `src/term_config.c` → `ConfigFlags()`,
    `src/interface.c` → `Set_local_echo()`, `Set_crlfauto()`, `Set_timestamp()`
  - **Python file:** `pyterm/main_window.py` → `_apply_config_to_ui()`
  - **Logic:**
    ```python
    self._action_echo.setChecked(self._config.port.echo)
    self._action_crlfauto.setChecked(self._config.port.crlfauto)
    self._terminal_view.setFont(QFont(self._config.display.font))
    # Apply foreground/background colours to terminal_view palette
    ```

---

## Phase 7 – Configuration Dialogs (`pyterm/main_window.py`)

### 7.1 – Port configuration dialog
- [ ] **Task:** Build `_on_show_port_config_dialog()` as a `QDialog`.
  - **C reference:** `src/term_config.c` → `Config_Port_Fenetre()` (lines ~441-797)
  - **Python file:** `pyterm/main_window.py` → `_on_show_port_config_dialog()`
  - **Widgets to create (one-to-one with the GTK grid):**
    - Transport type combo (Serial / TCP Client / TCP Server)
    - TCP frame: Host entry, Port entry (shown only for TCP types)
    - Serial frame: Port combo+entry, Baud rate combo+entry, Parity combo,
      Bits combo, Stop bits combo, Flow control combo
    - Advanced expander:
      - End-of-line delay spin (0–500 ms)
      - Wait-for-char checkbox + char entry
      - RS-485 RTS-before spin, RTS-after spin
    - OK / Cancel buttons
  - On OK: copy dialog values into `self._config.port` and call
    `self._worker.apply_config(self._config.port)`.

### 7.2 – Terminal / display configuration dialog
- [ ] **Task:** Build `_on_show_terminal_config_dialog()` as a `QDialog`.
  - **C reference:** `src/term_config.c` → `Config_Terminal()` (search for it
    in term_config.c)
  - **Python file:** `pyterm/main_window.py` → `_on_show_terminal_config_dialog()`
  - **Widgets to create:**
    - Font chooser button (QFontDialog)
    - Foreground colour button (QColorDialog) → `self._config.display.foreground_color`
    - Background colour button (QColorDialog) → `self._config.display.background_color`
    - Block cursor checkbox
    - Rows / Columns spin boxes
    - Scrollback spin box
    - Visual bell checkbox
  - On OK: apply font and colours to `self._terminal_view`.

---

## Phase 8 – Logging (`pyterm/main_window.py`)

- [ ] **8.1 – Implement `_on_log_to_file()`**
  - **C reference:** `src/logging.c` → `logging_start()`
  - Open a `QFileDialog` to choose a log path.
  - Open the file in append mode.
  - Store the file handle; set a flag `self._logging_active = True`.

- [ ] **8.2 – Feed received data to the log**
  - **C reference:** `src/logging.c` → `log_chars()`
  - In `_on_data_received()`, after rendering, write raw bytes to the log
    file if `self._logging_active` is True.

- [ ] **8.3 – Implement Pause/Resume**
  - **C reference:** `src/logging.c` → `logging_pause_resume()`
  - Toggle `self._logging_paused`. Update menu item label
    ("Pause" ↔ "Resume"). Reference: `src/interface.c` `toggle_logging_pause_resume()`.

- [ ] **8.4 – Implement Stop**
  - **C reference:** `src/logging.c` → `logging_stop()`
  - Close the log file handle. Set `self._logging_active = False`.
  - Re-enable the "Log to file" action; disable Pause/Resume/Stop/Clear.

- [ ] **8.5 – Implement Clear Log**
  - **C reference:** `src/logging.c` → `logging_clear()`
  - Truncate the open log file to zero bytes.

---

## Phase 9 – Macro Panel (`pyterm/main_window.py`)

### 9.1 – Parse macro config
- [ ] **Task:** Load macros from the config and populate `self._config.macros`.
  - **C reference:** `src/macros.c` → `macros_file_load()`,
    `src/term_config.c` → `load_macros_file_callback()`
  - **Python file:** `pyterm/config.py` → extend `load_config()` to also
    parse macro entries from the config file or a separate JSON/INI macros file.

### 9.2 – `rebuild_macro_panel()`
- [ ] **Task:** Replace the placeholder in `_setup_macro_dock()` with a real panel.
  - **C reference:** `src/interface.c` → `rebuild_macro_buttons()` (lines ~799+)
  - **Python file:** `pyterm/main_window.py`
  - **Logic:**
    1. Create a `QTabWidget`.
    2. Group `self._config.macros` by `MacroConfig.tab`.
    3. For each group, create a `QScrollArea` containing a `QVBoxLayout`.
    4. For each macro, create a `QPushButton` with `macro.label`.
    5. Connect `clicked` → a lambda that calls `self._send_macro(macro)`.
    6. Right-click → context menu with "Polling Mode" toggle and period entry
       (mirrors `on_macro_button_right_click()` in interface.c).
    7. Set `self._macro_dock.setWidget(tab_widget)`.

### 9.3 – `_send_macro()`
- [ ] **Task:** Implement macro sending.
  - **C reference:** `src/macros.c` → `shortcut_callback()`,
    `send_macro_with_args()`
  - **Python file:** `pyterm/main_window.py`
  - **Logic:**
    1. Unescape the `macro.action` string (handle `\n`, `\r`, `\x..` escapes).
    2. Substitute any `%s`, `%d` format placeholders with `macro.args` values.
    3. Call `self._worker.send_bytes(action.encode("latin-1"))`.

### 9.4 – Macro polling
- [ ] **Task:** Implement periodic macro sending.
  - **C reference:** `src/interface.c` → `polling_timer_callback()`,
    `macro_polling_t`, `toggle_polling_run()`
  - **Python file:** `pyterm/main_window.py`
  - **Logic:**
    - Add a `QTimer` per polling macro.
    - On enable: `timer.start(macro.polling_period_ms)`.
    - On timeout: call `self._send_macro(macro)`.
    - Visual indicator: toggle button style (blinking when running).

---

## Phase 10 – Hex Send Bar (`pyterm/main_window.py`)

- [ ] **10.1 – Build the hex send bar widget**
  - **C reference:** `src/interface.c` → `Hex_Box`, `Send_Hexadecimal()`,
    `hex_history`, `on_key_press()`
  - Replace the stub in `_setup_hex_send_bar()` with a real `QWidget`:
    - `QLineEdit` (hex input) + `QPushButton("Send")`
    - Place in a `QHBoxLayout` inside a `QWidget` added as a dock or
      as the bottom part of a `QSplitter`.

- [ ] **10.2 – Implement hex parsing and send**
  - **C reference:** `src/interface.c` → `Send_Hexadecimal()`
  - Parse the QLineEdit text as space/comma-separated hex bytes.
  - Example: `"41 42 0A"` → `b"\x41\x42\x0A"`.
  - Call `self._worker.send_bytes(parsed_bytes)`.

- [ ] **10.3 – Implement hex input history**
  - **C reference:** `src/interface.c` → `hex_history`, `current_hex`,
    `update_hex_history()`, `set_saved_data()`
  - Store a `list[str]` history of sent hex strings.
  - Up/Down arrow keys in the QLineEdit navigate the history.
  - Mirrors the GList-based `hex_history` / `current_hex` in interface.c.

---

## Phase 11 – Status Bar & Signal LEDs (`pyterm/main_window.py`)

- [ ] **11.1 – Style the LED labels**
  - **C reference:** `src/interface.c` → `control_signals_read()`,
    `signals[6]` array
  - Apply QSS to `self._signal_labels`:
    ```python
    INACTIVE_STYLE = "background: #555; color: white; border-radius: 3px; padding: 2px;"
    ACTIVE_STYLE   = "background: #00cc44; color: black; border-radius: 3px; padding: 2px;"
    ```

- [ ] **11.2 – `_on_control_signals_changed()` – update LEDs**
  - **C reference:** `src/interface.c` → `control_signals_read()`
  - Decode the bitmask (using the same bit positions as `transport_get_signals()`
    in `src/transport.c`) and apply the correct style to each LED label.

---

## Phase 12 – Command-line Arguments (`main.py`)

- [ ] **12.1 – Implement `parse_args()`**
  - **C reference:** `src/cmdline.c` → the `GOptionEntry` table
  - **Python file:** `main.py` → `parse_args()`
  - Use `argparse.ArgumentParser`.
  - Flags to add (map names from the C source):
    | Flag              | Short | Type  | Destination        |
    |-------------------|-------|-------|--------------------|
    | `--port`          | `-p`  | str   | `port`             |
    | `--baud`          | `-s`  | int   | `baudrate`         |
    | `--bits`          | `-b`  | int   | `bits`             |
    | `--parity`        | `-a`  | str   | `parity`           |
    | `--stopbits`      | `-t`  | int   | `stopbits`         |
    | `--flow`          | `-f`  | str   | `flow`             |
    | `--echo`          | `-e`  | flag  | `echo`             |
    | `--noportlock`    | –     | flag  | `disable_port_lock`|
    | `--config`        | `-c`  | str   | `active_section`   |

- [ ] **12.2 – Implement `apply_cli_overrides()`**
  - **C reference:** `src/term_config.c` → `Verify_configuration()`
  - For each non-None value in `overrides`, set the corresponding attribute
    on `cfg.port`.

---

## Phase 13 – Shutdown & Config Save (`pyterm/main_window.py`)

- [ ] **13.1 – Implement `closeEvent()`**
  - **C reference:** `src/gtkterm.c` → application teardown
  - **Python file:** `pyterm/main_window.py` → `closeEvent()`
  - **Logic:**
    1. Call `self._worker.close_port()` synchronously or via
       `invokeMethod` + `wait()`.
    2. Call `save_config(self._config)` from `pyterm.config`.
    3. `event.accept()`.

---

## Phase 14 – ASCII File Transfer (`pyterm/main_window.py`)

- [ ] **14.1 – Send ASCII file**
  - **C reference:** `src/files.c` → `send_raw_file()` (or equivalent)
  - Open a `QFileDialog` to choose a text file.
  - Read lines; for each line, call `self._worker.send_bytes(line.encode())`.
  - Respect `self._config.port.delay_ms` between lines (use `QTimer.singleShot`
    so the GUI stays responsive).
  - Respect `self._config.port.wait_char` (send next line only after that
    byte is received).

---

## Phase 15 – Search Bar (`pyterm/main_window.py`)

- [ ] **15.1 – Implement Find in terminal view**
  - **C reference:** `src/search.c` / `src/search.h` → `search_for_text()`
  - Add a `QToolBar` or inline search widget that calls
    `self._terminal_view.find(text)` (QPlainTextEdit built-in).

---

## Final Checks

- [ ] **F.1 – Run the application end-to-end**
  ```bash
  python main.py
  ```
  The window must open without tracebacks.

- [ ] **F.2 – Open a real serial port**
  Connect a USB-serial adapter. Use port config dialog to set the port.
  Verify data flows in ASCII view and hex view.

- [ ] **F.3 – Verify High-DPI rendering**
  Run on a HiDPI display (or set `QT_SCALE_FACTOR=2`). Confirm crisp rendering.

- [ ] **F.4 – Delete original C source tree** *(Senior approval required)*
  ```bash
  git rm -r src/
  git rm meson.build data/meson.build po/meson.build
  git commit -m "chore: remove legacy C source after Python migration"
  ```
  > **Do NOT execute this step without explicit sign-off from the Senior architect.**
