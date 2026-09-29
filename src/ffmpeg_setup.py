import os
import shutil
from pathlib import Path

import imageio_ffmpeg


def preparar_ffmpeg():
    """Copia o ffmpeg localmente para a pasta do projeto e atualiza o PATH."""
    pasta_projeto = Path(__file__).resolve().parents[1]
    caminho_exe_original = imageio_ffmpeg.get_ffmpeg_exe()
    caminho_ffmpeg_local = pasta_projeto / "ffmpeg.exe"

    if not caminho_ffmpeg_local.exists():
        shutil.copy(caminho_exe_original, caminho_ffmpeg_local)

    os.environ["PATH"] = str(pasta_projeto) + os.pathsep + os.environ.get("PATH", "")
    return caminho_ffmpeg_local
