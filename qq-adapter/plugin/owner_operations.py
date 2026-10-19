"""Explicit host operations; the calling adapter must authorize every entry.

No message parsing, QQ identity claims, permission escalation or directory
allowlist belongs here. Operations use the existing Windows user's rights.
"""
from __future__ import annotations

import base64
import codecs
import ctypes
from datetime import datetime, timezone
import math
import os
from pathlib import Path
import select
import shutil
import subprocess
import time
from typing import Any



class OwnerOperations:
    """Bounded file and PowerShell operations after external authorization."""

    def __init__(self, workspace: str | Path, *,
                 max_output_chars: int = 12000, max_read_chars: int = 12000,
                 max_list_entries: int = 200, default_timeout: float = 30,
                 max_timeout: float = 120):
        self.workspace = self._absolute_path(workspace)
        self.max_output_chars = self._positive_int(max_output_chars, "max_output_chars")
        self.max_read_chars = self._positive_int(max_read_chars, "max_read_chars")
        self.max_list_entries = self._positive_int(max_list_entries, "max_list_entries")
        self.max_timeout = self._positive_seconds(max_timeout, "max_timeout")
        self.default_timeout = self._positive_seconds(default_timeout, "default_timeout")
        if self.default_timeout > self.max_timeout:
            raise ValueError("default_timeout exceeds max_timeout")

    @staticmethod
    def _absolute_path(path: str | Path) -> Path:
        if not isinstance(path, (str, Path)) or not str(path).strip():
            raise ValueError("An explicit absolute path is required")
        value = Path(path).expanduser()
        if not value.is_absolute():
            raise ValueError("An explicit absolute path is required")
        return Path(os.path.abspath(value))

    @staticmethod
    def _positive_int(value: int, name: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(name + " must be a positive integer")
        return value

    @staticmethod
    def _positive_seconds(value: float, name: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(name + " must be finite and positive")
        return float(value)

    def _limit(self, value: int | None, maximum: int, name: str) -> int:
        limit = maximum if value is None else self._positive_int(value, name)
        if limit > maximum:
            raise ValueError(name + " exceeds configured maximum")
        return limit

    def read_text(self, path: str | Path, *, max_chars: int | None = None,
                  encoding: str = "utf-8") -> dict[str, Any]:
        target = self._absolute_path(path)
        limit = self._limit(max_chars, self.max_read_chars, "max_chars")
        with target.open("r", encoding=encoding, newline="") as stream:
            content = stream.read(limit + 1)
        return {"ok": True, "action": "read_text", "path": str(target),
                "text": content[:limit], "truncated": len(content) > limit,
                "encoding": encoding, "size_bytes": target.stat().st_size,
                "limit_chars": limit}

    def list_dir(self, path: str | Path, *, limit: int | None = None) -> dict[str, Any]:
        target = self._absolute_path(path)
        count = self._limit(limit, self.max_list_entries, "limit")
        entries: list[dict[str, Any]] = []
        truncated = False
        with os.scandir(target) as iterator:
            for entry in iterator:
                if len(entries) >= count:
                    truncated = True
                    break
                item: dict[str, Any] = {"name": entry.name, "path": entry.path}
                try:
                    stat = entry.stat(follow_symlinks=False)
                    item.update(type="symlink" if entry.is_symlink() else "directory" if entry.is_dir(follow_symlinks=False) else "file",
                                size_bytes=stat.st_size,
                                modified_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat())
                except OSError as exc:
                    item.update(type="unavailable", error=type(exc).__name__)
                entries.append(item)
        entries.sort(key=lambda item: (item["type"] != "directory", item["name"].casefold()))
        return {"ok": True, "action": "list_dir", "path": str(target),
                "entries": entries, "truncated": truncated, "limit_entries": count}

    def write_text(self, path: str | Path, text: str, *, append: bool = False,
                   encoding: str = "utf-8") -> dict[str, Any]:
        target = self._absolute_path(path)
        if not isinstance(text, str):
            raise TypeError("text must be str")
        if not isinstance(append, bool):
            raise TypeError("append must be bool")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a" if append else "w", encoding=encoding, newline="") as stream:
            written = stream.write(text)
        return {"ok": True, "action": "write_text", "path": str(target),
                "append": append, "characters_written": written,
                "size_bytes": target.stat().st_size, "encoding": encoding}

    @staticmethod
    def _hidden_options() -> dict[str, Any]:
        if os.name != "nt":
            return {"start_new_session": True}
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = subprocess.SW_HIDE
        return {"startupinfo": startup,
                "creationflags": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP}

    @staticmethod
    def _powershell() -> str:
        for executable in ("powershell.exe", "pwsh.exe", "pwsh", "powershell"):
            located = shutil.which(executable)
            if located:
                return located
        raise FileNotFoundError("PowerShell is not available in this Windows user environment")

    @staticmethod
    def _read_available(stream: Any) -> tuple[bytes, bool]:
        """Drain only available pipe bytes; background children cannot block us."""
        if os.name == "nt":
            import msvcrt
            available = ctypes.c_ulong(0)
            handle = ctypes.c_void_p(msvcrt.get_osfhandle(stream.fileno()))
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            if not kernel.PeekNamedPipe(handle, None, 0, None, ctypes.byref(available), None):
                error = ctypes.get_last_error()
                if error in (109, 232, 233):  # broken or disconnected pipe
                    return b"", True
                raise OSError(error, "Unable to read process output")
            if available.value == 0:
                return b"", False
            data = os.read(stream.fileno(), min(available.value, 65536))
        else:
            if not select.select([stream], [], [], 0)[0]:
                return b"", False
            data = os.read(stream.fileno(), 65536)
        return data, not data

    def _terminate_tree(self, process: subprocess.Popen[bytes]) -> None:
        if process.poll() is not None:
            return
        if os.name == "nt":
            try:
                subprocess.run(["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=2, **self._hidden_options())
            except (OSError, subprocess.TimeoutExpired):
                pass
        else:
            import signal
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if process.poll() is None:
            process.kill()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass

    def run_command(self, command: str, *, cwd: str | Path | None = None,
                    timeout: float | None = None,
                    max_output_chars: int | None = None) -> dict[str, Any]:
        if not isinstance(command, str) or not command.strip():
            raise ValueError("An explicit nonempty PowerShell command is required")
        working = self._absolute_path(cwd) if cwd is not None else self.workspace
        if cwd is None:
            working.mkdir(parents=True, exist_ok=True)
        elif not working.is_dir():
            raise NotADirectoryError(str(working))
        seconds = self.default_timeout if timeout is None else self._positive_seconds(timeout, "timeout")
        if seconds > self.max_timeout:
            raise ValueError("timeout exceeds configured maximum")
        limit = self._limit(max_output_chars, self.max_output_chars, "max_output_chars")
        # EncodedCommand preserves arbitrary explicit command text as one argv
        # value. No shell quoting, profile loading, policy bypass or elevation.
        script = ("[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)\n"
                  "$OutputEncoding = [Console]::OutputEncoding\n"
                  "$PSDefaultParameterValues['Start-Process:WindowStyle'] = 'Hidden'\n" + command)
        encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        argv = [self._powershell(), "-NoLogo", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded]
        started = time.monotonic()
        process = subprocess.Popen(argv, cwd=str(working), stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   bufsize=0, **self._hidden_options())
        decoder = codecs.getincrementaldecoder("utf-8")("replace")
        parts: list[str] = []
        captured = 0
        truncated = timed_out = False
        exit_seen: float | None = None

        def capture(data: bytes, final: bool = False) -> None:
            nonlocal captured, truncated
            value = decoder.decode(data, final=final)
            remaining = limit - captured
            if len(value) > remaining:
                truncated = True
            if remaining > 0:
                parts.append(value[:remaining])
                captured += min(len(value), remaining)

        try:
            assert process.stdout is not None
            while True:
                now = time.monotonic()
                code = process.poll()
                if code is None and not timed_out and now - started >= seconds:
                    timed_out = True
                    self._terminate_tree(process)
                    code = process.poll()
                    exit_seen = now
                if code is not None and exit_seen is None:
                    exit_seen = now
                if exit_seen is not None and now - exit_seen >= .25:
                    truncated = True
                    break
                chunk, eof = self._read_available(process.stdout)
                if chunk:
                    capture(chunk)
                    continue
                if code is not None or eof and timed_out:
                    break
                if timed_out:
                    break
                time.sleep(.01)
            capture(b"", final=True)
        except BaseException:
            self._terminate_tree(process)
            raise
        finally:
            if process.stdout is not None:
                process.stdout.close()
        return {"ok": not timed_out and process.returncode == 0,
                "action": "run_command", "cwd": str(working), "text": "".join(parts),
                "exit_code": process.returncode, "timed_out": timed_out,
                "truncated": truncated, "limit_chars": limit,
                "timeout_seconds": seconds, "duration_seconds": round(time.monotonic() - started, 3)}
