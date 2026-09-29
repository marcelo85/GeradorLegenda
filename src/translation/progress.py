import sys
import time


def show_progress_bar(current, total, start_time):
    """Exibe uma barra de progresso no terminal com tempo restante estimado."""
    if total <= 0:
        return

    percent = (current / total) * 100

    elapsed_time = time.time() - start_time
    estimated_total_time = (elapsed_time / current) * total if current > 0 else 0
    remaining_time = estimated_total_time - elapsed_time

    bar_length = 40
    filled_length = int(bar_length * current // total)
    bar = '=' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write(f'\r[{bar}] {percent:.2f}% - Tempo restante: {remaining_time:.2f}s')
    sys.stdout.flush()

    if current == total:
        sys.stdout.write('\n')
        sys.stdout.flush()
