# Gerador de Legenda

Projeto para gerar arquivos `.srt` a partir de vídeos, usando o modelo Whisper para transcrição.

## Visão geral

O sistema permite:
- selecionar um vídeo
- escolher o idioma falado no arquivo
- transcrever o áudio com o Whisper
- gerar um arquivo de legenda no idioma original

## Estrutura do projeto

```text
GeradorLegenda/
├── main.py
├── docs/
│   └── README.md
├── src/
│   ├── app.py
│   ├── ffmpeg_setup.py
│   ├── language_picker.py
│   ├── model_picker.py
│   ├── progress_bar.py
│   ├── text_utils.py
│   └── transcription.py
├── tests/
│   ├── test_translator.py
│   ├── test_utils.py
│   └── test_whisper.py
└── ffmpeg.exe
```

## Modelos do Whisper

- **tiny**: mais rápido, menor precisão
- **base**: equilíbrio bom para uso geral
- **small**: melhor custo-benefício
- **medium**: mais preciso, porém mais lento
- **large**: maior precisão, exige mais recursos

## Como usar

1. Abra o projeto em um ambiente Python.
2. Execute:

```bash
python main.py
```

3. Selecione o vídeo.
4. Escolha o idioma falado no vídeo.
5. Escolha o modelo Whisper na janela seguinte.
6. Aguarde o processamento.
7. Ao terminar, escolha se deseja apagar o modelo Whisper do cache.
8. O arquivo `.srt` será gerado na mesma pasta do vídeo.

## Dependências

```bash
pip install openai-whisper
pip install imageio-ffmpeg
pip install deep-translator
```

## Observações

- O projeto também prepara automaticamente uma cópia local do `ffmpeg.exe` para funcionar dentro da pasta do aplicativo.
- O modelo Whisper é selecionado pela interface. O FP16 é ativado automaticamente quando o modelo está usando uma GPU CUDA; em CPU, é desativado. Ao fim da transcrição, o aplicativo pergunta se o arquivo do modelo deve ser removido do cache; se removido, será baixado novamente no próximo uso.
- O Whisper não oferece uma opção para desativar censura; palavras omitidas podem depender do áudio ou do reconhecimento do modelo.
- A tradução está temporariamente desativada; a lógica foi mantida no código para reativação posterior.
- Durante a transcrição, o terminal mostra a barra real de frames e as frases reconhecidas.
- A lógica foi separada por responsabilidade para facilitar manutenção e expansão futura.
