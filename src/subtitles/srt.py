"""Formatting and persistence helpers for SRT subtitles."""

from .text_utils import corrigir_erros_texto, segundos_para_tempo


def formatar_segmentos(segmentos, deslocamento_segundos=0.0):
    """Converte os segmentos Whisper em blocos SRT e dados reutilizáveis."""
    blocos = []
    segmentos_validos = []
    contador_legenda = 1

    for segment in segmentos:
        inicio = segment["start"] - deslocamento_segundos
        fim = segment["end"] - deslocamento_segundos

        if fim < 0:
            continue
        if inicio < 0:
            inicio = 0

        texto_original = corrigir_erros_texto(segment["text"])
        if not texto_original:
            continue

        t_inicio = segundos_para_tempo(inicio)
        t_fim = segundos_para_tempo(fim)
        blocos.append(
            f"{contador_legenda}\n{t_inicio} --> {t_fim}\n{texto_original}"
        )
        segmentos_validos.append(
            (contador_legenda, t_inicio, t_fim, texto_original)
        )
        contador_legenda += 1

    return blocos, segmentos_validos


def formatar_segmentos_traduzidos(segmentos, textos_traduzidos):
    return [
        f"{numero}\n{t_inicio} --> {t_fim}\n{texto_traduzido}"
        for (numero, t_inicio, t_fim, _), texto_traduzido in zip(
            segmentos, textos_traduzidos
        )
    ]


def salvar_legenda(caminho_saida, blocos):
    with open(caminho_saida, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n\n".join(blocos) + "\n")
