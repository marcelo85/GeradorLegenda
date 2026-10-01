"""Formatting and persistence helpers for SRT subtitles."""

import textwrap
import warnings

from .text_utils import corrigir_erros_texto, segundos_para_tempo


MAX_CARACTERES_POR_LINHA = 40
MAX_LINHAS_POR_BLOCO = 2
MAX_DURACAO_BLOCO = 6.0
MAX_PAUSA_ENTRE_PALAVRAS = 0.8
ABREVIACOES_COM_PONTO = {
    "a.m.",
    "dr.",
    "e.g.",
    "i.e.",
    "jr.",
    "mr.",
    "mrs.",
    "ms.",
    "p.m.",
    "prof.",
    "sr.",
    "st.",
    "u.k.",
    "u.s.",
}


def _quebrar_linhas(texto):
    return textwrap.wrap(
        texto,
        width=MAX_CARACTERES_POR_LINHA,
        break_long_words=True,
        break_on_hyphens=False,
    ) or [""]


def _encerra_frase(palavra):
    palavra_final = palavra.rstrip("\"'”’)]}")
    if palavra_final.endswith(("?", "!", "…")):
        return True
    if palavra_final.endswith("."):
        return palavra_final.strip().casefold() not in ABREVIACOES_COM_PONTO
    return False


def _coletar_palavras(segmentos):
    palavras = []

    for segment in segmentos:
        texto = segment.get("text", "").strip()
        palavras_segmento = segment.get("words")
        if not texto:
            continue
        if not palavras_segmento:
            raise ValueError(
                "O Whisper não retornou timestamps por palavra para um "
                "segmento reconhecido."
            )

        inicio_segmento = float(segment["start"])
        fim_segmento = float(segment["end"])
        for palavra in palavras_segmento:
            texto_palavra = palavra["word"]
            if not isinstance(texto_palavra, str):
                raise ValueError("O Whisper retornou uma palavra inválida.")
            inicio = float(palavra["start"])
            fim = float(palavra["end"])
            if fim < inicio:
                raise ValueError("O Whisper retornou um timestamp de palavra inválido.")
            palavras.append(
                (
                    texto_palavra,
                    inicio,
                    fim,
                    inicio_segmento,
                    fim_segmento,
                )
            )

    return palavras


def _agrupar_palavras(segmentos):
    blocos = []
    palavras_bloco = []

    def finalizar_bloco():
        nonlocal palavras_bloco
        if not palavras_bloco:
            return

        texto = corrigir_erros_texto(
            "".join(palavra[0] for palavra in palavras_bloco)
        )
        if texto:
            inicio = palavras_bloco[0][1]
            fim = palavras_bloco[-1][2]
            tempos_inicio = segundos_para_tempo(inicio)
            tempos_fim = segundos_para_tempo(fim)
            if fim <= inicio or tempos_fim == tempos_inicio:
                warnings.warn(
                    "Timestamps por palavra sem duração válida; usando os "
                    "limites do segmento Whisper.",
                    RuntimeWarning,
                    stacklevel=2,
                )
                inicio = palavras_bloco[0][3]
                fim = palavras_bloco[-1][4]
                tempos_inicio = segundos_para_tempo(inicio)
                tempos_fim = segundos_para_tempo(fim)
            if fim <= inicio or tempos_fim == tempos_inicio:
                warnings.warn(
                    "Não foi possível gerar um bloco SRT: os timestamps da "
                    "palavra e do segmento têm duração zero.",
                    RuntimeWarning,
                    stacklevel=2,
                )
                raise ValueError(
                    "O Whisper retornou um bloco sem duração válida nas "
                    "palavras e no segmento."
                )
            blocos.append((inicio, fim, texto))
        palavras_bloco = []

    for palavra in _coletar_palavras(segmentos):
        texto_candidato = corrigir_erros_texto(
            "".join(item[0] for item in palavras_bloco) + palavra[0]
        )
        linhas_candidato = _quebrar_linhas(texto_candidato)

        if palavras_bloco:
            pausa = palavra[1] - palavras_bloco[-1][2]
            duracao = palavra[2] - palavras_bloco[0][1]
            if (
                pausa > MAX_PAUSA_ENTRE_PALAVRAS
                or duracao > MAX_DURACAO_BLOCO
                or len(linhas_candidato) > MAX_LINHAS_POR_BLOCO
            ):
                finalizar_bloco()
                texto_candidato = corrigir_erros_texto(palavra[0])
                linhas_candidato = _quebrar_linhas(texto_candidato)

        if len(linhas_candidato) > MAX_LINHAS_POR_BLOCO:
            raise ValueError(
                "Uma palavra reconhecida excede o limite de linhas da legenda."
            )

        palavras_bloco.append(palavra)
        if _encerra_frase(palavra[0]):
            finalizar_bloco()

    finalizar_bloco()
    return blocos


def formatar_segmentos(segmentos, deslocamento_segundos=0.0):
    """Agrupa palavras alinhadas em blocos SRT curtos e temporizados."""
    blocos = []
    segmentos_validos = []
    contador_legenda = 1

    for inicio, fim, texto_original in _agrupar_palavras(segmentos):
        inicio -= deslocamento_segundos
        fim -= deslocamento_segundos

        if fim < 0:
            continue
        if inicio < 0:
            inicio = 0

        if fim <= inicio:
            raise ValueError("O bloco de legenda resultou em duração inválida.")

        texto_formatado = "\n".join(_quebrar_linhas(texto_original))
        t_inicio = segundos_para_tempo(inicio)
        t_fim = segundos_para_tempo(fim)
        blocos.append(
            f"{contador_legenda}\n{t_inicio} --> {t_fim}\n{texto_formatado}"
        )
        segmentos_validos.append(
            (contador_legenda, t_inicio, t_fim, texto_formatado)
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
