import os
import tkinter as tk
from tkinter import filedialog, messagebox

from src.ffmpeg_setup import preparar_ffmpeg
from src.language_picker import perguntar_idioma
from src.model_picker import perguntar_modelo
from src.transcription import gerar_e_formatar_legenda, remover_modelo_do_cache


def run():
    preparar_ffmpeg()

    root = tk.Tk()
    root.withdraw()

    video_entrada = filedialog.askopenfilename(
        title="Selecione o arquivo de vídeo",
        filetypes=[("Arquivos de Vídeo", "*.mp4 *.mkv *.avi *.mov"), ("Todos os Arquivos", "*.*")],
        parent=root,
    )

    if not video_entrada:
        print("Nenhum vídeo selecionado. Encerrando o script.")
        return

    idioma = perguntar_idioma(root)
    if not idioma:
        print("Nenhum idioma selecionado. Encerrando o script.")
        return

    selecao_modelo = perguntar_modelo(root)
    if not selecao_modelo:
        print("Nenhum modelo selecionado. Encerrando o script.")
        return
    modelo = selecao_modelo

    pasta_video = os.path.dirname(video_entrada)
    nome_base = os.path.splitext(os.path.basename(video_entrada))[0]
    tempo_de_corte = 0.0

    srt_saida_original = os.path.join(pasta_video, f"{nome_base}.{idioma}.srt")
    sufixo_segundo = "en" if idioma == "pt" else "pt-BR"
    srt_saida_segundo = os.path.join(pasta_video, f"{nome_base}.{sufixo_segundo}.srt")

    print(f"\nPreparando para legendar '{nome_base}' no idioma [{idioma.upper()}]...")

    gerar_e_formatar_legenda(
        video_entrada,
        srt_saida_original,
        srt_saida_segundo,
        idioma_escolhido=idioma,
        deslocamento_segundos=tempo_de_corte,
        model_type=modelo,
    )

    if messagebox.askyesno(
        "Apagar cache do modelo?",
        "A transcrição terminou. Deseja apagar o modelo Whisper do cache? "
        "Ele precisará ser baixado novamente na próxima utilização.",
        parent=root,
    ):
        remover_modelo_do_cache(modelo)


if __name__ == "__main__":
    run()
