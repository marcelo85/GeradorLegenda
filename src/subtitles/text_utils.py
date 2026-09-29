import re


def segundos_para_tempo(segundos):
    total_milissegundos = max(0, round(segundos * 1000))
    total_segundos, ms = divmod(total_milissegundos, 1000)
    h, resto = divmod(total_segundos, 3600)
    m, s = divmod(resto, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def corrigir_erros_texto(texto):
    correcoes = {
        r"\bthanme\b": "than me",
        r"\bthanhim\b": "than him",
        r"\bthanher\b": "than her",
        r"\bthanus\b": "than us",
        r"\bthanthem\b": "than them",
    }

    for padrao, sub in correcoes.items():
        texto = re.sub(padrao, sub, texto, flags=re.IGNORECASE)

    texto = re.sub(r"([?.!])([A-Za-z])", r"\1 \2", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto
