import io

import pytest
from fastapi import UploadFile

from app.services import audio_validation as av

from ..helpers import wav_bytes


def _upload(content: bytes, filename: str = "audio.wav", content_type: str = "audio/wav"):
    return UploadFile(
        file=io.BytesIO(content),
        filename=filename,
        headers={"content-type": content_type},
    )


def test_accepts_mp3_and_wav():
    assert av.validate_upload("entrevista.wav", "audio/wav") == ".wav"
    assert av.validate_upload("ENTREVISTA.MP3", "audio/mpeg") == ".mp3"


def test_rejects_unsupported_extension():
    with pytest.raises(av.AudioValidationError) as error:
        av.validate_upload("notas.txt", "text/plain")
    assert error.value.code == "unsupported_format"


def test_rejects_mismatched_mime():
    with pytest.raises(av.AudioValidationError) as error:
        av.validate_upload("audio.wav", "video/mp4")
    assert error.value.code == "unsupported_format"


@pytest.mark.parametrize("generic", ["application/octet-stream", "", None])
def test_accepts_generic_mime(generic):
    assert av.validate_upload("entrevista.wav", generic) == ".wav"


def test_rejects_missing_filename():
    with pytest.raises(av.AudioValidationError) as error:
        av.validate_upload(None, "audio/wav")
    assert error.value.code == "missing_file"


def test_persist_upload_returns_size(tmp_path):
    content = wav_bytes(0.5)
    destination = tmp_path / "salida.wav"

    written = av.persist_upload(_upload(content), destination)

    assert written == len(content)
    assert destination.read_bytes() == content


def test_persist_rejects_empty_file(tmp_path):
    with pytest.raises(av.AudioValidationError) as error:
        av.persist_upload(_upload(b""), tmp_path / "vacio.wav")
    assert error.value.code == "invalid_audio"
    assert not (tmp_path / "vacio.wav").exists()


def test_persist_cuts_at_size_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(av, "MAX_BYTES", 100)
    destination = tmp_path / "grande.wav"

    with pytest.raises(av.AudioValidationError) as error:
        av.persist_upload(_upload(b"\x00" * 500), destination)

    assert error.value.code == "payload_too_large"
    assert not destination.exists()


def test_inspect_audio_reads_duration(tmp_path):
    path = tmp_path / "audio.wav"
    path.write_bytes(wav_bytes(1.0))

    assert av.inspect_audio(path) == pytest.approx(1.0, abs=0.05)


def test_exactly_the_limit_is_accepted(tmp_path, monkeypatch):
    monkeypatch.setattr(av, "MAX_BYTES", 100)
    destination = tmp_path / "limite.wav"

    assert av.persist_upload(_upload(b"\x00" * 100), destination) == 100
    assert destination.exists()


def test_inspect_rejects_non_audio(tmp_path):
    path = tmp_path / "falso.wav"
    path.write_bytes(b"esto no es audio")

    with pytest.raises(av.AudioValidationError) as error:
        av.inspect_audio(path)

    assert error.value.code == "invalid_audio"


def test_content_length_detecta_exceso_sin_leer_el_cuerpo():
    assert av.content_length_exceeded(None) is False
    assert av.content_length_exceeded("") is False
    assert av.content_length_exceeded("no-numerico") is False
    assert av.content_length_exceeded(str(av.MAX_BYTES)) is False
    assert av.content_length_exceeded(str(av.MAX_BYTES + 1)) is True
