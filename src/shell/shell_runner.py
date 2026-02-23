"""
Runs a real Windows shell (cmd.exe) in a subprocess and exposes a line buffer
plus write(line) for the UI to drive a real terminal.
Supports optional PTY (pseudo-terminal) mode so SSH and other TTY programs work.

Debug: set env ROBCO_SHELL_DEBUG=1 to log raw PTY data and line processing to stderr.
"""
import os
import re
import subprocess
import sys
import threading
import logging

logger = logging.getLogger(__name__)
if os.environ.get("ROBCO_SHELL_DEBUG"):
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        h = logging.StreamHandler(sys.stderr)
        h.setFormatter(logging.Formatter("%(asctime)s [shell] %(message)s"))
        logger.addHandler(h)

# Strip ANSI escape sequences so prompts (e.g. SSH password) and text are visible
# instead of raw codes like [1:35H, [?1004h. Covers CSI, OSC, and common two-byte.
# OSC (e.g. window title) must end with BEL or ST so the full sequence is removed.
_ANSI_ESCAPE = re.compile(
    r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\][^\x1b]*(?:\x07|\x1b\\))"
)
# C0 control characters (incl. BEL 0x07) to strip from visible output
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _strip_ansi(text):
    if not text:
        return text
    return _ANSI_ESCAPE.sub("", text)


def _visible_line(text):
    """Apply \\r semantics: take the part after the last \\r (in-place overwrite).
    If that part is empty (e.g. password prompt ending with \\r), show the full line.
    Strips ANSI, then C0 control chars (e.g. BEL), so only printable content is shown.
    """
    if not text:
        return ""
    s = _strip_ansi(text).rstrip("\r\n")
    after_last_r = s.split("\r")[-1]
    visible = after_last_r if after_last_r else s
    return _CONTROL_CHARS.sub("", visible)


class ShellRunner:
    """
    Spawns a shell process, reads stdout/stderr into a thread-safe line buffer,
    and provides write(line) to send input. No UI dependency.
    When use_pty is True on Windows, uses a PTY so SSH and similar programs work.
    """

    def __init__(self, shell_command=None, shell_cwd=None, use_pty=True):
        if shell_command is None:
            shell_command = "cmd.exe"
        if isinstance(shell_command, str):
            self._argv = [shell_command, "/q", "/k"]
        else:
            self._argv = list(shell_command)
        self._cwd = shell_cwd or os.getcwd()
        self._lines = []
        self._lock = threading.Lock()
        self._process = None
        self._pty = None
        self._reader_thread = None
        self._encoding = "utf-8"
        self._errors = "replace"
        self._history = []
        self._history_index = -1
        self._history_max = 50
        self._use_pty = False
        self._pending = ""  # in-progress line (no \\n yet); \\r updates apply here

        if use_pty and sys.platform == "win32":
            try:
                import winpty

                # Pass full argv (e.g. ["cmd.exe", "/q", "/k"]) so cmd starts quiet
                # and doesn't print delayed Microsoft banner lines
                self._pty = winpty.PtyProcess.spawn(
                    self._argv, cwd=self._cwd, dimensions=(24, 80)
                )
                self._pty.setwinsize(24, 80)
                self._use_pty = True
                self._reader_thread = threading.Thread(
                    target=self._read_loop_pty, daemon=True
                )
                self._reader_thread.start()
            except Exception:
                self._use_pty = False
                self._pty = None
                self._start_pipe()
        else:
            self._start_pipe()

    def _start_pipe(self):
        kwargs = {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "bufsize": 0,
            "cwd": self._cwd,
        }
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        self._process = subprocess.Popen(self._argv, **kwargs)
        self._reader_thread = threading.Thread(target=self._read_loop_pipe, daemon=True)
        self._reader_thread.start()

    def _read_loop_pipe(self):
        out = self._process.stdout if self._process else None
        if out is None:
            return
        buffer = b""
        try:
            while True:
                chunk = out.read(4096)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line_bytes, _, buffer = buffer.partition(b"\n")
                    decoded = line_bytes.decode(
                        self._encoding, errors=self._errors
                    )
                    visible = _visible_line(decoded)
                    if visible:
                        with self._lock:
                            self._lines.append(visible)
                with self._lock:
                    self._pending = buffer.decode(
                        self._encoding, errors=self._errors
                    )
        except (OSError, ValueError):
            pass
        finally:
            if buffer.strip():
                visible = _visible_line(
                    buffer.decode(self._encoding, errors=self._errors)
                )
                if visible:
                    with self._lock:
                        self._lines.append(visible)
                with self._lock:
                    self._pending = ""

    def _read_loop_pty(self):
        if self._pty is None:
            return
        buffer = ""
        try:
            while self._pty.isalive():
                try:
                    data = self._pty.read(4096)
                except (EOFError, OSError, ValueError):
                    break
                if not data:
                    break
                if isinstance(data, bytes):
                    data = data.decode(self._encoding, errors=self._errors)
                logger.debug("pty raw: %r", data)
                buffer += data
                while "\n" in buffer:
                    line, _, buffer = buffer.partition("\n")
                    visible = _visible_line(line)
                    logger.debug("pty line: %r -> visible: %r", line, visible)
                    if visible:
                        with self._lock:
                            self._lines.append(visible)
                            self._pending = buffer
                    else:
                        with self._lock:
                            self._pending = buffer
                    logger.debug("pty pending: %r", buffer)
                if buffer and "\n" not in buffer:
                    logger.debug("pty pending (no newline yet): %r", buffer)
                    with self._lock:
                        self._pending = buffer
        except Exception:
            pass
        finally:
            if buffer.strip():
                visible = _visible_line(buffer)
                if visible:
                    with self._lock:
                        self._lines.append(visible)
                with self._lock:
                    self._pending = ""

    def get_output_lines(self):
        """Return a copy of the current output lines plus the pending line (if any)."""
        with self._lock:
            out = list(self._lines)
            if self._pending:
                out.append(_visible_line(self._pending))
            return out

    def write(self, line):
        """Send a line to the shell (adds newline if missing)."""
        cmd = line.strip().rstrip("\n")
        if cmd:
            self._history.append(cmd)
            if len(self._history) > self._history_max:
                self._history.pop(0)
            self._history_index = -1
        if not line.endswith("\n"):
            line = line + "\n"
        if self._use_pty and self._pty is not None:
            try:
                to_send = line if line.endswith("\r\n") else line.replace("\n", "\r\n")
                if isinstance(to_send, bytes):
                    to_send = to_send.decode(self._encoding, errors=self._errors)
                self._pty.write(to_send)
            except (OSError, BrokenPipeError, ValueError):
                pass
            return
        if self._process is None or self._process.stdin is None:
            return
        try:
            self._process.stdin.write(
                line.encode(self._encoding, errors=self._errors)
            )
            self._process.stdin.flush()
        except (OSError, BrokenPipeError, ValueError):
            pass

    def history_prev(self):
        """Return the previous command in history, or None if at top or empty."""
        if not self._history:
            return None
        if self._history_index <= 0:
            self._history_index = 0
            return self._history[0]
        self._history_index -= 1
        return self._history[self._history_index]

    def history_next(self):
        """Return the next command in history; '' when moving to bottom (empty line). None if already at bottom."""
        if self._history_index < 0:
            return None
        if self._history_index >= len(self._history) - 1:
            self._history_index = -1
            return ""
        self._history_index += 1
        return self._history[self._history_index]

    def send_interrupt(self):
        """Send Ctrl+C to the shell process."""
        if self._use_pty and self._pty is not None:
            try:
                self._pty.write("\x03")
            except (OSError, BrokenPipeError, ValueError):
                pass
            return
        if self._process is None or self._process.stdin is None:
            return
        try:
            self._process.stdin.write(b"\x03")
            self._process.stdin.flush()
        except (OSError, BrokenPipeError, ValueError):
            pass

    def setwinsize(self, rows, cols):
        """Set the PTY terminal size (rows, cols). No-op in pipe mode. Call when
        the shell scene is shown so programs like SSH get the size and show prompts.
        """
        if self._use_pty and self._pty is not None:
            try:
                self._pty.setwinsize(rows, cols)
            except Exception:
                pass

    def is_alive(self):
        """True if the shell process is still running."""
        if self._use_pty and self._pty is not None:
            try:
                return self._pty.isalive()
            except Exception:
                return False
        return (
            self._process is not None and self._process.poll() is None
        )
