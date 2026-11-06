import pytest

from app.services.annotations import AnnotationError, validate_input


def test_acepta_un_caracter():
    fields = validate_input("a", "segment-001", 0, 1)
    assert fields["text"] == "a"


def test_acepta_exactamente_500_caracteres():
    fields = validate_input("a" * 500, "segment-001", 0, 1)
    assert len(fields["text"]) == 500


def test_rechaza_501_caracteres():
    with pytest.raises(AnnotationError) as error:
        validate_input("a" * 501, "segment-001", 0, 1)
    assert error.value.code == "annotation_too_long"


@pytest.mark.parametrize("value", ["", "   ", None, 42])
def test_rechaza_texto_vacio_o_no_textual(value):
    with pytest.raises(AnnotationError) as error:
        validate_input(value, "segment-001", 0, 1)
    assert error.value.code == "empty_annotation"


def test_recorta_espacios_del_texto():
    assert validate_input("  observación  ", "segment-001", 0, 1)["text"] == "observación"


@pytest.mark.parametrize("segment", ["", "   ", None, 7])
def test_rechaza_segmento_ausente(segment):
    with pytest.raises(AnnotationError) as error:
        validate_input("texto", segment, 0, 1)
    assert error.value.code == "unknown_segment"


@pytest.mark.parametrize("start,end", [(-1, 1), (2, 2), (3, 1), ("x", 1), (0, None)])
def test_rechaza_rangos_invalidos(start, end):
    with pytest.raises(AnnotationError) as error:
        validate_input("texto", "segment-001", start, end)
    assert error.value.code == "invalid_range"


def test_redondea_marcas_a_tres_decimales():
    fields = validate_input("texto", "segment-001", 0.123456, 1.987654)
    assert fields["start_time"] == 0.123
    assert fields["end_time"] == 1.988
