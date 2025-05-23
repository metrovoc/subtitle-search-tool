# Demo Guide - Subtitle Search Tool

## Quick Demo Steps

1. **Start the application**:

   ```bash
   ./run.sh
   ```

2. **Select test folder**:

   - Click "Browse" button
   - Select the `test_data` folder in this project

3. **Scan for subtitles**:

   - Click "Scan Subtitles" button
   - You should see "Found 2 subtitle files" in the status bar

4. **Search for text**:

   - Type "tool" in the search box
   - Press Enter or click "Search"
   - You should see results from both sample files

5. **Test jump functionality** (if you have video files):
   - Double-click on any search result
   - OR right-click and select "Jump to Video"
   - The tool will try to open the video at the exact timestamp

## Expected Results

### File Display Names

- Standalone subtitle files: `sample.srt`, `sample2.srt`
- Extracted MKV subtitles: `video.mkv [Track 0: en - English]`

### Search Features

- Case-sensitive/insensitive search
- Multiple file search
- Timestamp display
- Text preview

### Video Integration

- VLC Media Player (recommended)
- mpv player
- System default player
- Precise timestamp seeking

## Troubleshooting

### No video player found

Install VLC Media Player:

```bash
# macOS
brew install --cask vlc

# Ubuntu/Debian
sudo apt install vlc
```

### FFmpeg not found

Install FFmpeg:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```
