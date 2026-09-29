import tkinter as tk

from src.media.ffmpeg_setup import preparar_ffmpeg
from src.workflow.video_batch import processar_lotes_videos


def run():
    preparar_ffmpeg()

    root = tk.Tk()
    root.withdraw()
    try:
        processar_lotes_videos(root)
    finally:
        root.destroy()


if __name__ == "__main__":
    run()
