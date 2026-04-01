"""Utility helpers for probing video metadata using ffmpeg."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import ffmpeg


def _ensure_path(path: Path | str) -> Path:
    """Coerce arbitrary path-like input into a resolved Path object."""
    if isinstance(path, Path):
        return path
    return Path(path)


def _parse_fps(stream: Dict[str, Any]) -> float:
    """Extract frames-per-second as a float from a stream dict."""
    fps_text = stream.get("avg_frame_rate") or stream.get("r_frame_rate")
    if not fps_text or fps_text in {"0", "0/0"}:
        return 0.0
    num, _, den = fps_text.partition("/")
    try:
        numerator = float(num)
        denominator = float(den) if den else 1.0
        if denominator == 0:
            return 0.0
        return numerator / denominator
    except ValueError:
        return 0.0


def get_video_duration(video_path: Path | str) -> float:
    """Return the duration in seconds for the provided video file."""
    resolved_path = _ensure_path(video_path)
    try:
        probe = ffmpeg.probe(str(resolved_path))
    except ffmpeg.Error as exc:
        raise RuntimeError(f"Failed to probe video: {exc.stderr.decode(errors='ignore')}") from exc

    duration_text = probe.get("format", {}).get("duration")
    if duration_text is None:
        raise ValueError("Unable to determine video duration from metadata.")

    try:
        return float(duration_text)
    except ValueError as exc:
        raise ValueError("Video duration is not a valid float.") from exc


def get_video_info(video_path: Path | str) -> Dict[str, Any]:
    """Return key metadata (duration, dimensions, fps, audio presence) for a video."""
    resolved_path = _ensure_path(video_path)
    try:
        probe = ffmpeg.probe(str(resolved_path))
    except ffmpeg.Error as exc:
        raise RuntimeError(f"Failed to probe video: {exc.stderr.decode(errors='ignore')}") from exc

    format_data = probe.get("format", {})
    duration_text = format_data.get("duration")
    if duration_text is None:
        raise ValueError("Video metadata missing duration value.")

    try:
        duration = float(duration_text)
    except ValueError as exc:
        raise ValueError("Video duration is not a valid float.") from exc

    streams = probe.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video_stream is None:
        raise ValueError("No video stream found in file.")

    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))
    fps = _parse_fps(video_stream)
    has_audio = any(s.get("codec_type") == "audio" for s in streams)

    return {
        "duration": duration,
        "width": width,
        "height": height,
        "fps": fps,
        "has_audio": has_audio,
    }
