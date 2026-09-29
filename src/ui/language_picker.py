import tkinter as tk
from tkinter import simpledialog

from src.ui.window_position import centralizar_janela


def perguntar_idioma(root_janela) -> str | None:
    """Cria uma janela visual com botões para escolher o idioma principal."""
    idioma_escolhido: str | None = None

    janela = tk.Toplevel(root_janela)
    janela.title("Selecionar Idioma do Vídeo")
    janela.geometry("320x340")
    janela.resizable(False, False)
    janela.grab_set()
    centralizar_janela(janela, 320, 340)

    tk.Label(janela, text="Qual é o idioma falado no vídeo?", font=("Arial", 11, "bold")).pack(pady=15)

    def selecionar(sigla):
        nonlocal idioma_escolhido
        idioma_escolhido = sigla
        janela.destroy()

    def outro_idioma():
        nonlocal idioma_escolhido
        sigla = simpledialog.askstring("Outro Idioma", "Digite a sigla do idioma (ex: it, ru, zh):", parent=janela)
        if sigla:
            idioma_escolhido = sigla.strip().lower()
            janela.destroy()

    btn_config = {"font": ("Arial", 10), "width": 22, "pady": 5}

    tk.Button(janela, text="🇬🇧 Inglês (en)", bg="#e1e1e1", command=lambda: selecionar("en"), **btn_config).pack(pady=4)
    tk.Button(janela, text="🇧🇷 Português (pt)", bg="#e1e1e1", command=lambda: selecionar("pt"), **btn_config).pack(pady=4)
    tk.Button(janela, text="🇪🇸 Espanhol (es)", bg="#e1e1e1", command=lambda: selecionar("es"), **btn_config).pack(pady=4)
    tk.Button(janela, text="🇫🇷 Francês (fr)", bg="#e1e1e1", command=lambda: selecionar("fr"), **btn_config).pack(pady=4)
    tk.Button(janela, text="🇩🇪 Alemão (de)", bg="#e1e1e1", command=lambda: selecionar("de"), **btn_config).pack(pady=4)
    tk.Button(janela, text="🌐 Outro idioma...", bg="#d0d0d0", command=outro_idioma, **btn_config).pack(pady=10)

    root_janela.wait_window(janela)
    return idioma_escolhido
