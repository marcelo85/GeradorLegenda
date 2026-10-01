import pytest

from src.subtitles.srt import formatar_segmentos


def _segmento(palavras, inicio, fim, texto):
    return {
        "start": inicio,
        "end": fim,
        "text": texto,
        "words": [
            {"word": palavra, "start": palavra_inicio, "end": palavra_fim}
            for palavra, palavra_inicio, palavra_fim in palavras
        ],
    }


def test_formatar_segmentos_agrupa_palavras_de_segmentos_contiguos():
    segmentos = [
        _segmento(
            [(" The", 0.0, 0.2), (" cat", 0.2, 0.5)],
            0.0,
            0.5,
            "The cat",
        ),
        _segmento(
            [(" runs", 0.6, 1.0), (" fast.", 1.0, 1.4)],
            0.6,
            1.4,
            "runs fast.",
        ),
    ]

    blocos, validos = formatar_segmentos(segmentos)

    assert blocos == ["1\n00:00:00,000 --> 00:00:01,400\nThe cat runs fast."]
    assert validos == [
        (1, "00:00:00,000", "00:00:01,400", "The cat runs fast.")
    ]


def test_formatar_segmentos_limita_blocos_a_duas_linhas_de_ate_40_caracteres():
    palavras = [
        (f" longword{'.' if indice == 8 else ''}", (indice - 1) * 0.2, indice * 0.2)
        for indice in range(1, 10)
    ]
    segmento = _segmento(palavras, 0.0, 1.8, " ".join(["longword"] * 9) + ".")

    blocos, _ = formatar_segmentos([segmento])

    assert len(blocos) == 2
    for bloco in blocos:
        linhas_texto = bloco.splitlines()[2:]
        assert len(linhas_texto) <= 2
        assert all(len(linha) <= 40 for linha in linhas_texto)


def test_formatar_segmentos_aplica_deslocamento_aos_tempos_de_palavra():
    segmento = _segmento(
        [(" Hello.", 1.25, 2.0)],
        1.25,
        2.0,
        "Hello.",
    )

    blocos, _ = formatar_segmentos([segmento], deslocamento_segundos=1.0)

    assert blocos == ["1\n00:00:00,250 --> 00:00:01,000\nHello."]


def test_timestamps_de_palavra_sem_duracao_usam_intervalo_do_segmento():
    segmento = _segmento(
        [(" Hello.", 1.0, 1.0)],
        1.0,
        1.5,
        "Hello.",
    )

    with pytest.warns(RuntimeWarning, match="usando os limites do segmento"):
        blocos, _ = formatar_segmentos([segmento])

    assert blocos == ["1\n00:00:01,000 --> 00:00:01,500\nHello."]


def test_timestamps_arredondados_sem_duracao_usam_intervalo_do_segmento():
    segmento = _segmento(
        [(" Hello.", 1.0001, 1.0004)],
        1.0,
        1.5,
        "Hello.",
    )

    with pytest.warns(RuntimeWarning, match="usando os limites do segmento"):
        blocos, _ = formatar_segmentos([segmento])

    assert blocos == ["1\n00:00:01,000 --> 00:00:01,500\nHello."]


def test_timestamps_sem_duracao_na_palavra_e_no_segmento_falham_explicitamente():
    segmento = _segmento(
        [(" Hello.", 1.0, 1.0)],
        1.0,
        1.0,
        "Hello.",
    )

    with pytest.warns(RuntimeWarning) as avisos:
        with pytest.raises(ValueError, match="sem duração válida"):
            formatar_segmentos([segmento])

    assert any("duração zero" in str(aviso.message) for aviso in avisos)


def test_formatar_segmentos_sinaliza_segmento_sem_timestamps_de_palavra():
    with pytest.raises(ValueError, match="timestamps por palavra"):
        formatar_segmentos(
            [{"start": 0, "end": 1, "text": "Hello."}]
        )
