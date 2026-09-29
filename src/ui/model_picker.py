import tkinter as tk
from tkinter import ttk

from src.ui.window_position import centralizar_janela


MODELOS_WHISPER = {
    "tiny": "Mais rápido e leve; menor precisão.",
    "base": "Rápido e leve; adequado para áudio claro.",
    "small": "Bom equilíbrio entre velocidade e precisão.",
    "medium": "Mais preciso; requer mais memória e tempo.",
    "large": "Maior precisão; requer mais memória e tempo.",
}


def perguntar_modelo(root_janela) -> str | None:
    """Abre uma janela para selecionar o modelo Whisper."""
    janela = tk.Toplevel(root_janela)
    janela.title("Selecionar modelo Whisper")
    janela.geometry("440x250")
    janela.resizable(False, False)
    janela.grab_set()
    centralizar_janela(janela, 440, 250)

    modelo_escolhido: str | None = None
    modelo_var = tk.StringVar(value="large")

    tk.Label(
        janela,
        text="Qual modelo deseja usar?",
        font=("Arial", 12, "bold"),
    ).pack(pady=(20, 8))

    seletor = ttk.Combobox(
        janela,
        textvariable=modelo_var,
        values=list(MODELOS_WHISPER),
        state="readonly",
        width=18,
    )
    seletor.pack()

    descricao = tk.Label(janela, text="", wraplength=370, justify="center")
    descricao.pack(pady=12)

    def atualizar_descricao(_evento=None):
        descricao.config(text=MODELOS_WHISPER[modelo_var.get()])

    seletor.bind("<<ComboboxSelected>>", atualizar_descricao)
    atualizar_descricao()

    tk.Label(
        janela,
        text="FP16 será ativado automaticamente quando o modelo usar uma GPU CUDA.",
        wraplength=370,
        justify="center",
    ).pack(pady=(0, 10))

    botoes = tk.Frame(janela)
    botoes.pack(pady=4)

    def confirmar():
        nonlocal modelo_escolhido
        modelo_escolhido = modelo_var.get()
        janela.destroy()

    ttk.Button(botoes, text="Cancelar", command=janela.destroy).pack(
        side="left", padx=6
    )
    ttk.Button(botoes, text="Continuar", command=confirmar).pack(
        side="left", padx=6
    )

    root_janela.wait_window(janela)
    return modelo_escolhido
