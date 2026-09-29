# Gerador de Legendas

Aplicativo para transcrever o áudio de vídeos com o Whisper e gerar um arquivo de legenda `.srt` no idioma falado.

## O que o aplicativo faz

- Permite selecionar um vídeo nos formatos MP4, MKV, AVI ou MOV.
- Permite escolher o idioma do áudio: inglês, português, espanhol, francês, alemão ou outro idioma pelo código (por exemplo, `it`, `ru` ou `zh`).
- Transcreve o áudio usando um modelo Whisper selecionado na interface.
- Salva a legenda `.srt` na mesma pasta do vídeo, no idioma original.
- Pergunta ao final se deseja apagar do cache o modelo Whisper utilizado.

**A tradução automática está temporariamente desativada.** O código da tradução foi mantido para uso futuro, mas o aplicativo atualmente gera somente a legenda no idioma original.

## Estrutura do projeto

```text
GeradorLegenda/
├── main.py                  # Entrada alternativa do aplicativo
├── run.py                   # Arquivo recomendado para iniciar o aplicativo
├── README.md
├── src/
│   ├── __init__.py
│   ├── app.py               # Fluxo principal e interface de seleção
│   ├── ffmpeg_setup.py      # Preparação automática do FFmpeg
│   ├── language_picker.py   # Seleção do idioma do áudio
│   ├── model_picker.py     # Seleção do modelo Whisper
│   ├── progress_bar.py     # Barra de progresso
│   ├── text_utils.py       # Formatação e correção do texto
│   └── transcription.py    # Transcrição e geração do arquivo SRT
└── tests/
    ├── test_translator.py
    ├── test_utils.py
    └── test_whisper.py
```

## Requisitos

- Windows
- Python 3.10 ou superior
- Git, se for baixar o projeto usando `git clone`
- Acesso à internet para instalar as bibliotecas e baixar o modelo Whisper na primeira utilização

Não é necessário instalar o FFmpeg separadamente. O projeto usa `imageio-ffmpeg` para disponibilizar uma cópia local do executável automaticamente.

## Baixar o projeto

Para clonar o repositório, abra o PowerShell na pasta onde deseja guardar o projeto e execute:

```powershell
git clone https://github.com/marcelo85/GeradorLegenda.git
cd GeradorLegenda
```

Também é possível baixar o projeto como ZIP pelo GitHub e extraí-lo. Nesse caso, abra o PowerShell dentro da pasta extraída antes de seguir para a instalação.

## Instalação

Na pasta do projeto, crie e ative um ambiente virtual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a ativação de scripts, libere a execução apenas para a janela atual e tente ativar novamente:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Com o ambiente virtual ativo, instale as dependências:

```powershell
python -m pip install --upgrade pip
python -m pip install openai-whisper imageio-ffmpeg deep-translator
```

`deep-translator` continua listado porque o código de tradução foi preservado e a biblioteca é importada pelo aplicativo, embora a tradução esteja desativada.

## Executar

Com o ambiente virtual ativo e o PowerShell aberto na pasta do projeto, inicie o aplicativo com:

```powershell
python run.py
```

O arquivo `main.py` também pode iniciar o aplicativo, mas `run.py` é o ponto de entrada recomendado.

1. Selecione o arquivo de vídeo.
2. Escolha o idioma falado no vídeo.
3. Selecione o modelo Whisper.
4. Aguarde a transcrição. Na primeira utilização, o modelo escolhido será baixado e isso pode levar algum tempo.
5. Ao terminar, confirme se deseja apagar o modelo Whisper do cache.

O arquivo `.srt` é salvo na mesma pasta do vídeo, com o idioma no nome, por exemplo `video.en.srt`. Se o modelo for apagado do cache, será baixado novamente na próxima utilização.

## Modelos Whisper

- **tiny**: mais rápido e leve, com menor precisão.
- **base**: rápido e leve, adequado para áudio claro.
- **small**: equilíbrio entre velocidade e precisão.
- **medium**: mais preciso, mas requer mais memória e tempo.
- **large**: maior precisão potencial e maior consumo de recursos.

Modelos maiores podem demorar bastante, especialmente em CPU. O FP16 é ativado automaticamente quando o modelo está usando uma GPU CUDA e desativado em CPU.

## FFmpeg

O aplicativo prepara uma cópia local do executável FFmpeg a partir da biblioteca `imageio-ffmpeg` na primeira execução. Não é necessário baixar nem instalar o FFmpeg manualmente. O arquivo local `ffmpeg.exe` é gerado na pasta do projeto e pode ser grande.

## Tradução

A geração da segunda legenda traduzida está temporariamente desativada porque o serviço de tradução utilizado não está funcionando de forma confiável. Por enquanto, somente a legenda no idioma original é criada. A lógica de tradução permanece no código para ser reativada quando uma alternativa adequada estiver definida.

## Testes

Para executar os testes automatizados, instale `pytest` no ambiente virtual e rode:

```powershell
python -m pip install pytest
python -m pytest
```
