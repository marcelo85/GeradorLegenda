from contextlib import redirect_stdout
import importlib
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace
from urllib.parse import urlparse

import time

import whisper
from deep_translator import GoogleTranslator
from deep_translator.exceptions import TooManyRequests

from src.progress_bar import show_progress_bar
from src.text_utils import corrigir_erros_texto, segundos_para_tempo

SEPARADOR_TRADUCAO = "\nZXQSUBTITLEBOUNDARYZXQ\n"
LIMITE_CARACTERES_LOTE = 4500
TRADUCAO_ATIVA = False


class _WhisperProgressDisplay:
    def __init__(self):
        self.stream = sys.stdout
        self.total = 0
        self.current = 0
        self.terminal = self.stream.isatty() and os.environ.get("TERM") != "dumb"
        self.rows = shutil.get_terminal_size((80, 24)).lines
        self.finished = False

    def start(self, total):
        self.total = total
        if self.terminal:
            self.stream.write(f"\033[2;{self.rows}r\033[1;1H")
            self._render()
            self.stream.write("\033[2;1H")
        else:
            self._render()
        self.stream.flush()

    def update(self, amount):
        self.current += amount
        self._render()
        self.stream.flush()

    def _render(self):
        percent = min(100, self.current * 100 / self.total) if self.total else 0
        bar_length = 32
        filled = int(bar_length * percent / 100)
        header = (
            f"Transcrição [{('=' * filled) + ('-' * (bar_length - filled))}] "
            f"{percent:5.1f}% ({self.current}/{self.total} frames)"
        )
        if self.terminal:
            self.stream.write(f"\033[s\033[1;1H{header}\033[K\033[u")
        else:
            self.stream.write(header + "\n")

    def write(self, text):
        self.stream.write(text)
        return len(text)

    def flush(self):
        self.stream.flush()

    def finish(self):
        if self.finished:
            return
        self.finished = True
        if self.terminal:
            self.stream.write(f"\033[r\033[{self.rows};1H\n")
        self.stream.flush()


def _transcrever_com_barra_e_frases(model, caminho_video, fp16, idioma):
    modulo_transcricao = importlib.import_module("whisper.transcribe")
    display = _WhisperProgressDisplay()

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


def remover_modelo_do_cache(model_type):
    url_modelo = whisper._MODELS.get(model_type)
    if url_modelo is None:
        raise ValueError(f"Não é possível localizar o arquivo do modelo {model_type!r}.")

    cache_padrao = Path.home() / ".cache"
    raiz_cache = Path(os.environ.get("XDG_CACHE_HOME", cache_padrao)) / "whisper"
    arquivo_modelo = raiz_cache / Path(urlparse(url_modelo).path).name
    if arquivo_modelo.exists():
        arquivo_modelo.unlink()
        print(f"Arquivo do modelo removido do cache: {arquivo_modelo}")


def _traduzir_textos(tradutor, textos, mostrar_progresso=False):
    """Agrupa traduções, reutiliza textos repetidos e preserva a ordem dos segmentos."""
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


def gerar_e_formatar_legenda(
    caminho_video,
    caminho_saida_original,
    caminho_saida_pt,
    idioma_escolhido,
    deslocamento_segundos=0.0,
    model_type="base",
):
    print(f"\nCarregando o modelo Whisper (idioma alvo: {idioma_escolhido.upper()})...")
    model = whisper.load_model(model_type)

    print("Ouvindo e transcrevendo o áudio do vídeo... (Isso pode demorar um pouco)")
    usar_fp16 = getattr(model.device, "type", None) == "cuda"
    resultado = _transcrever_com_barra_e_frases(
        model,
        caminho_video,
        usar_fp16,
        idioma_escolhido,
    )

    print("\nGerando arquivo de legenda... (Aguarde)")

    blocos_finais_original = []
    blocos_finais_pt = []
    contador_legenda = 1

    if TRADUCAO_ATIVA:
        alvo_traducao = "en" if idioma_escolhido == "pt" else "pt"
        tradutor = GoogleTranslator(source=idioma_escolhido, target=alvo_traducao)
    segmentos_validos = []

    for segment in resultado["segments"]:
        inicio = segment["start"] - deslocamento_segundos
        fim = segment["end"] - deslocamento_segundos

        if fim < 0:
            continue
        if inicio < 0:
            inicio = 0

        texto_original = corrigir_erros_texto(segment["text"])

        if texto_original:
            t_inicio = segundos_para_tempo(inicio)
            t_fim = segundos_para_tempo(fim)
            blocos_finais_original.append(f"{contador_legenda}\n{t_inicio} --> {t_fim}\n{texto_original}")
            if TRADUCAO_ATIVA:
                segmentos_validos.append(
                    (contador_legenda, t_inicio, t_fim, texto_original)
                )
            contador_legenda += 1

    if TRADUCAO_ATIVA:
        textos_traduzidos = _traduzir_textos(
            tradutor,
            [segmento[3] for segmento in segmentos_validos],
            mostrar_progresso=True,
        )
        for (numero, t_inicio, t_fim, _), texto_traduzido in zip(
            segmentos_validos, textos_traduzidos
        ):
            blocos_finais_pt.append(
                f"{numero}\n{t_inicio} --> {t_fim}\n{texto_traduzido}"
            )

    with open(caminho_saida_original, "w", encoding="utf-8") as f:
        f.write("\n\n".join(blocos_finais_original) + "\n")

    if TRADUCAO_ATIVA:
        with open(caminho_saida_pt, "w", encoding="utf-8") as f:
            f.write("\n\n".join(blocos_finais_pt) + "\n")

    print(f"\nFeito! Seu arquivo foi salvo em:\n-> {caminho_saida_original}")
    if TRADUCAO_ATIVA:
        print(f"-> {caminho_saida_pt}")
