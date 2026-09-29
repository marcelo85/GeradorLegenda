import importlib
from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from src import translation
from src.transcription import gerar_e_formatar_legenda
from src.transcription.model_cache import remover_modelo_do_cache
from src.transcription.progress import (
    WhisperProgressDisplay,
    transcrever_com_progresso,
)


@pytest.mark.parametrize(
    ("device", "fp16"),
    [("cpu", False), ("cuda", True)],
)
def test_whisper_model_loading_and_transcription(device, fp16, tmp_path):
    modelo = Mock()
    modelo.device = SimpleNamespace(type=device)
    modelo.transcribe.return_value = {
        "segments": [
            {"start": 0.25, "end": 1.5, "text": " Hello.World "},
            {"start": 2.0, "end": 2.5, "text": "Thank you."},
        ]
    }
    with (
        patch(
            "src.transcription.service.whisper.load_model",
            return_value=modelo,
        ) as load_model,
        patch("src.translation.GoogleTranslator") as google_translator,
    ):
        caminho_original = tmp_path / "legenda.en.srt"
        caminho_traduzido = tmp_path / "legenda.pt.srt"
        gerar_e_formatar_legenda(
            "video.mp4",
            caminho_original,
            caminho_traduzido,
            "en",
            model_type="small",
        )

    google_translator.assert_not_called()
    load_model.assert_called_once_with("small")
    modelo.transcribe.assert_called_once_with(
        "video.mp4",
        fp16=fp16,
        verbose=True,
        language="en",
    )
    assert caminho_original.read_text(encoding="utf-8") == (
        "1\n00:00:00,250 --> 00:00:01,500\nHello. World\n\n"
        "2\n00:00:02,000 --> 00:00:02,500\nThank you.\n"
    )
    assert not caminho_traduzido.exists()


def test_translation_is_available_when_enabled(monkeypatch, tmp_path):
    modelo = Mock()
    modelo.device = SimpleNamespace(type="cpu")
    modelo.transcribe.return_value = {
        "segments": [{"start": 0, "end": 1, "text": "Hello."}]
    }
    tradutor = Mock()
    monkeypatch.setattr(translation, "TRADUCAO_ATIVA", True)

    caminho_original = tmp_path / "legenda.en.srt"
    caminho_traduzido = tmp_path / "legenda.pt.srt"

    def traduzir_apos_salvar(texto):
        assert caminho_original.exists()
        assert "Hello." in caminho_original.read_text(encoding="utf-8")
        return "Olá."

    tradutor.translate.side_effect = traduzir_apos_salvar

    with (
        patch("src.transcription.service.whisper.load_model", return_value=modelo),
        patch("src.translation.GoogleTranslator", return_value=tradutor),
    ):
        gerar_e_formatar_legenda(
            "video.mp4",
            caminho_original,
            caminho_traduzido,
            "en",
        )

    assert "Hello." in caminho_original.read_text(encoding="utf-8")
    assert "Olá." in caminho_traduzido.read_text(encoding="utf-8")


def test_transcription_failure_is_propagated(tmp_path):
    modelo = Mock()
    modelo.device = SimpleNamespace(type="cpu")
    modelo.transcribe.side_effect = RuntimeError("falha de transcrição")

    with (
        patch("src.transcription.service.whisper.load_model", return_value=modelo),
        pytest.raises(RuntimeError, match="falha de transcrição"),
    ):
        gerar_e_formatar_legenda(
            "video.mp4",
            tmp_path / "original.srt",
            tmp_path / "traduzida.srt",
            "en",
        )

def test_cache_cleanup_removes_selected_checkpoint(tmp_path, monkeypatch):
    import whisper

    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    monkeypatch.setitem(
        whisper._MODELS,
        "base",
        "https://example.test/checksum/base.pt",
    )
    cache_modelo = tmp_path / "whisper" / "base.pt"
    cache_modelo.parent.mkdir()
    cache_modelo.write_bytes(b"modelo")

    remover_modelo_do_cache("base")

    assert not cache_modelo.exists()


def test_cache_cleanup_does_not_fail_if_checkpoint_is_not_present(tmp_path, monkeypatch):
    import whisper

    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    monkeypatch.setitem(
        whisper._MODELS,
        "base",
        "https://example.test/checksum/base.pt",
    )

    remover_modelo_do_cache("base")


def test_cache_cleanup_rejects_unknown_model():
    with pytest.raises(ValueError, match="Não é possível localizar"):
        remover_modelo_do_cache("unknown-model")


def test_transcription_shows_frame_bar_and_segments_together():
    modulo_transcricao = importlib.import_module("whisper.transcribe")
    model = Mock()

    def transcribe(*args, **kwargs):
        with modulo_transcricao.tqdm.tqdm(total=100, unit="frames") as progress:
            print("[00:00:00.000 --> 00:00:01.000] frase reconhecida")
            progress.update(25)
        return {"segments": []}

    model.transcribe.side_effect = transcribe
    tqdm_previo = modulo_transcricao.tqdm
    saida = StringIO()
    with patch("src.transcription.progress.sys.stdout", saida):
        transcrever_com_progresso(model, "video.mp4", False, "en")

    assert modulo_transcricao.tqdm is tqdm_previo
    assert "25.0%" in saida.getvalue()
    assert "frase reconhecida" in saida.getvalue()
    assert model.transcribe.call_args.kwargs["verbose"] is True


def test_transcription_restores_whisper_progress_hook_after_exception():
    modulo_transcricao = importlib.import_module("whisper.transcribe")
    tqdm_previo = modulo_transcricao.tqdm
    model = Mock()
    model.transcribe.side_effect = RuntimeError("erro")

    with pytest.raises(RuntimeError, match="erro"):
        transcrever_com_progresso(model, "video.mp4", False, "en")

    assert modulo_transcricao.tqdm is tqdm_previo


@pytest.mark.parametrize(
    ("terminal", "esperado"),
    [(False, "50.0%"), (True, "\x1b[1;1H")],
)
def test_progress_display_handles_terminal_and_plain_output(terminal, esperado):
    stream = StringIO()
    stream.isatty = lambda: terminal
    display = WhisperProgressDisplay()
    display.stream = stream
    display.terminal = terminal

    display.start(100)
    display.update(50)
    display.finish()

    assert esperado in stream.getvalue()
    assert display.finished


def test_progress_display_caps_progress_at_one_hundred_percent():
    stream = StringIO()
    display = WhisperProgressDisplay()
    display.stream = stream
    display.terminal = False

    display.start(10)
    display.update(15)

    assert "100.0%" in stream.getvalue()


@pytest.mark.parametrize(
    ("elapsed_seconds", "expected"),
    [(65, "Decorrido: 00:01:05"), (3661, "Decorrido: 01:01:01")],
)
def test_progress_display_shows_elapsed_time(elapsed_seconds, expected):
    from src.transcription.progress import WhisperProgressDisplay

    stream = StringIO()
    display = WhisperProgressDisplay()
    display.stream = stream
    display.terminal = False

    with patch(
        "src.transcription.progress.time.monotonic",
        side_effect=[100, 100 + elapsed_seconds],
    ):
        display.start(100)

    assert expected in stream.getvalue()


def test_progress_display_uses_fixed_bar_in_pycharm_console(monkeypatch):
    monkeypatch.setenv("PYCHARM_HOSTED", "1")
    stream = StringIO()
    display = WhisperProgressDisplay()
    display.stream = stream

    display.start(100)
    display.update(25)
    display.write("frase reconhecida\n")
    display.finish()

    output = stream.getvalue()
    assert display.ide_console
    assert not display.terminal
    assert "\rTranscrição" in output
    assert "\033[" not in output
    assert "frase reconhecida" in stream.getvalue()
    assert "\nfrase reconhecida\n\rTranscrição" in output


def test_progress_display_refreshes_elapsed_time_without_spinner():
    stream = StringIO()
    display = WhisperProgressDisplay()
    display.stream = stream
    display.terminal = True

    display.start(100)
    assert display._refresh_thread.is_alive()
    display.finish()

    assert "Decorrido: 00:00:00" in stream.getvalue()
    assert not display._refresh_thread.is_alive()


def test_progress_display_handles_zero_total():
    stream = StringIO()
    display = WhisperProgressDisplay()
    display.stream = stream
    display.terminal = False

    display.start(0)

    assert "0.0%" in stream.getvalue()
