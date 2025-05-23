# Subtitle Search Tool

A GUI application to search text in subtitle files including embedded MKV subtitles.

## Features

- Browse and select folders containing subtitle files
- Support for multiple subtitle formats: SRT, VTT, ASS, SSA, SUB, SBV, TTML
- Extract and search embedded subtitles from MKV files
- Case-sensitive and case-insensitive search
- Display search results with file name, timestamp, and matching text
- Multi-threaded processing for responsive UI
- Support for multiple text encodings with automatic detection

## Requirements

- Python 3.9+
- FFmpeg (for MKV subtitle extraction)
- uv (for Python package management)

## Installation

1. Install FFmpeg:

   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt install ffmpeg

   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

2. Install Python dependencies using uv:
   ```bash
   uv sync
   ```

## Usage

### Quick Start

```bash
# Make script executable (first time only)
chmod +x run.sh

# Run the application
./run.sh
```

### Manual Start

```bash
uv run python subtitle_search_tool.py
```

### How to Use

1. Click "Browse" to select a folder containing subtitle files
2. Click "Scan Subtitles" to discover all subtitle files (including embedded MKV subtitles)
3. Enter search text and click "Search" or press Enter
4. Results will show matching lines with file names and timestamps
5. Use "Case Sensitive" checkbox for exact case matching

### Test Data

A sample subtitle file is included in `test_data/sample.srt` for testing the search functionality.

## Supported Formats

- **Standalone subtitle files**: .srt, .vtt, .ass, .ssa, .sub, .sbv, .ttml
- **Embedded subtitles**: MKV files with embedded subtitle tracks
- **Text encodings**: Automatic detection using chardet

## License

MIT License
