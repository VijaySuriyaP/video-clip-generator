
# YouTube Clip Generator

Generate short, subtitle-burned clips from long videos using local AI transcription and FFmpeg.

This app is built for creators who want to turn long-form recordings into social-ready highlights quickly.

## Why this project

- Fully local workflow after install (no cloud API required)
- Automatic clip picking using transcript density
- Burned subtitles and aspect ratio conversion for social platforms
- Batch output with individual clips plus a single ZIP download
- Real-time progress log in the UI

## Tech stack

- UI: Gradio 4+
- Transcription: openai-whisper (local model)
- Video processing: FFmpeg + ffmpeg-python
- Packaging: Python zipfile

## Project structure

```text
clip_generator_app/
|- app.py
|- requirements.txt
|- README.md
|- pipeline/
|  |- __init__.py
|  |- transcriber.py
|  |- scorer.py
|  |- subtitle_builder.py
|  |- extractor.py
|- utils/
   |- __init__.py
   |- ffprobe.py
   |- zipper.py
```

## Prerequisites

- Python 3.10 or newer
- FFmpeg available on PATH
  - Windows: https://ffmpeg.org/download.html
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

## Installation

```bash
git clone <your-repo-url>
cd clip_generator_app

# Optional but recommended
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

## Run

```bash
python app.py
```

The app launches at http://127.0.0.1:7860.

## How to use

1. Upload a video (MP4, MKV, MOV, AVI)
2. Choose number of clips and clip length
3. Select Whisper model size
4. Select aspect ratio and subtitle settings
5. Click Generate Clips
6. Watch progress in the log panel
7. Preview clips and download individual outputs or all clips as ZIP

## How clip selection works

1. Whisper transcribes video into word-level timestamps
2. A 1-second sliding window scores transcript density
3. Top non-overlapping windows are selected
4. SRT subtitles are generated per selected window
5. FFmpeg extracts clip, resizes, pads, and burns subtitles
6. Results are shown in a summary table and gallery

## Settings reference

| Setting | Description | Typical values |
|---|---|---|
| Number of Clips | How many highlights to produce | 3-10 |
| Clip Length | Duration of each highlight | 20-60 sec |
| Whisper Model | Accuracy vs speed tradeoff | tiny/base/small/medium/large |
| Aspect Ratio | Output canvas shape | 16:9, 9:16, 1:1 |
| Subtitle Font Size | Burned subtitle text size | 14-24 |
| Subtitle Position | Subtitle vertical position | bottom or top |

## Model size guide

| Model | Speed | Accuracy | Approx VRAM |
|---|---|---|---|
| tiny | Fastest | Low | ~1 GB |
| base | Fast | Medium | ~1 GB |
| small | Medium | Good | ~2 GB |
| medium | Slow | Great | ~5 GB |
| large | Slowest | Best | ~10 GB |

## Output

- Clip summary table (start/end/word count/preview)
- Individual MP4 files with burned subtitles
- `all_clips.zip` containing all generated clips

Generated clips are written to a temporary output directory during processing.

## Troubleshooting

### 127.0.0.1 refused to connect

- Make sure dependencies are installed in the same Python environment used to run `app.py`
- Verify app is running and listening on port 7860
- If needed, stop old processes and relaunch

### Video is not playable

- Regenerate clips after updating to latest code
- Ensure FFmpeg installation includes `libx264` and AAC support
- Confirm output is MP4 (`H.264` + `yuv420p` + `AAC`)

### ffmpeg not found

- Add FFmpeg `bin` folder to PATH
- Restart terminal and VS Code after PATH changes

### Whisper is slow or runs out of memory

- Use `tiny` or `base` model
- Close heavy apps
- Prefer shorter source videos for quick tests

## Privacy

This app runs locally on your machine. Video files and transcripts are processed on-device.

## Publish to GitHub

If this folder is not yet a git repository, run:

```bash
cd clip_generator_app
git init
git add .
git commit -m "Add YouTube Clip Generator app"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

## Acknowledgements

- openai-whisper
- FFmpeg
- Gradio
