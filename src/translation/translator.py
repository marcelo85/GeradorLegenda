"""Batched translation operations and rate-limit handling."""

import time

from deep_translator import GoogleTranslator
from deep_translator.exceptions import TooManyRequests

from .progress import show_progress_bar

SEPARADOR_TRADUCAO = "\nZXQSUBTITLEBOUNDARYZXQ\n"
LIMITE_CARACTERES_LOTE = 4500
TRADUCAO_ATIVA = False


def traduzir_textos(tradutor, textos, mostrar_progresso=False):
    """Agrupa traduções, reutiliza textos repetidos e preserva a ordem."""
    traducoes = {}
    textos_unicos = list(dict.fromkeys(textos))
    lotes = []
    lote_atual = []
    tamanho_atual = 0

    for texto in textos_unicos:
        tamanho_item = len(texto) + (len(SEPARADOR_TRADUCAO) if lote_atual else 0)
        if lote_atual and tamanho_atual + tamanho_item > LIMITE_CARACTERES_LOTE:
            lotes.append(lote_atual)
            lote_atual = []
            tamanho_atual = 0
            tamanho_item = len(texto)

        if len(texto) > LIMITE_CARACTERES_LOTE:
            if lote_atual:
                lotes.append(lote_atual)
                lote_atual = []
                tamanho_atual = 0
            lotes.append([texto])
        else:
            lote_atual.append(texto)
            tamanho_atual += tamanho_item

    if lote_atual:
        lotes.append(lote_atual)

    inicio_traducao = time.time()
    limite_requisicoes_atingido = False
    for indice, lote in enumerate(lotes, start=1):
        if limite_requisicoes_atingido:
            traducoes.update((texto, texto) for texto in lote)
        else:
            try:
                resultado = tradutor.translate(SEPARADOR_TRADUCAO.join(lote))
                partes = resultado.split(SEPARADOR_TRADUCAO)
                if len(partes) != len(lote):
                    raise ValueError("O tradutor alterou os separadores do lote.")
                traducoes.update(zip(lote, (parte.strip() for parte in partes)))
            except TooManyRequests as erro:
                print(
                    "Aviso: o serviço de tradução limitou as requisições. "
                    f"Os segmentos restantes ficarão no idioma original: {erro}"
                )
                traducoes.update((texto, texto) for texto in lote)
                limite_requisicoes_atingido = True
            except Exception as erro:
                print(f"Aviso: falha ao traduzir um lote: {erro}")
                for posicao, texto in enumerate(lote):
                    if limite_requisicoes_atingido:
                        traducoes[texto] = texto
                        continue
                    try:
                        traducoes[texto] = tradutor.translate(texto)
                    except TooManyRequests as erro_individual:
                        print(
                            "Aviso: o serviço de tradução limitou as requisições. "
                            "Os segmentos restantes ficarão no idioma original: "
                            f"{erro_individual}"
                        )
                        traducoes.update(
                            (segmento, segmento) for segmento in lote[posicao:]
                        )
                        limite_requisicoes_atingido = True
                    except Exception as erro_individual:
                        print(
                            "Aviso: segmento mantido no idioma original: "
                            f"{erro_individual}"
                        )
                        traducoes[texto] = texto

        if mostrar_progresso:
            show_progress_bar(indice, len(lotes), inicio_traducao)

    return [traducoes[texto] for texto in textos]
