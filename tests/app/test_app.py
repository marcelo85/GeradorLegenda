from unittest.mock import Mock

import pytest

from src import app


class FakeRoot:
    def __init__(self):
        self.destroyed = False

    def withdraw(self):
        pass

    def destroy(self):
        self.destroyed = True


def test_run_prepares_ffmpeg_and_destroys_root(monkeypatch):
    root = FakeRoot()
    prepare_ffmpeg = Mock()
    process_videos = Mock()
    monkeypatch.setattr(app, "preparar_ffmpeg", prepare_ffmpeg)
    monkeypatch.setattr(app.tk, "Tk", lambda: root)
    monkeypatch.setattr(app, "processar_lotes_videos", process_videos)

    app.run()

    prepare_ffmpeg.assert_called_once_with()
    process_videos.assert_called_once_with(root)
    assert root.destroyed


def test_run_destroys_root_when_workflow_fails(monkeypatch):
    root = FakeRoot()
    monkeypatch.setattr(app, "preparar_ffmpeg", Mock())
    monkeypatch.setattr(app.tk, "Tk", lambda: root)
    monkeypatch.setattr(
        app,
        "processar_lotes_videos",
        Mock(side_effect=RuntimeError("workflow failed")),
    )

    with pytest.raises(RuntimeError, match="workflow failed"):
        app.run()

    assert root.destroyed
