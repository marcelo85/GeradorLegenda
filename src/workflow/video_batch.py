import os
from tkinter import filedialog, messagebox

from src.transcription import gerar_e_formatar_legenda
from src.transcription.model_cache import remover_modelo_do_cache
from src.ui.language_picker import perguntar_idioma
from src.ui.model_picker import perguntar_modelo
from src.ui.video_order_picker import ordenar_videos


def _processar_video(root, video_entrada, indice, total):
    nome_base = os.path.splitext(os.path.basename(video_entrada))[0]
    print(f"\nVídeo {indice} de {total}: {nome_base}")

    idioma = perguntar_idioma(root)
    if not idioma:
        print("Nenhum idioma selecionado. Encerrando a seleção de vídeos.")
        return None

    modelo = perguntar_modelo(root)
    if not modelo:
        print("Nenhum modelo selecionado. Encerrando a seleção de vídeos.")
        return None

    pasta_video = os.path.dirname(video_entrada)
    srt_saida_original = os.path.join(pasta_video, f"{nome_base}.{idioma}.srt")
    sufixo_segundo = "en" if idioma == "pt" else "pt-BR"
    srt_saida_segundo = os.path.join(
        pasta_video, f"{nome_base}.{sufixo_segundo}.srt"
    )

    print(
        f"\nPreparando para legendar '{nome_base}' "
        f"no idioma [{idioma.upper()}]..."
    )
    gerar_e_formatar_legenda(
        video_entrada,
        srt_saida_original,
        srt_saida_segundo,
        idioma_escolhido=idioma,
        deslocamento_segundos=0.0,
        model_type=modelo,
    )
    return modelo


def _selecionar_videos(root):
    videos = filedialog.askopenfilenames(
        title="Selecione um ou mais arquivos de vídeo",
        filetypes=[
            ("Arquivos de Vídeo", "*.mp4 *.mkv *.avi *.mov"),
            ("Todos os Arquivos", "*.*"),
        ],
        parent=root,
    )
    if not videos:
        return ()
    if len(videos) == 1:
        return videos
    return ordenar_videos(videos, root)


def _perguntar_apagar_modelos(root, modelos_usados):
    if not modelos_usados or not messagebox.askyesno(
        "Apagar cache dos modelos?",
        "Deseja apagar do cache todos os modelos Whisper usados nesta sessão? "
        "Eles precisarão ser baixados novamente na próxima utilização.",
        parent=root,
    ):
        return

    for modelo in modelos_usados:
        remover_modelo_do_cache(modelo)


def processar_lotes_videos(root):
    """Seleciona, ordena e processa lotes de vídeos até o usuário encerrar."""
    modelos_usados = []

    while True:
        videos = _selecionar_videos(root)
        if videos is None:
            print("Seleção de vídeos cancelada.")
            break
        if not videos:
            if not modelos_usados:
                print("Nenhum vídeo selecionado. Encerrando o script.")
            break

        selecao_cancelada = False
        total_videos = len(videos)
        for indice, video in enumerate(videos, start=1):
            modelo = _processar_video(root, video, indice, total_videos)
            if modelo is None:
                selecao_cancelada = True
                break
            if modelo not in modelos_usados:
                modelos_usados.append(modelo)

        if selecao_cancelada or not messagebox.askyesno(
            "Adicionar mais vídeos?",
            "Os vídeos selecionados foram processados. Deseja selecionar mais vídeos?",
            parent=root,
        ):
            break

    _perguntar_apagar_modelos(root, modelos_usados)
