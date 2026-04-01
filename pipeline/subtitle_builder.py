"""Subtitle generation helpers for the extracted clips."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

Word = Dict[str, float | str]


SENTENCE_ENDINGS = {".", "!", "?", "…"}


def seconds_to_srt_time(seconds: float) -> str:
    """Convert seconds into the SRT timestamp format HH:MM:SS,mmm."""
    if seconds < 0:
        seconds = 0
    total_milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(total_milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def build_srt(words: List[Word], clip_start: float, output_path: Path | str) -> str:
    """Create an SRT file for the clip's words and return its textual contents."""
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    adjusted_words: List[Word] = []
    for word in words:
        start = float(word["start"]) - clip_start
        end = float(word["end"]) - clip_start
        adjusted_words.append({"word": str(word["word"]), "start": max(0.0, start), "end": max(0.0, end)})

    entries: List[dict] = []
    current_block: List[Word] = []

    def flush_block() -> None:
        if not current_block:
            return
        start_time = seconds_to_srt_time(float(current_block[0]["start"]))
        end_time = seconds_to_srt_time(float(current_block[-1]["end"]))
        text = " ".join(str(word["word"]) for word in current_block).strip()
        if text:
            entries.append({"start": start_time, "end": end_time, "text": text})
        current_block.clear()

    for word in adjusted_words:
        current_block.append(word)
        text = str(word["word"])
        if len(current_block) >= 8 or text[-1:] in SENTENCE_ENDINGS:
            flush_block()

    flush_block()

    lines: List[str] = []
    for idx, entry in enumerate(entries, start=1):
        lines.extend([
            str(idx),
            f"{entry['start']} --> {entry['end']}",
            entry["text"],
            "",
        ])

    content = "\n".join(lines).strip() + "\n"
    out_path.write_text(content, encoding="utf-8")
    return content
