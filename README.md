# Gerador de Legendas

Aplicativo para transcrever vídeos com o Whisper e gerar um arquivo `.srt` no idioma original do áudio.

## Requisitos

- Windows
- Python 3.10 ou superior instalado
- Git instalado, caso vá clonar o projeto pelo terminal
- Conexão com a internet para instalar as bibliotecas e baixar o modelo Whisper escolhido

Não é necessário instalar o FFmpeg manualmente. O aplicativo prepara uma cópia local automaticamente usando `imageio-ffmpeg`.

## Baixar o projeto

Se ainda não tiver o projeto no computador, abra o PowerShell na pasta onde deseja salvá-lo e execute:

```powershell
git clone https://github.com/marcelo85/GeradorLegenda.git
cd GeradorLegenda
```

Se já baixou o projeto como arquivo ZIP, extraia-o e abra o PowerShell na pasta extraída.

## Instalar

Na pasta do projeto, crie e ative um ambiente virtual Python:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell impedir a ativação do ambiente, permita scripts somente nesta janela e tente novamente:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Com o ambiente virtual ativo, instale as dependências:

```powershell
python -m pip install --upgrade pip
python -m pip install openai-whisper imageio-ffmpeg deep-translator
```

`deep-translator` permanece nas dependências porque o código de tradução foi mantido, mas a tradução está temporariamente desativada.

## Iniciar o aplicativo

Com o ambiente virtual ativado e ainda na pasta do projeto, execute:

```powershell
python run.py
```

Na janela do aplicativo:

1. Selecione o arquivo de vídeo.
2. Escolha o idioma falado no vídeo.
3. Escolha o modelo Whisper.
4. Aguarde a transcrição. Na primeira utilização do modelo escolhido, o Whisper baixa os arquivos do modelo, o que pode levar algum tempo.
5. Ao fim, escolha se deseja apagar o modelo do cache.

O arquivo `.srt` é salvo na mesma pasta do vídeo. Se apagar o modelo do cache, ele será baixado novamente na próxima utilização.

## Modelos Whisper

- **tiny**: mais rápido e leve, com menor precisão.
- **base**: rápido e leve, adequado para áudio claro.
- **small**: equilíbrio entre velocidade e precisão.
- **medium**: mais preciso, mas requer mais tempo e memória.
- **large**: maior precisão e maior consumo de recursos.

O modelo é baixado automaticamente na primeira vez que for usado. Modelos maiores exigem mais memória e podem levar mais tempo para transcrever, especialmente em CPU. O FP16 é ativado automaticamente quando o Whisper utiliza uma GPU CUDA; em CPU, é desativado.

## Tradução

A geração da legenda traduzida está temporariamente desativada. No momento, o aplicativo gera somente a legenda no idioma original. A lógica de tradução foi mantida no código para reativação posterior.

## FFmpeg

O aplicativo usa `imageio-ffmpeg` para preparar automaticamente o executável do FFmpeg na pasta do projeto. Não baixe nem instale o FFmpeg separadamente.
