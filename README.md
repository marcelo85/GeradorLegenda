# Gerador de Legendas

Aplicativo para transcrever o áudio de vídeos com o Whisper e gerar um arquivo de legenda `.srt` no idioma falado.

## O que o aplicativo faz

- Permite selecionar vários vídeos nos formatos MP4, MKV, AVI ou MOV de uma só vez.
- Permite escolher o idioma do áudio: inglês, português, espanhol, francês, alemão ou outro idioma pelo código (por exemplo, `it`, `ru` ou `zh`).
- Para cada vídeo, permite escolher individualmente o idioma e o modelo Whisper.
- Transcreve os vídeos em sequência, um por vez.
- Salva a legenda `.srt` na mesma pasta do vídeo, no idioma original.
- Usa timestamps por palavra para agrupar as falas em blocos de até duas linhas,
  com aproximadamente 40 caracteres por linha.
- Depois de processar os arquivos selecionados, permite selecionar mais vídeos.
- Ao encerrar a seleção de vídeos, pergunta se deseja apagar do cache todos os modelos Whisper utilizados na sessão.

**A tradução automática está temporariamente desativada.** O código da tradução foi mantido para uso futuro, mas o aplicativo atualmente gera somente a legenda no idioma original.

## Estrutura do projeto

```text
GeradorLegenda/
├── main.py                  # Entrada alternativa do aplicativo
├── run.py                   # Arquivo recomendado para iniciar o aplicativo
├── README.md
├── src/
│   ├── __init__.py
│   ├── app.py                  # Orquestra o fluxo da aplicação
│   ├── media/
│   │   └── ffmpeg_setup.py     # Preparação automática do FFmpeg
│   ├── subtitles/
│   │   ├── __init__.py         # Formatação e gravação de arquivos SRT
│   │   ├── srt.py              # Formatação e persistência das legendas
│   │   └── text_utils.py       # Correção e formatação de texto/tempo
│   ├── transcription/
│   │   ├── __init__.py         # Exporta a API de transcrição
│   │   ├── model_cache.py      # Gerencia o cache dos modelos Whisper
│   │   ├── progress.py         # Barra, animação e saída das frases
│   │   └── service.py          # Coordena a transcrição
│   ├── translation/
│   │   ├── __init__.py         # Exporta a API de tradução
│   │   ├── progress.py         # Progresso da tradução
│   │   └── translator.py       # Tradução em lotes, desativada no momento
│   ├── ui/
│   │   ├── language_picker.py  # Seleção do idioma do áudio
│   │   ├── model_picker.py     # Seleção do modelo Whisper
│   │   ├── window_position.py  # Centralização das janelas do aplicativo
│   │   └── video_order_picker.py # Revisão e ordenação dos vídeos
│   └── workflow/
│       └── video_batch.py      # Seleção, configuração e processamento em lote
└── tests/
    ├── app/
    │   └── test_app.py
    ├── subtitles/
    │   └── test_utils.py
    ├── transcription/
    │   └── test_whisper.py
    ├── translation/
    │   └── test_translator.py
    └── workflow/
        └── test_video_batch.py
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

1. Selecione um ou mais vídeos na janela de arquivos. Use `Ctrl` ou `Shift` para selecionar vários.
2. Na tela de revisão, organize a ordem de processamento usando os botões para mover vídeos para cima ou para baixo.
3. O terminal indica o vídeo atual e o total selecionado (por exemplo, `Vídeo 1 de 5`). Para cada vídeo, escolha o idioma falado e o modelo Whisper.
4. Aguarde cada transcrição terminar. A legenda de cada vídeo é salva antes de o próximo começar. Na primeira utilização, o modelo escolhido será baixado e isso pode levar algum tempo.
5. Depois que todos os vídeos selecionados forem processados, escolha se deseja selecionar mais vídeos.
6. Quando não quiser adicionar mais vídeos, confirme se deseja apagar do cache os modelos Whisper utilizados nesta sessão.

Cada arquivo `.srt` é salvo na mesma pasta do respectivo vídeo, com o idioma no nome, por exemplo `video.en.srt`. Se os modelos forem apagados do cache, serão baixados novamente na próxima utilização.

## Modelos Whisper

- **tiny**: mais rápido e leve, com menor precisão.
- **base**: rápido e leve, adequado para áudio claro.
- **small**: equilíbrio entre velocidade e precisão.
- **medium**: mais preciso, mas requer mais memória e tempo.
- **large**: maior precisão potencial e maior consumo de recursos.

Modelos maiores podem demorar bastante, especialmente em CPU. O FP16 é ativado automaticamente quando o modelo está usando uma GPU CUDA e desativado em CPU.

Durante a transcrição, a barra mostra a porcentagem, os frames processados e o tempo transcorrido (`HH:MM:SS`). Em terminais compatíveis, a barra fica fixa no topo; no console do PyCharm, ela é atualizada na mesma linha enquanto as frases reconhecidas aparecem em linhas separadas. O relógio continua avançando durante o processamento, mesmo quando o Whisper ainda não atualiza os frames. O alinhamento por palavra pode aumentar o tempo de processamento; os limites são estimativas do Whisper e ainda podem exigir revisão contra o áudio.

## FFmpeg

O aplicativo prepara uma cópia local do executável FFmpeg a partir da biblioteca `imageio-ffmpeg` na primeira execução. Não é necessário baixar nem instalar o FFmpeg manualmente. O arquivo local `ffmpeg.exe` é gerado na pasta do projeto e pode ser grande.

## Tradução

A geração da segunda legenda traduzida está temporariamente desativada porque o serviço de tradução utilizado não está funcionando de forma confiável. Por enquanto, somente a legenda no idioma original é criada. A lógica de tradução permanece organizada no pacote `src/translation/` para ser reativada quando uma alternativa adequada estiver definida.

## Testes

Para executar os testes automatizados, instale `pytest` no ambiente virtual e rode:

```powershell
python -m pip install pytest
python -m pytest
```
