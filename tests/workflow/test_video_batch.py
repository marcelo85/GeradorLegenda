from unittest.mock import Mock

from src.workflow import video_batch


def test_processar_lotes_transcribes_selected_order_and_cleans_used_models(
    monkeypatch, tmp_path, capsys
):
    videos = iter(
        [
            (
                str(tmp_path / "first.mp4"),
                str(tmp_path / "second.mkv"),
            ),
            None,
        ]
    )
    monkeypatch.setattr(video_batch, "_selecionar_videos", lambda _root: next(videos))
    monkeypatch.setattr(
        video_batch,
        "perguntar_idioma",
        Mock(side_effect=["en", "pt"]),
    )
    monkeypatch.setattr(
        video_batch,
        "perguntar_modelo",
        Mock(side_effect=["small", "large"]),
    )
    transcribe = Mock()
    monkeypatch.setattr(video_batch, "gerar_e_formatar_legenda", transcribe)
    confirmations = iter([False, True])
    monkeypatch.setattr(
        video_batch.messagebox,
        "askyesno",
        Mock(side_effect=lambda *args, **kwargs: next(confirmations)),
    )
    remove_model = Mock()
    monkeypatch.setattr(video_batch, "remover_modelo_do_cache", remove_model)

    video_batch.processar_lotes_videos(Mock())

    calls = transcribe.call_args_list
    assert [call.args[:2] for call in calls] == [
        (
            str(tmp_path / "first.mp4"),
            str(tmp_path / "first.en.srt"),
        ),
        (
            str(tmp_path / "second.mkv"),
            str(tmp_path / "second.pt.srt"),
        ),
    ]
    assert [call.kwargs["model_type"] for call in calls] == ["small", "large"]
    assert [call.args[0] for call in remove_model.call_args_list] == ["small", "large"]
    output = capsys.readouterr().out
    assert "Vídeo 1 de 2: first" in output
    assert "Vídeo 2 de 2: second" in output


def test_processar_lotes_skips_cache_prompt_without_processed_videos(monkeypatch):
    monkeypatch.setattr(video_batch, "_selecionar_videos", lambda _root: ())
    ask_yes_no = Mock()
    monkeypatch.setattr(video_batch.messagebox, "askyesno", ask_yes_no)

    video_batch.processar_lotes_videos(Mock())

    ask_yes_no.assert_not_called()


def test_processar_lotes_stops_when_order_dialog_is_cancelled(monkeypatch):
    monkeypatch.setattr(
        video_batch.filedialog,
        "askopenfilenames",
        lambda **kwargs: ("video.mp4",),
    )
    monkeypatch.setattr(video_batch, "ordenar_videos", lambda videos, root: None)
    ask_yes_no = Mock()
    monkeypatch.setattr(video_batch.messagebox, "askyesno", ask_yes_no)

    video_batch.processar_lotes_videos(Mock())

    ask_yes_no.assert_not_called()
