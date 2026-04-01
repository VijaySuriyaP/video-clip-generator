"""Gradio desktop app for generating word-dense YouTube clips."""
from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any, Iterable, List, Sequence

import gradio as gr

from pipeline.extractor import extract_clip
from pipeline.scorer import score_windows, select_top_clips
from pipeline.subtitle_builder import build_srt
from pipeline.transcriber import transcribe_video
from utils.ffprobe import get_video_info
from utils.zipper import zip_clips


def _ensure_path(file_obj: Any) -> Path:
    """Normalize Gradio file inputs into a Path instance."""
    if isinstance(file_obj, Path):
        return file_obj
    if isinstance(file_obj, str):
        return Path(file_obj)
    if isinstance(file_obj, dict) and "name" in file_obj:
        return Path(file_obj["name"])
    if hasattr(file_obj, "name"):
        return Path(str(file_obj.name))
    raise ValueError("Unsupported file input type.")


def _format_timestamp(seconds: float) -> str:
    """Return a mm:ss string for a timestamp in seconds."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def generate_clips(
    video_file: Any,
    num_clips: int,
    clip_length: float,
    model_size: str,
    aspect_ratio: str,
    subtitle_size: int,
    subtitle_position: str,
) -> Generator[tuple[str, Any, Any, Any], None, None]:
    """Generator powering the Gradio UI with streaming progress updates."""
    log = ""

    def push(message: str) -> str:
        nonlocal log
        log += message
        return log

    if video_file is None:
        yield (push("Please upload a video file first.\n"), None, None, None)
        return

    try:
        source_path = _ensure_path(video_file)
    except Exception as exc:  # noqa: BLE001
        yield (push(f"Unable to read uploaded file: {exc}\n"), None, None, None)
        return

    if not source_path.exists():
        yield (push("Uploaded video file could not be found on disk.\n"), None, None, None)
        return

    if clip_length <= 0:
        yield (push("Clip length must be greater than zero.\n"), None, None, None)
        return

    output_dir = Path(tempfile.mkdtemp(prefix="clipgen_"))

    try:
        yield (push("Analyzing video...\n"), None, None, None)
        info = get_video_info(source_path)
        duration = float(info["duration"])
        if clip_length > duration:
            yield (
                push("Clip length cannot exceed the total video duration.\n"),
                None,
                None,
                None,
            )
            return
        push(f"Video duration: {duration:.1f}s | Has audio: {info['has_audio']}\n")
        yield (log, None, None, None)

        push(f"Loading Whisper model '{model_size}'... (this may take a moment)\n")
        yield (log, None, None, None)

        def whisper_callback(message: str) -> None:
            push(message + "\n")

        words = transcribe_video(source_path, model_size, progress_callback=whisper_callback)
        yield (log, None, None, None)

        push("Scoring clip windows...\n")
        yield (log, None, None, None)
        windows = score_windows(words, clip_length, duration)
        clips = select_top_clips(windows, num_clips)
        push(f"Selected {len(clips)} clips.\n")
        yield (log, None, None, None)

        clip_paths: List[str] = []
        table_rows: List[List[Any]] = []

        for idx, clip in enumerate(clips, start=1):
            clip_filename = f"clip_{idx:02d}.mp4"
            clip_path = output_dir / clip_filename
            srt_path = output_dir / f"clip_{idx:02d}.srt"

            push(f"Generating clip {idx}/{len(clips)}: {clip_filename}...\n")
            yield (log, None, None, None)

            build_srt(clip["words_in_window"], float(clip["start"]), srt_path)

            extract_clip(
                input_path=source_path,
                start=float(clip["start"]),
                duration=clip_length,
                output_path=clip_path,
                srt_path=srt_path,
                aspect_ratio=aspect_ratio,
                subtitle_size=subtitle_size,
                subtitle_position=subtitle_position,
            )

            clip_paths.append(str(clip_path))
            start_fmt = _format_timestamp(float(clip["start"]))
            end_fmt = _format_timestamp(float(clip["start"]) + clip_length)
            preview = " ".join(word["word"] for word in clip["words_in_window"][:20])

            table_rows.append(
                [
                    clip_filename,
                    start_fmt,
                    end_fmt,
                    clip["word_count"],
                    round(float(clip["words_per_second"]), 2),
                    preview,
                ]
            )

            push(f"Clip {idx} done.\n")
            yield (log, None, None, None)

        if not clip_paths:
            push("No clips were generated.\n")
            yield (log, [], [], None)
            return

        push("Creating ZIP archive...\n")
        yield (log, None, None, None)
        zip_path = zip_clips(clip_paths, output_dir / "all_clips.zip")

        push(f"Done! {len(clip_paths)} clips generated.\n")
        gallery_items = [(path, Path(path).name) for path in clip_paths]
        yield (log, table_rows, gallery_items, zip_path)
    except Exception as exc:  # noqa: BLE001
        yield (push(f"Error: {exc}\n"), None, None, None)


def build_ui() -> gr.Blocks:
    """Construct and return the Gradio Blocks interface."""
    with gr.Blocks(title="🎬 YouTube Clip Generator") as demo:
        gr.Markdown("""# 🎬 YouTube Clip Generator\nUpload a video → auto-generate the most word-dense clips with subtitles""")

        with gr.Row():
            with gr.Column():
                video_input = gr.Video(label="Upload Video", sources=["upload"], interactive=True)
                generate_btn = gr.Button("Generate Clips", variant="primary", size="lg")

            with gr.Column():
                num_clips_slider = gr.Slider(
                    minimum=1,
                    maximum=20,
                    value=5,
                    step=1,
                    label="Number of Clips",
                )
                clip_length_slider = gr.Slider(
                    minimum=10,
                    maximum=120,
                    value=45,
                    step=5,
                    label="Clip Length (seconds)",
                )
                model_dropdown = gr.Dropdown(
                    choices=["tiny", "base", "small", "medium", "large"],
                    value="base",
                    label="Whisper Model (larger = more accurate, slower)",
                )
                aspect_dropdown = gr.Dropdown(
                    choices=["16:9", "9:16", "1:1"],
                    value="16:9",
                    label="Aspect Ratio",
                )
                subtitle_size_slider = gr.Slider(
                    minimum=12,
                    maximum=32,
                    value=18,
                    step=1,
                    label="Subtitle Font Size",
                )
                subtitle_position_radio = gr.Radio(
                    choices=["bottom", "top"],
                    value="bottom",
                    label="Subtitle Position",
                )

        progress_log = gr.Textbox(
            label="Progress Log",
            lines=6,
            interactive=False,
            autoscroll=True,
            value="",
        )

        summary_table = gr.Dataframe(
            headers=["Clip", "Start", "End", "Words", "Words/sec", "Preview"],
            label="Clip Summary",
            interactive=False,
            value=[],
        )

        clip_gallery = gr.Gallery(
            label="Generated Clips",
            show_label=True,
            columns=[2],
            height="auto",
        )

        zip_download = gr.File(label="Download All Clips (ZIP)")

        generate_btn.click(
            fn=generate_clips,
            inputs=[
                video_input,
                num_clips_slider,
                clip_length_slider,
                model_dropdown,
                aspect_dropdown,
                subtitle_size_slider,
                subtitle_position_radio,
            ],
            outputs=[
                progress_log,
                summary_table,
                clip_gallery,
                zip_download,
            ],
        )

    return demo


demo = build_ui()

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True, share=False)
