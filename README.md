# Subtitle Search Tool

A GUI application to search text in subtitle files including embedded MKV subtitles with video playback integration.

## Features

- Browse and select folders containing subtitle files
- Support for multiple subtitle formats: SRT, VTT, ASS, SSA, SUB, SBV, TTML
- Extract and search embedded subtitles from MKV files
- **Smart filename display**: Shows original video filename for extracted subtitles with track information
- Case-sensitive and case-insensitive search
- Display search results with file name, timestamp, and matching text
- **Jump to video**: Double-click or right-click search results to jump to exact position in video
- Multi-threaded processing for responsive UI
- Support for multiple text encodings with automatic detection
- Cross-platform video player integration (VLC, mpv, system default)

## Requirements

- Python 3.9+
- FFmpeg (for MKV subtitle extraction)
- uv (for Python package management)
- **Recommended**: VLC Media Player (for best seeking support)

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

2. Install VLC Media Player (optional but recommended):

   ```bash
   # macOS
   brew install --cask vlc

   # Ubuntu/Debian
   sudo apt install vlc

   # Windows
   # Download from https://www.videolan.org/vlc/
   ```

3. Install Python dependencies using uv:
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

1. Click "Browse" to select a folder containing subtitle files and/or video files
2. Click "Scan Subtitles" to discover all subtitle files (including embedded MKV subtitles)
3. Enter search text and click "Search" or press Enter
4. Results will show matching lines with file names and timestamps
5. **Double-click** or **right-click** on any search result to jump to that exact moment in the video
6. Use "Case Sensitive" checkbox for exact case matching

### Video Playback Features

- **Smart filename display**: Extracted MKV subtitles show as "video.mkv [Track 0: en - English]"
- **Precise seeking**: Jump directly to subtitle timing in video
- **Multiple player support**: Tries VLC first (best), then mpv, then system default player
- **Cross-platform**: Works on macOS, Windows, and Linux

### Test Data

A sample subtitle file is included in `test_data/sample.srt` for testing the search functionality.

## Supported Formats

- **Standalone subtitle files**: .srt, .vtt, .ass, .ssa, .sub, .sbv, .ttml
- **Embedded subtitles**: MKV files with embedded subtitle tracks
- **Video formats**: Any format supported by FFmpeg (MKV, MP4, AVI, etc.)
- **Text encodings**: Automatic detection using chardet

## Video Players

The tool supports multiple video players with automatic detection:

1. **VLC Media Player** (recommended): Best seeking accuracy and format support
2. **mpv**: Lightweight player with good seeking support
3. **System default player**: Fallback option (may not support precise seeking)

## Troubleshooting

### Common Issues

#### "Display column #0 cannot be set" Error

This error has been fixed in the latest version. If you encounter it:

- Make sure you're using the latest version of the tool
- Try restarting the application

#### Video jump not working

- Install VLC Media Player for best results
- Check that the video file exists in the same location
- Ensure FFmpeg is installed for MKV subtitle extraction

#### No subtitle files found

- Check that the folder contains subtitle files (.srt, .vtt, .ass, etc.)
- For MKV files, ensure FFmpeg is properly installed
- Try scanning a different folder

#### Encoding issues with subtitle files

- The tool uses automatic encoding detection
- If characters appear garbled, the file might use an unsupported encoding
- Try converting the subtitle file to UTF-8

## License

MIT License
