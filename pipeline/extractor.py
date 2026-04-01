"""Clip extraction with ffmpeg filters and subtitle burning."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import subprocess
from typing import Tuple

import ffmpeg

ASPECT_TARGETS: dict[str, Tuple[int, int]] = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
}


@lru_cache(maxsize=8)
def _has_audio(path: Path) -> bool:
    """Return True if the input video contains an audio stream."""
    try:
        probe = ffmpeg.probe(str(path))
    except ffmpeg.Error:
        return False
    return any(stream.get("codec_type") == "audio" for stream in probe.get("streams", []))


def extract_clip(
    input_path: Path | str,
    start: float,
    duration: float,
    output_path: Path | str,
    srt_path: Path | str,
    aspect_ratio: str,
    subtitle_size: int,
    subtitle_position: str,
) -> None:
    """Use ffmpeg to cut, format, and subtitle a clip, saving it to disk."""
    source = Path(input_path)
    destination = Path(output_path)
    subtitles = Path(srt_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    target = ASPECT_TARGETS.get(aspect_ratio, ASPECT_TARGETS["16:9"])
    width, height = target

    input_stream = ffmpeg.input(str(source), ss=start, t=duration)
    video_stream = (
        input_stream.video
        .filter_("scale", width, height, force_original_aspect_ratio="decrease")
        .filter_("pad", width, height, "(ow-iw)/2", "(oh-ih)/2")
    )

    alignment = 2 if subtitle_position == "bottom" else 8
    force_style = (
        f"FontSize={subtitle_size},"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "Outline=2,"
        f"Alignment={alignment}"
    )

    video_stream = video_stream.filter_(
        "subtitles",
        filename=subtitles.name,
        force_style=force_style,
    )

    include_audio = _has_audio(source)
    output_kwargs = {
        "vcodec": "libx264",
        "preset": "fast",
        "crf": 23,
        "pix_fmt": "yuv420p",
        "movflags": "+faststart",
    }
    if include_audio:
        audio_stream = input_stream.audio
        output_kwargs.update({"acodec": "aac", "audio_bitrate": "128k"})
        streams = [video_stream, audio_stream]
    else:
        output_kwargs["an"] = None
        streams = [video_stream]

    out = ffmpeg.output(*streams, str(destination), **output_kwargs)
    cmd = ffmpeg.compile(out.overwrite_output())

    try:
        completed = subprocess.run(
            cmd,
            cwd=str(subtitles.parent),
            check=True,
            capture_output=True,
        )
        _ = completed
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.decode(errors="ignore") if exc.stderr else str(exc)
        raise RuntimeError(f"ffmpeg failed to extract clip: {message}") from exc
