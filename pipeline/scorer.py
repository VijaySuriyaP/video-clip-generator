"""Scoring utilities that find the most word-dense windows in a transcript."""
from __future__ import annotations

from typing import Dict, List


Window = Dict[str, object]
Word = Dict[str, float | str]


def score_windows(words: List[Word], clip_length: float, video_duration: float) -> List[Window]:
    """Return sliding windows scored by the number of words they fully contain."""
    if clip_length <= 0:
        raise ValueError("Clip length must be positive.")
    if video_duration <= 0:
        raise ValueError("Video duration must be positive.")
    if clip_length > video_duration:
        raise ValueError("Clip length cannot exceed video duration.")

    windows: List[Window] = []
    start_time = 0.0
    max_start = video_duration - clip_length
    while start_time <= max_start + 1e-6:
        end_time = start_time + clip_length
        words_in_window = [
            word
            for word in words
            if float(word["start"]) >= start_time and float(word["end"]) <= end_time
        ]
        word_count = len(words_in_window)
        windows.append(
            {
                "start": start_time,
                "end": end_time,
                "word_count": word_count,
                "words_per_second": word_count / clip_length,
                "words_in_window": words_in_window,
            }
        )
        start_time += 1.0

    windows.sort(key=lambda w: (-int(w["word_count"]), float(w["start"])) )
    return windows


def _overlaps(a: Window, b: Window) -> bool:
    """Return True if two windows overlap in time."""
    return float(a["start"]) < float(b["end"]) and float(a["end"]) > float(b["start"])


def select_top_clips(windows: List[Window], n: int) -> List[Window]:
    """Greedily choose the top N non-overlapping windows."""
    if n <= 0:
        return []

    selected: List[Window] = []
    for window in sorted(windows, key=lambda w: (-int(w["word_count"]), float(w["start"]))):
        if any(_overlaps(window, existing) for existing in selected):
            continue
        selected.append(window)
        if len(selected) >= n:
            break

    selected.sort(key=lambda w: float(w["start"]))
    return selected
