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
- **High-performance search**: Intelligent caching and parallel processing for fast searches
- **Smart pre-loading**: Background subtitle parsing for instant search results

## Requirements

- Python 3.9+
- FFmpeg (for MKV subtitle extraction)
- uv (for Python package management)
- **Recommended**: IINA (macOS) or VLC Media Player (for best seeking support)

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

2. Install video player (optional but recommended):

   ```bash
   # macOS - IINA (recommended for macOS users)
   brew install --cask iina

   # macOS/Linux/Windows - VLC Media Player
   brew install --cask vlc          # macOS
   sudo apt install vlc             # Ubuntu/Debian
   # Windows: Download from https://www.videolan.org/vlc/
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
- **Multiple player support**: Tries IINA (macOS), VLC, mpv, then system default player
- **Cross-platform**: Works on macOS, Windows, and Linux

### Performance Features

- **Intelligent caching**: Parsed subtitle files are cached in memory for instant re-search
- **Parallel processing**: Multiple files searched simultaneously using ThreadPoolExecutor
- **Smart pre-loading**: Subtitle files are parsed in background after scanning
- **Optimized encoding detection**: Enhanced encoding detection with 32KB sample for better accuracy
- **Fast search algorithms**: Cached text searching with compiled regex patterns
- **Memory management**: Automatic cache invalidation when files are modified
- **Robust fallback**: Multiple parsing methods ensure no text is missed
- **Search validation**: Built-in accuracy verification and detailed logging

### Test Data

A sample subtitle file is included in `test_data/sample.srt` for testing the search functionality.

## Supported Formats

- **Standalone subtitle files**: .srt, .vtt, .ass, .ssa, .sub, .sbv, .ttml
- **Embedded subtitles**: MKV files with embedded subtitle tracks
- **Video formats**: Any format supported by FFmpeg (MKV, MP4, AVI, etc.)
- **Text encodings**: Automatic detection using chardet

## Video Players

The tool supports multiple video players with automatic detection:

1. **IINA** (macOS only, recommended): Modern player with mpv backend, excellent seeking accuracy
2. **VLC Media Player** (cross-platform): Best seeking accuracy and format support across all platforms
3. **mpv**: Lightweight player with good seeking support
4. **System default player**: Fallback option (may not support precise seeking)

**Player Priority on macOS**: IINA → VLC → mpv → System default  
**Player Priority on other platforms**: VLC → mpv → System default

## Troubleshooting

### Common Issues

#### "Display column #0 cannot be set" Error

This error has been fixed in the latest version. If you encounter it:

- Make sure you're using the latest version of the tool
- Try restarting the application

#### Video jump not working

- Install IINA (macOS) or VLC Media Player for best results
- Check that the video file exists in the same location
- Ensure FFmpeg is installed for MKV subtitle extraction

#### No subtitle files found

- Check that the folder contains subtitle files (.srt, .vtt, .ass, etc.)
- For MKV files, ensure FFmpeg is properly installed
- Try scanning a different folder

#### Encoding issues with subtitle files

- The tool uses enhanced encoding detection with multiple fallback methods
- If characters appear garbled, the file might use an unsupported encoding
- Try converting the subtitle file to UTF-8

#### Slow search performance

- The tool now uses intelligent caching and parallel processing
- First search may be slower as files are parsed and cached
- Subsequent searches should be much faster using cached data

#### Missing search results

- The tool now includes enhanced fallback parsing methods
- Multiple encoding detection strategies ensure maximum text coverage
- Enable debug output to see detailed search statistics

### No video player found

Install a compatible video player:

```bash
# macOS - IINA (recommended)
brew install --cask iina

# Cross-platform - VLC Media Player
brew install --cask vlc      # macOS
sudo apt install vlc         # Ubuntu/Debian
```

## License

MIT License
