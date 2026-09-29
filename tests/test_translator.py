import pytest
from unittest.mock import patch

from deep_translator.exceptions import TooManyRequests

from src.transcription import (
    LIMITE_CARACTERES_LOTE,
    SEPARADOR_TRADUCAO,
    _traduzir_textos,
)


class TradutorFalso:
    def __init__(self, traducoes):
        self.traducoes = traducoes
        self.chamadas = []

    def translate(self, texto):
        self.chamadas.append(texto)
        return SEPARADOR_TRADUCAO.join(
            self.traducoes[parte]
            for parte in texto.split(SEPARADOR_TRADUCAO)
        )


def test_translation_accuracy():
    tradutor = TradutorFalso({"Good morning.": "Bom dia.", "Thank you.": "Obrigado."})

    resultado = _traduzir_textos(tradutor, ["Good morning.", "Thank you."])

    assert resultado == ["Bom dia.", "Obrigado."]
    assert len(tradutor.chamadas) == 1


def test_translation_reuses_repeated_text():
    tradutor = TradutorFalso({"Repeated line": "Linha repetida"})

    resultado = _traduzir_textos(
        tradutor, ["Repeated line", "Repeated line", "Repeated line"]
    )

    assert resultado == ["Linha repetida"] * 3
    assert len(tradutor.chamadas) == 1


def test_translation_falls_back_to_individual_segments_if_batch_separator_is_lost():
    class TradutorComSeparadorAlterado(TradutorFalso):
        def translate(self, texto):
            self.chamadas.append(texto)
            if SEPARADOR_TRADUCAO in texto:
                return "tradução sem separador"
            return self.traducoes[texto]

    tradutor = TradutorComSeparadorAlterado({"First": "Primeiro", "Second": "Segundo"})

    assert _traduzir_textos(tradutor, ["First", "Second"]) == ["Primeiro", "Segundo"]
    assert len(tradutor.chamadas) == 3


def test_translation_reports_progress_per_batch():
    tradutor = TradutorFalso({"First": "Primeiro", "Second": "Segundo"})

    with patch("src.transcription.show_progress_bar") as show_progress:
        resultado = _traduzir_textos(
            tradutor, ["First", "Second"], mostrar_progresso=True
        )

    assert resultado == ["Primeiro", "Segundo"]
    show_progress.assert_called_once()
    assert show_progress.call_args.args[:2] == (1, 1)


def test_translation_of_empty_input_does_not_call_translator_or_progress():
    tradutor = TradutorFalso({})

    with patch("src.transcription.show_progress_bar") as show_progress:
        assert _traduzir_textos(tradutor, [], mostrar_progresso=True) == []

    assert tradutor.chamadas == []
    show_progress.assert_not_called()


def test_translation_splits_texts_into_character_limited_batches(monkeypatch):
    limite = len(SEPARADOR_TRADUCAO) + 4
    monkeypatch.setattr("src.transcription.LIMITE_CARACTERES_LOTE", limite)
    tradutor = TradutorFalso(
        {"aa": "A", "bb": "B", "cc": "C", "dd": "D"}
    )

    resultado = _traduzir_textos(tradutor, ["aa", "bb", "cc", "dd"])

    assert resultado == ["A", "B", "C", "D"]
    assert tradutor.chamadas == [
        f"aa{SEPARADOR_TRADUCAO}bb",
        f"cc{SEPARADOR_TRADUCAO}dd",
    ]
    assert all(len(lote) <= limite for lote in tradutor.chamadas)


def test_oversized_text_is_translated_as_a_separate_single_item_batch(monkeypatch):
    monkeypatch.setattr("src.transcription.LIMITE_CARACTERES_LOTE", 3)
    tradutor = TradutorFalso({"long": "longo", "x": "xis"})

    assert _traduzir_textos(tradutor, ["long", "x"]) == ["longo", "xis"]
    assert tradutor.chamadas == ["long", "x"]


def test_batch_exception_falls_back_to_translating_each_segment():
    class TradutorComFalhaNoLote(TradutorFalso):
        def translate(self, texto):
            self.chamadas.append(texto)
            if SEPARADOR_TRADUCAO in texto:
                raise RuntimeError("falha no lote")
            return self.traducoes[texto]

    tradutor = TradutorComFalhaNoLote({"First": "Primeiro", "Second": "Segundo"})

    assert _traduzir_textos(tradutor, ["First", "Second"]) == ["Primeiro", "Segundo"]
    assert len(tradutor.chamadas) == 3


def test_failed_individual_translation_keeps_original_text(capsys):
    class TradutorComFalha(TradutorFalso):
        def translate(self, texto):
            self.chamadas.append(texto)
            if SEPARADOR_TRADUCAO in texto or texto == "Broken":
                raise RuntimeError("falha simulada")
            return "Funcionou"

    tradutor = TradutorComFalha({})

    assert _traduzir_textos(tradutor, ["Broken"]) == ["Broken"]
    assert "segmento mantido no idioma original" in capsys.readouterr().out


def test_progress_updates_once_for_each_batch(monkeypatch):
    monkeypatch.setattr(
        "src.transcription.LIMITE_CARACTERES_LOTE",
        len(SEPARADOR_TRADUCAO) + 4,
    )
    tradutor = TradutorFalso({"aa": "A", "bb": "B", "cc": "C"})

    with patch("src.transcription.show_progress_bar") as show_progress:
        _traduzir_textos(tradutor, ["aa", "bb", "cc"], mostrar_progresso=True)

    assert [call.args[:2] for call in show_progress.call_args_list] == [
        (1, 2),
        (2, 2),
    ]


def test_rate_limit_does_not_trigger_individual_retries_or_later_batches(monkeypatch):
    monkeypatch.setattr(
        "src.transcription.LIMITE_CARACTERES_LOTE",
        len(SEPARADOR_TRADUCAO) + 2,
    )

    class TradutorComLimite(TradutorFalso):
        def translate(self, texto):
            self.chamadas.append(texto)
            raise TooManyRequests("limite atingido")

    tradutor = TradutorComLimite({})

    resultado = _traduzir_textos(
        tradutor,
        ["aa", "bb", "cc"],
    )

    assert resultado == ["aa", "bb", "cc"]
    assert len(tradutor.chamadas) == 1


def test_rate_limit_during_individual_fallback_preserves_remaining_texts(capsys):
    class TradutorComLimiteNoFallback(TradutorFalso):
        def translate(self, texto):
            self.chamadas.append(texto)
            if SEPARADOR_TRADUCAO in texto:
                return "resposta sem os separadores"
            if texto == "Second":
                raise TooManyRequests("limite atingido")
            return "Primeiro traduzido"

    tradutor = TradutorComLimiteNoFallback({})

    resultado = _traduzir_textos(tradutor, ["First", "Second", "Third"])

    assert resultado == ["Primeiro traduzido", "Second", "Third"]
    assert tradutor.chamadas == [
        f"First{SEPARADOR_TRADUCAO}Second{SEPARADOR_TRADUCAO}Third",
        "First",
        "Second",
    ]
    assert "limitou as requisições" in capsys.readouterr().out
