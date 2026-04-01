"""Helpers for packaging generated clips into a ZIP archive."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable
from zipfile import ZIP_DEFLATED, ZipFile


def zip_clips(clip_paths: Iterable[Path | str], output_zip_path: Path | str) -> str:
    """Bundle clip files into a single ZIP archive and return its filesystem path."""
    out_path = Path(output_zip_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    clip_path_list = [Path(path) for path in clip_paths]
    if not clip_path_list:
        raise ValueError("No clip files were provided to zip.")

    with ZipFile(out_path, mode="w", compression=ZIP_DEFLATED) as archive:
        for clip_path in clip_path_list:
            archive.write(clip_path, arcname=clip_path.name)

    return str(out_path)
