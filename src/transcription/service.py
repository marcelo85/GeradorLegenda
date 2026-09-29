"""Coordinates Whisper transcription and subtitle output."""

import whisper

from src import translation
from src.subtitles import (
    formatar_segmentos,
    formatar_segmentos_traduzidos,
    salvar_legenda,
)
from .model_cache import remover_modelo_do_cache
from .progress import transcrever_com_progresso


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
    resultado = transcrever_com_progresso(
        model,
        caminho_video,
        usar_fp16,
        idioma_escolhido,
    )

    print("\nGerando arquivo de legenda... (Aguarde)")
    blocos_finais_original, segmentos_validos = formatar_segmentos(
        resultado["segments"],
        deslocamento_segundos,
    )

    # Persist the transcript first so translation failures cannot lose it.
    salvar_legenda(caminho_saida_original, blocos_finais_original)

    if translation.TRADUCAO_ATIVA:
        alvo_traducao = "en" if idioma_escolhido == "pt" else "pt"
        tradutor = translation.GoogleTranslator(
            source=idioma_escolhido,
            target=alvo_traducao,
        )
        textos_traduzidos = translation.traduzir_textos(
            tradutor,
            [segmento[3] for segmento in segmentos_validos],
            mostrar_progresso=True,
        )
        blocos_finais_pt = formatar_segmentos_traduzidos(
            segmentos_validos,
            textos_traduzidos,
        )
        salvar_legenda(caminho_saida_pt, blocos_finais_pt)

    print(f"\nFeito! Seu arquivo foi salvo em:\n-> {caminho_saida_original}")
    if translation.TRADUCAO_ATIVA:
        print(f"-> {caminho_saida_pt}")
