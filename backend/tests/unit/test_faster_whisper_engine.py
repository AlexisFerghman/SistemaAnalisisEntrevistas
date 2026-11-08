import logging

import pytest

from app.transcription import faster_whisper_engine as engine
from app.transcription.adapter import (
    TranscriptionCancelled,
    TranscriptionRejected,
    TranscriptionUnavailable,
)


class FakeWord:
    def __init__(self, text: str, start: float, end: float) -> None:
        self.word = text
        self.start = start
        self.end = end


class FakeSegment:
    def __init__(self, start: float, end: float, text: str, words: list[FakeWord]) -> None:
        self.start = start
        self.end = end
        self.text = text
        self.words = words


class FakeModel:
    def __init__(self, segments=None, error: Exception | None = None) -> None:
        self.segments = segments or []
        self.error = error
        self.calls: list[tuple[tuple, dict]] = []

    def transcribe(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if self.error is not None:
            raise self.error
        return iter(self.segments), None


def _segments() -> list[FakeSegment]:
    return [
        FakeSegment(
            0.0,
            1.0,
            "Hola mundo.",
            [
                FakeWord("Hola", 0.0, 0.4),
                FakeWord("mundo.", 0.4, 1.0),
            ],
        ),
        FakeSegment(
            1.0,
            2.0,
            "Segundo segmento.",
            [FakeWord("Segundo", 1.0, 1.5)],
        ),
    ]


@pytest.fixture(autouse=True)
def _reset_engine():
    engine.reset_model()
    yield
    engine.reset_model()


def _audio(tmp_path):
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"\x00" * 10)
    return audio


def _patch_model(monkeypatch, model: FakeModel):
    monkeypatch.setattr(engine, "_load_model", lambda: model)


def test_default_configuration(monkeypatch, tmp_path):
    model = FakeModel(_segments())
    created = []

    def fake_create(model_name, device, compute_type, local_files_only):
        created.append((model_name, device, compute_type, local_files_only))
        return model

    glossary = tmp_path / "glosario.txt"
    glossary.write_text("WindowSHAP, BiGRU", encoding="utf-8")
    monkeypatch.setattr(engine, "_create_model", fake_create)
    monkeypatch.setenv("WHISPER_GLOSSARY_PATH", str(glossary))

    result = engine.FasterWhisperEngine().run(_audio(tmp_path), "es", None, None)

    assert created == [("large-v3-turbo", "cuda", "float16", True)]
    _args, kwargs = model.calls[0]
    assert kwargs["language"] == "es"
    assert kwargs["word_timestamps"] is True
    assert kwargs["vad_filter"] is True
    assert kwargs["beam_size"] == 5
    assert kwargs["initial_prompt"] == "WindowSHAP, BiGRU"
    assert result[0]["words"][0]["text"] == "Hola"


def test_environment_overrides_model_and_local_files(monkeypatch, tmp_path):
    model = FakeModel(_segments())
    created = []

    def fake_create(model_name, device, compute_type, local_files_only):
        created.append((model_name, local_files_only))
        return model

    monkeypatch.setattr(engine, "_create_model", fake_create)
    monkeypatch.setenv("WHISPER_MODEL", "base")
    monkeypatch.setenv("WHISPER_LOCAL_FILES_ONLY", "0")
    monkeypatch.setenv("WHISPER_VAD_FILTER", "0")

    engine.FasterWhisperEngine().run(_audio(tmp_path), "es", None, None)

    assert created == [("base", False)]
    _args, kwargs = model.calls[0]
    assert kwargs["vad_filter"] is False


def test_glossary_loader_reads_and_hashes(monkeypatch, tmp_path, caplog):
    glossary = tmp_path / "glosario.txt"
    glossary.write_text("  SHAP, BiGRU  \n", encoding="utf-8")
    monkeypatch.setenv("WHISPER_GLOSSARY_PATH", str(glossary))

    with caplog.at_level(logging.INFO):
        text = engine._load_glossary()

    assert text == "SHAP, BiGRU"
    assert "hash=" in caplog.text


def test_glossary_missing_returns_none(monkeypatch, tmp_path):
    monkeypatch.setenv("WHISPER_GLOSSARY_PATH", str(tmp_path / "no-existe.txt"))

    assert engine._load_glossary() is None


def test_glossary_empty_returns_none(monkeypatch, tmp_path):
    glossary = tmp_path / "vacio.txt"
    glossary.write_text("   \n", encoding="utf-8")
    monkeypatch.setenv("WHISPER_GLOSSARY_PATH", str(glossary))

    assert engine._load_glossary() is None


def test_bundled_glossary_is_present(monkeypatch):
    monkeypatch.delenv("WHISPER_GLOSSARY_PATH", raising=False)

    text = engine._load_glossary()

    assert text
    assert "SHAP" in text


def test_engine_provider_is_local():
    assert engine.FasterWhisperEngine.name == "local"


def test_words_are_preserved_and_callbacks_run(monkeypatch, tmp_path):
    model = FakeModel(_segments())
    _patch_model(monkeypatch, model)
    seen: list[int] = []

    result = engine.FasterWhisperEngine().run(
        _audio(tmp_path), "es", lambda index: seen.append(index), None
    )

    assert len(result) == 2
    assert result[0]["words"] == [
        {"text": "Hola", "start_time": 0.0, "end_time": 0.4},
        {"text": "mundo.", "start_time": 0.4, "end_time": 1.0},
    ]
    assert seen == [0, 1]


def test_no_speech_raises_rejected(monkeypatch, tmp_path):
    _patch_model(monkeypatch, FakeModel([]))

    with pytest.raises(TranscriptionRejected):
        engine.FasterWhisperEngine().run(_audio(tmp_path), "es", None, None)


def test_cancel_before_model_load(monkeypatch, tmp_path):
    called: list[tuple] = []

    def fake_create(*args, **kwargs):
        called.append(args)
        return FakeModel(_segments())

    monkeypatch.setattr(engine, "_create_model", fake_create)

    with pytest.raises(TranscriptionCancelled):
        engine.FasterWhisperEngine().run(
            _audio(tmp_path), "es", None, lambda: True
        )

    assert called == []


def test_cancel_between_segments(monkeypatch, tmp_path):
    _patch_model(monkeypatch, FakeModel(_segments()))
    checks = {"count": 0}

    def should_cancel() -> bool:
        checks["count"] += 1
        return checks["count"] >= 3

    with pytest.raises(TranscriptionCancelled):
        engine.FasterWhisperEngine().run(
            _audio(tmp_path), "es", None, should_cancel
        )


def test_gpu_failure_falls_back_to_cpu(monkeypatch, tmp_path):
    created: list[tuple[str, str]] = []

    def fake_create(model_name, device, compute_type, local_files_only):
        created.append((device, compute_type))
        if device == "cuda":
            raise RuntimeError("CUDA no disponible")
        return FakeModel(_segments())

    monkeypatch.setattr(engine, "_create_model", fake_create)

    engine.FasterWhisperEngine().run(_audio(tmp_path), "es", None, None)

    assert created == [("cuda", "float16"), ("cpu", "int8")]


def test_both_devices_fail_raises_unavailable(monkeypatch, tmp_path):
    def fake_create(*args, **kwargs):
        raise RuntimeError("sin recursos")

    monkeypatch.setattr(engine, "_create_model", fake_create)

    with pytest.raises(TranscriptionUnavailable):
        engine.FasterWhisperEngine().run(_audio(tmp_path), "es", None, None)


def test_memory_error_maps_to_unavailable(monkeypatch, tmp_path):
    _patch_model(monkeypatch, FakeModel(error=MemoryError("out of memory")))

    with pytest.raises(TranscriptionUnavailable):
        engine.FasterWhisperEngine().run(_audio(tmp_path), "es", None, None)


def test_decode_error_maps_to_rejected(monkeypatch, tmp_path):
    class InvalidDataError(Exception):
        pass

    _patch_model(monkeypatch, FakeModel(error=InvalidDataError("invalid data")))

    with pytest.raises(TranscriptionRejected):
        engine.FasterWhisperEngine().run(_audio(tmp_path), "es", None, None)


def test_unknown_error_maps_to_unavailable(monkeypatch, tmp_path):
    _patch_model(monkeypatch, FakeModel(error=RuntimeError("fallo raro")))

    with pytest.raises(TranscriptionUnavailable):
        engine.FasterWhisperEngine().run(_audio(tmp_path), "es", None, None)
