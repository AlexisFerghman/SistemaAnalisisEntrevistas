#!/usr/bin/env python3
"""Evalúa WER y aciertos de glosario de un audio sintético.

Uso:
    python scripts/evaluate_transcription.py \
        --audio /data/audio/eval/audioCorto.wav \
        --reference /data/audio/eval/audioCorto.reference.txt \
        --model large-v3-turbo

El script no usa la salida de un motor como referencia: `--reference` debe ser
una transcripción corregida manualmente a partir del audio.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.transcription import faster_whisper_engine as engine  # noqa: E402


def normalize(text: str) -> str:
    """Minúsculas, sin puntuación, con espacios colapsados; conserva acentos."""
    lowered = text.lower()
    cleaned = re.sub(r"[^\wáéíóúüñ]+", " ", lowered, flags=re.UNICODE)
    return re.sub(r"\s+", " ", cleaned).strip()


def word_error_rate(reference: str, hypothesis: str) -> float:
    ref = normalize(reference).split()
    hyp = normalize(hypothesis).split()
    if not ref:
        return 0.0 if not hyp else 1.0
    if not hyp:
        return 1.0

    previous = list(range(len(hyp) + 1))
    for i, ref_word in enumerate(ref, start=1):
        current = [i]
        for j, hyp_word in enumerate(hyp, start=1):
            cost = 0 if ref_word == hyp_word else 1
            current.append(
                min(
                    previous[j] + 1,          # borrado
                    current[j - 1] + 1,       # inserción
                    previous[j - 1] + cost,   # sustitución
                )
            )
        previous = current
    return previous[-1] / len(ref)


def load_glossary(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    terms = [term.strip() for term in re.split(r"[,\n;]+", text)]
    return [term for term in terms if term]


def _contains_term(normalized_text: str, normalized_term: str) -> bool:
    if not normalized_term:
        return False
    pattern = rf"(?<!\w){re.escape(normalized_term)}(?!\w)"
    return re.search(pattern, normalized_text) is not None


def glossary_accuracy(
    terms: list[str], reference: str, hypothesis: str
) -> tuple[float, int]:
    """Mide solo los términos del glosario que la referencia declara hablados.

    Usa límites de palabra para que `SHAP` no cuente como acierto dentro de
    `WindowSHAP`. Si la referencia no contiene términos del glosario, la
    métrica es 1.0 con cero términos esperados; no se penaliza al motor por
    términos que no se dijeron.
    """
    normalized_reference = normalize(reference)
    expected = [
        term
        for term in terms
        if _contains_term(normalized_reference, normalize(term))
    ]
    if not expected:
        return 1.0, 0

    normalized_hypothesis = normalize(hypothesis)
    hits = sum(
        1
        for term in expected
        if _contains_term(normalized_hypothesis, normalize(term))
    )
    return hits / len(expected), len(expected)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", required=True, type=Path)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--model", default="large-v3-turbo")
    parser.add_argument(
        "--glossary",
        default=str(engine.DEFAULT_GLOSSARY),
        help="Ruta al glosario usado para calcular aciertos.",
    )
    parser.add_argument(
        "--allow-download",
        action="store_true",
        help="Permite descargar el modelo si no está en caché (solo desarrollo).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.audio.exists():
        print(f"No se encuentra el audio: {args.audio}", file=sys.stderr)
        return 2
    if not args.reference.exists():
        print(
            f"No se encuentra la referencia: {args.reference}. "
            "Crea una transcripción corregida manualmente.",
            file=sys.stderr,
        )
        return 2

    os.environ["WHISPER_MODEL"] = args.model
    os.environ["WHISPER_LOCAL_FILES_ONLY"] = "0" if args.allow_download else "1"

    engine.reset_model()
    segments = engine.FasterWhisperEngine().run(args.audio, "es", None, None)
    hypothesis = " ".join(segment["text"] for segment in segments).strip()

    reference = args.reference.read_text(encoding="utf-8")
    terms = load_glossary(Path(args.glossary))
    accuracy, expected_terms = glossary_accuracy(terms, reference, hypothesis)

    result = {
        "model": args.model,
        "audio": str(args.audio),
        "reference": str(args.reference),
        "wer": round(word_error_rate(reference, hypothesis), 6),
        "glossary_accuracy": round(accuracy, 6),
        "glossary_terms_expected": expected_terms,
        "segments": len(segments),
        "words": sum(len(segment["words"]) for segment in segments),
        "hypothesis": hypothesis,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
