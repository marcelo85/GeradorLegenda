import os
from pathlib import Path
from urllib.parse import urlparse

import whisper


def remover_modelo_do_cache(model_type):
    """Remove do cache o checkpoint Whisper correspondente ao modelo."""
    url_modelo = whisper._MODELS.get(model_type)
    if url_modelo is None:
        raise ValueError(f"Não é possível localizar o arquivo do modelo {model_type!r}.")

    cache_padrao = Path.home() / ".cache"
    raiz_cache = Path(os.environ.get("XDG_CACHE_HOME", cache_padrao)) / "whisper"
    arquivo_modelo = raiz_cache / Path(urlparse(url_modelo).path).name
    if arquivo_modelo.exists():
        arquivo_modelo.unlink()
        print(f"Arquivo do modelo removido do cache: {arquivo_modelo}")
