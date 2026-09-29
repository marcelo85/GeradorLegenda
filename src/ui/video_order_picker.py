import tkinter as tk
from tkinter import ttk

from src.ui.window_position import centralizar_janela


def mover_video(videos, indice, deslocamento):
    """Move um vídeo na lista e retorna a nova lista e posição."""
    destino = indice + deslocamento
    if indice < 0 or indice >= len(videos) or destino < 0 or destino >= len(videos):
        return list(videos), indice

    ordenados = list(videos)
    ordenados[indice], ordenados[destino] = ordenados[destino], ordenados[indice]
    return ordenados, destino


def ordenar_videos(videos, root_janela):
    """Permite revisar e ajustar explicitamente a ordem de processamento."""
    ordenados = list(videos)
    resultado = None

    janela = tk.Toplevel(root_janela)
    janela.title("Ordem dos vídeos")
    janela.geometry("700x420")
    janela.minsize(540, 320)
    janela.grab_set()
    centralizar_janela(janela, 700, 420)

    tk.Label(
        janela,
        text="Os vídeos serão processados de cima para baixo. Ajuste a ordem:",
        font=("Arial", 11, "bold"),
        wraplength=640,
    ).pack(padx=16, pady=(16, 10))

    conteudo = tk.Frame(janela)
    conteudo.pack(fill="both", expand=True, padx=16)

    lista = tk.Listbox(conteudo, selectmode="browse", activestyle="dotbox")
    barra_rolagem = ttk.Scrollbar(conteudo, orient="vertical", command=lista.yview)
    lista.configure(yscrollcommand=barra_rolagem.set)
    lista.pack(side="left", fill="both", expand=True)
    barra_rolagem.pack(side="right", fill="y")

    def atualizar_lista(indice_selecionado=None):
        lista.delete(0, tk.END)
        for video in ordenados:
            lista.insert(tk.END, video)
        if indice_selecionado is not None and ordenados:
            lista.selection_set(indice_selecionado)
            lista.activate(indice_selecionado)
            lista.see(indice_selecionado)

    atualizar_lista()

    controles = tk.Frame(janela)
    controles.pack(pady=10)

    def mover_selecao(deslocamento):
        selecao = lista.curselection()
        if not selecao:
            return
        nonlocal ordenados
        ordenados, novo_indice = mover_video(
            ordenados,
            selecao[0],
            deslocamento,
        )
        atualizar_lista(novo_indice)

    ttk.Button(
        controles,
        text="Mover para cima",
        command=lambda: mover_selecao(-1),
    ).pack(side="left", padx=5)
    ttk.Button(
        controles,
        text="Mover para baixo",
        command=lambda: mover_selecao(1),
    ).pack(side="left", padx=5)

    botoes = tk.Frame(janela)
    botoes.pack(pady=(0, 14))

    def confirmar():
        nonlocal resultado
        resultado = tuple(ordenados)
        janela.destroy()

    ttk.Button(botoes, text="Cancelar", command=janela.destroy).pack(
        side="left", padx=5
    )
    ttk.Button(botoes, text="Continuar", command=confirmar).pack(
        side="left", padx=5
    )

    root_janela.wait_window(janela)
    return resultado
