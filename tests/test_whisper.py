import importlib
from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from src.transcription import gerar_e_formatar_legenda


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
        patch("src.transcription.whisper.load_model", return_value=modelo) as load_model,
        patch("src.transcription.GoogleTranslator") as google_translator,
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
    tradutor.translate.return_value = "Olá."
    monkeypatch.setattr("src.transcription.TRADUCAO_ATIVA", True)

    with (
        patch("src.transcription.whisper.load_model", return_value=modelo),
        patch("src.transcription.GoogleTranslator", return_value=tradutor),
    ):
        caminho_original = tmp_path / "legenda.en.srt"
        caminho_traduzido = tmp_path / "legenda.pt.srt"
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
        patch("src.transcription.whisper.load_model", return_value=modelo),
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

    from src.transcription import remover_modelo_do_cache

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

    from src.transcription import remover_modelo_do_cache

    remover_modelo_do_cache("base")


def test_cache_cleanup_rejects_unknown_model():
    from src.transcription import remover_modelo_do_cache

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
    with patch("src.transcription.sys.stdout", saida):
        from src.transcription import _transcrever_com_barra_e_frases

        _transcrever_com_barra_e_frases(model, "video.mp4", False, "en")

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
        from src.transcription import _transcrever_com_barra_e_frases

        _transcrever_com_barra_e_frases(model, "video.mp4", False, "en")

    assert modulo_transcricao.tqdm is tqdm_previo


@pytest.mark.parametrize(
    ("terminal", "esperado"),
    [(False, "50.0%"), (True, "\x1b[1;1H")],
)
def test_progress_display_handles_terminal_and_plain_output(terminal, esperado):
    from src.transcription import _WhisperProgressDisplay

    stream = StringIO()
    stream.isatty = lambda: terminal
    display = _WhisperProgressDisplay()
    display.stream = stream
    display.terminal = terminal

    display.start(100)
    display.update(50)
    display.finish()

    assert esperado in stream.getvalue()
    assert display.finished


def test_progress_display_caps_progress_at_one_hundred_percent():
    from src.transcription import _WhisperProgressDisplay

    stream = StringIO()
    display = _WhisperProgressDisplay()
    display.stream = stream
    display.terminal = False

    display.start(10)
    display.update(15)

    assert "100.0%" in stream.getvalue()


def test_progress_display_handles_zero_total():
    from src.transcription import _WhisperProgressDisplay

    stream = StringIO()
    display = _WhisperProgressDisplay()
    display.stream = stream
    display.terminal = False

    display.start(0)

    assert "0.0%" in stream.getvalue()
