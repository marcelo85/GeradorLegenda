def centralizar_janela(janela, largura, altura):
    """Posiciona uma janela Tk no centro da tela após calcular seu layout."""
    janela.update_idletasks()
    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()
    x = max(0, (largura_tela - largura) // 2)
    y = max(0, (altura_tela - altura) // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
