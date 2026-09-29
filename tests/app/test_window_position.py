from unittest.mock import Mock

from src.ui.window_position import centralizar_janela


def test_centralizar_janela_positions_window_at_screen_center():
    window = Mock()
    window.winfo_screenwidth.return_value = 1920
    window.winfo_screenheight.return_value = 1080

    centralizar_janela(window, 700, 420)

    window.update_idletasks.assert_called_once_with()
    window.geometry.assert_called_once_with("700x420+610+330")


def test_centralizar_janela_clamps_position_for_windows_larger_than_screen():
    window = Mock()
    window.winfo_screenwidth.return_value = 800
    window.winfo_screenheight.return_value = 600

    centralizar_janela(window, 1000, 700)

    window.geometry.assert_called_once_with("1000x700+0+0")
