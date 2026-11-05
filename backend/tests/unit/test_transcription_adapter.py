import pytest

from app.transcription import adapter
from app.transcription.adapter import (
    TranscriptionCancelled,
    TranscriptionInvalidResponse,
    TranscriptionTimeout,
)

FAKE_SEGMENTS = [
    {
        "start_time": 0.0,
        "end_time": 2.0,
        "text": "Primer segmento sintético.",
        "words": [
            {"text": "Primer", "start_time": 0.0, "end_time": 0.5},
            {"text": "segmento", "start_time": 0.5, "end_time": 1.4},
        ],
    },
    {
        "start_time": 2.0,
        "end_time": 4.0,
        "text": "Segundo segmento sintético.",
        "words": [{"text": "Segundo", "start_time": 2.0, "end_time": 2.8}],
    },
]


class FlakyEngine:
    """Falla una vez y luego responde."""

    name = "flaky"

    def __init__(self) -> None:
        self.calls = 0

    def run(self, audio_path, language, on_segment, should_cancel):
        self.calls += 1
        if self.calls == 1:
            raise TranscriptionTimeout("timeout simulado")
        return [dict(segment) for segment in FAKE_SEGMENTS]


class AlwaysTimeoutEngine:
    name = "timeout"

    def run(self, audio_path, language, on_segment, should_cancel):
        raise TranscriptionTimeout("timeout simulado")


def test_transcribe_with_fake_engine(monkeypatch, tmp_path):
    monkeypatch.setenv("TRANSCRIPTION_ENGINE", "fake")
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"\x00" * 10)

    result = adapter.transcribe(audio, duration_seconds=10.0)

    assert result.provider == "fake"
    assert result.retry_count == 0
    assert len(result.segments) == 3
    assert result.segments[0]["id"] == "segment-001"
    assert result.segments[0]["words"], "debe conservar marcas por palabra"


def test_normalize_sorts_and_removes_overlaps():
    segments = adapter.normalize_segments(
        [
            {"start_time": 5.0, "end_time": 7.0, "text": "Tercero", "words": []},
            {"start_time": 0.0, "end_time": 3.0, "text": "Primero", "words": []},
            {"start_time": 2.0, "end_time": 4.0, "text": "Solapado", "words": []},
        ],
        duration_seconds=10.0,
    )

    assert [segment["text"] for segment in segments] == ["Primero", "Solapado", "Tercero"]
    assert segments[1]["start_time"] == segments[0]["end_time"]


def test_normalize_clamps_negative_and_out_of_range():
    segments = adapter.normalize_segments(
        [{"start_time": -3.0, "end_time": 99.0, "text": "Fuera", "words": []}],
        duration_seconds=8.0,
    )

    assert segments[0]["start_time"] == 0.0
    assert segments[0]["end_time"] == 8.0


def test_normalize_drops_empty_text_and_invalid_ranges():
    with pytest.raises(TranscriptionInvalidResponse):
        adapter.normalize_segments(
            [
                {"start_time": 0.0, "end_time": 2.0, "text": "   ", "words": []},
                {"start_time": 3.0, "end_time": 3.0, "text": "Nulo", "words": []},
            ],
            duration_seconds=5.0,
        )


def test_normalize_clamps_words_inside_segment():
    segments = adapter.normalize_segments(
        [
            {
                "start_time": 1.0,
                "end_time": 3.0,
                "text": "Palabra",
                "words": [{"text": "Palabra", "start_time": 0.0, "end_time": 10.0}],
            }
        ],
        duration_seconds=5.0,
    )

    word = segments[0]["words"][0]
    assert word["start_time"] >= 1.0
    assert word["end_time"] <= 3.0


def test_retries_once_on_timeout(monkeypatch, tmp_path):
    engine = FlakyEngine()
    monkeypatch.setattr(adapter, "get_engine", lambda: engine)
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"\x00" * 10)

    result = adapter.transcribe(audio, duration_seconds=10.0)

    assert engine.calls == 2
    assert result.retry_count == 1
    assert result.provider == "flaky"


def test_timeout_after_retry_propagates(monkeypatch, tmp_path):
    monkeypatch.setattr(adapter, "get_engine", lambda: AlwaysTimeoutEngine())
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"\x00" * 10)

    with pytest.raises(TranscriptionTimeout):
        adapter.transcribe(audio, duration_seconds=10.0)


def test_cancellation_stops_between_segments(monkeypatch, tmp_path):
    monkeypatch.setenv("TRANSCRIPTION_ENGINE", "fake")
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"\x00" * 10)

    with pytest.raises(TranscriptionCancelled):
        adapter.transcribe(audio, duration_seconds=10.0, should_cancel=lambda: True)
