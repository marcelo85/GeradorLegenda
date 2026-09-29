from contextlib import redirect_stdout
import importlib
import os
import shutil
import sys
import time
from threading import Event, Lock, Thread
from types import SimpleNamespace


class WhisperProgressDisplay:
    """Renderiza o progresso do Whisper no topo do console."""

    def __init__(self):
        self.stream = sys.stdout
        self.total = 0
        self.current = 0
        self.started_at = 0.0
        self.ide_console = os.environ.get("PYCHARM_HOSTED") == "1"
        self.terminal = self.stream.isatty() and os.environ.get("TERM") != "dumb"
        self.rows = shutil.get_terminal_size((80, 24)).lines
        self.finished = False
        self._refresh_stop = Event()
        self._write_lock = Lock()
        self._refresh_thread = None
        self._ide_status_visible = False

    def start(self, total):
        self.total = total
        self.started_at = time.monotonic()
        if self.terminal or self.ide_console:
            with self._write_lock:
                if self.terminal:
                    self.stream.write(f"\033[2;{self.rows}r\033[1;1H")
                self._render_locked()
                if self.terminal:
                    self.stream.write("\033[2;1H")
                self.stream.flush()
            self._refresh_thread = Thread(target=self._refresh_clock, daemon=True)
            self._refresh_thread.start()
        else:
            self._render()

    def update(self, amount):
        with self._write_lock:
            self.current += amount
            self._render_locked()
            self.stream.flush()

    def _render(self):
        with self._write_lock:
            self._render_locked()

    def _render_locked(self):
        percent = min(100, self.current * 100 / self.total) if self.total else 0
        elapsed_seconds = max(0, int(time.monotonic() - self.started_at))
        elapsed_hours, elapsed_remainder = divmod(elapsed_seconds, 3600)
        elapsed_minutes, elapsed_seconds = divmod(elapsed_remainder, 60)
        elapsed = (
            f"{elapsed_hours:02d}:{elapsed_minutes:02d}:{elapsed_seconds:02d}"
        )
        bar_length = 32
        filled = int(bar_length * percent / 100)
        header = (
            f"Transcrição [{('=' * filled) + ('-' * (bar_length - filled))}] "
            f"{percent:5.1f}% ({self.current}/{self.total} frames)"
            f"  Decorrido: {elapsed}"
        )
        if self.terminal:
            self.stream.write(f"\033[s\033[1;1H{header}\033[K\033[u")
        elif self.ide_console:
            self.stream.write(f"\r{header}")
            self._ide_status_visible = True
        else:
            self.stream.write(header + "\n")

    def _refresh_clock(self):
        while not self._refresh_stop.wait(1):
            with self._write_lock:
                if self.finished:
                    return
                self._render_locked()
                self.stream.flush()

    def write(self, text):
        with self._write_lock:
            if self.ide_console and self._ide_status_visible:
                self.stream.write("\n")
                self._ide_status_visible = False
            self.stream.write(text)
            if self.ide_console and text.endswith("\n"):
                self._render_locked()
        return len(text)

    def flush(self):
        with self._write_lock:
            self.stream.flush()

    def finish(self):
        self._refresh_stop.set()
        if self._refresh_thread is not None:
            self._refresh_thread.join()
        with self._write_lock:
            if self.finished:
                return
            self.finished = True
            if self.terminal:
                self.stream.write(f"\033[r\033[{self.rows};1H\n")
            elif self.ide_console and self._ide_status_visible:
                self.stream.write("\n")
                self._ide_status_visible = False
            self.stream.flush()


def transcrever_com_progresso(model, caminho_video, fp16, idioma):
    modulo_transcricao = importlib.import_module("whisper.transcribe")
    display = WhisperProgressDisplay()

    class BarraWhisper:
        def __init__(self, *args, **kwargs):
            display.start(kwargs.get("total", 0))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            display.finish()

        def update(self, amount):
            display.update(amount)

    tqdm_original = modulo_transcricao.tqdm
    modulo_transcricao.tqdm = SimpleNamespace(tqdm=BarraWhisper)
    try:
        with redirect_stdout(display):
            return model.transcribe(
                caminho_video,
                fp16=fp16,
                verbose=True,
                language=idioma,
            )
    finally:
        modulo_transcricao.tqdm = tqdm_original
        display.finish()
