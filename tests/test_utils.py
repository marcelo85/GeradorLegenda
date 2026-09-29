import pytest

from src.text_utils import corrigir_erros_texto, segundos_para_tempo


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("I saw thanme yesterday.", "I saw than me yesterday."),
        ("Hello.World", "Hello. World"),
        ("  texto   com   espaços  ", "texto com espaços"),
        ("THANHIM!", "than him!"),
        ("", ""),
        ("line?Next!Word", "line? Next! Word"),
        ("thanme THANHER thanus thanthem", "than me than her than us than them"),
    ],
)
def test_corrigir_erros_texto(entrada, esperado):
    assert corrigir_erros_texto(entrada) == esperado


@pytest.mark.parametrize(
    ("segundos", "esperado"),
    [
        (0, "00:00:00,000"),
        (1.234, "00:00:01,234"),
        (3661.005, "01:01:01,005"),
        (-2, "00:00:00,000"),
        (59.9999, "00:01:00,000"),
        (3600, "01:00:00,000"),
        (86400, "24:00:00,000"),
        (0.0004, "00:00:00,000"),
        (0.0006, "00:00:00,001"),
    ],
)
def test_segundos_para_tempo(segundos, esperado):
    assert segundos_para_tempo(segundos) == esperado
