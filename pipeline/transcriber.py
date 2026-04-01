"""Whisper-powered transcription utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional

import whisper

ProgressCallback = Optional[Callable[[str], None]]


def transcribe_video(video_path: Path | str, model_size: str, progress_callback: ProgressCallback = None) -> List[Dict[str, float | str]]:
    """Transcribe a video using Whisper and return a list of word-level timestamps."""
    source_path = Path(video_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Video file not found: {source_path}")

    model = whisper.load_model(model_size)
    try:
        result = model.transcribe(
            str(source_path),
            word_timestamps=True,
            verbose=False,
        )
    except Exception as exc:  # whisper raises generic Exception variants
        raise RuntimeError(f"Whisper transcription failed: {exc}") from exc

    words: List[Dict[str, float | str]] = []
    for segment in result.get("segments", []):
        for word in segment.get("words", []):
            start = word.get("start")
            end = word.get("end")
            text = (word.get("word") or "").strip()
            if not text:
                continue
            if start is None or end is None:
                continue
            try:
                start_f = float(start)
                end_f = float(end)
            except (TypeError, ValueError):
                continue
            words.append({"word": text, "start": start_f, "end": end_f})

    if progress_callback:
        progress_callback(f"Transcription complete. {len(words)} words found.")

    return words
