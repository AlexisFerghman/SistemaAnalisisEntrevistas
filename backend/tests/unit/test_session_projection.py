"""Proyección de lectura: resumen sin `words` y palabras por segmento (RF-020, RF-021)."""

from __future__ import annotations

from app.services.session_projection import segment_words, summarize_document

from ..fixtures.sessions import sample_document


def test_resumen_elimina_words_y_anade_words_count():
    document = sample_document(segment_count=3, words_per_segment=4)

    summary = summarize_document(document)

    for segment in summary["transcription"]["segments"]:
        assert "words" not in segment
        assert segment["words_count"] == 4
    assert summary["annotations"] == document["annotations"]
    assert summary["audio"] == document["audio"]
    assert summary["transcription"]["language"] == "es"


def test_resumen_no_muta_el_documento_original():
    document = sample_document(segment_count=2, words_per_segment=3)
    original_words = document["transcription"]["segments"][0]["words"]

    summarize_document(document)

    assert document["transcription"]["segments"][0]["words"] == original_words
    assert "words_count" not in document["transcription"]["segments"][0]


def test_resumen_con_transcripcion_vacia():
    document = sample_document(segment_count=1, words_per_segment=1)
    document["transcription"] = None
    document["audio"] = None
    document["status"] = "empty"

    summary = summarize_document(document)

    assert summary["transcription"] is None
    assert summary["audio"] is None
    assert summary["session_id"] == document["session_id"]


def test_resumen_de_segmento_sin_marcas_devuelve_cero():
    document = sample_document(segment_count=1, words_per_segment=1)
    document["transcription"]["segments"][0].pop("words")

    summary = summarize_document(document)

    assert summary["transcription"]["segments"][0]["words_count"] == 0


def test_segment_words_devuelve_solo_el_segmento_pedido():
    document = sample_document(segment_count=2, words_per_segment=3)

    words = segment_words(document, "segment-002")

    assert words == document["transcription"]["segments"][1]["words"]
    assert all(word["text"].startswith("palabra-01-") for word in words)


def test_segment_words_devuelve_none_si_no_existe():
    document = sample_document(segment_count=1, words_per_segment=1)

    assert segment_words(document, "segment-999") is None
    assert segment_words({"transcription": None}, "segment-001") is None
