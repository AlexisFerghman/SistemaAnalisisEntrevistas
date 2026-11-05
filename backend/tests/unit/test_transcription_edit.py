import pytest

from app.services.transcription_edit import EditError, apply_edit, redistribute_words


def _segments():
    return [
        {
            "id": "segment-001",
            "start_time": 0.0,
            "end_time": 2.0,
            "text": "Primer segmento",
            "words": [
                {"text": "Primer", "start_time": 0.0, "end_time": 1.0},
                {"text": "segmento", "start_time": 1.0, "end_time": 2.0},
            ],
        },
        {
            "id": "segment-002",
            "start_time": 2.0,
            "end_time": 4.0,
            "text": "Segundo segmento",
            "words": [{"text": "Segundo", "start_time": 2.0, "end_time": 4.0}],
        },
    ]


def test_keeps_original_words_when_text_is_unchanged():
    result = apply_edit(_segments(), _segments(), duration_seconds=5.0)

    assert result[0]["words"] == _segments()[0]["words"]
    assert result[1]["words"] == _segments()[1]["words"]


def test_redistributes_words_when_text_changes():
    incoming = _segments()
    incoming[0]["text"] = "Primer segmento corregido"

    result = apply_edit(_segments(), incoming, duration_seconds=5.0)
    words = result[0]["words"]

    assert [word["text"] for word in words] == ["Primer", "segmento", "corregido"]
    assert words[0]["start_time"] == 0.0
    assert words[-1]["end_time"] == 2.0
    assert all(word["end_time"] > word["start_time"] for word in words)


def test_clamps_words_when_timestamps_shrink():
    incoming = _segments()
    incoming[0]["end_time"] = 1.0

    result = apply_edit(_segments(), incoming, duration_seconds=5.0)

    assert all(word["end_time"] <= 1.0 for word in result[0]["words"])


def test_rejects_empty_transcription():
    with pytest.raises(EditError) as error:
        apply_edit(_segments(), [], duration_seconds=5.0)
    assert error.value.code == "invalid_timestamps"


def test_rejects_empty_text():
    incoming = _segments()
    incoming[0]["text"] = "   "

    with pytest.raises(EditError) as error:
        apply_edit(_segments(), incoming, duration_seconds=5.0)
    assert error.value.code == "empty_text"


@pytest.mark.parametrize("start,end", [(-1.0, 1.0), (2.0, 2.0), (3.0, 2.0)])
def test_rejects_invalid_ranges(start, end):
    incoming = _segments()
    incoming[0]["start_time"] = start
    incoming[0]["end_time"] = end

    with pytest.raises(EditError) as error:
        apply_edit(_segments(), incoming, duration_seconds=5.0)
    assert error.value.code == "invalid_timestamps"


def test_rejects_segment_beyond_duration():
    incoming = _segments()
    incoming[1]["end_time"] = 99.0

    with pytest.raises(EditError) as error:
        apply_edit(_segments(), incoming, duration_seconds=5.0)
    assert error.value.code == "invalid_timestamps"


def test_rejects_overlapping_segments():
    incoming = _segments()
    incoming[1]["start_time"] = 1.5

    with pytest.raises(EditError) as error:
        apply_edit(_segments(), incoming, duration_seconds=5.0)
    assert error.value.code == "invalid_timestamps"


def test_redistribute_words_returns_empty_for_empty_text():
    assert redistribute_words("   ", 0.0, 2.0) == []
