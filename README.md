# 🎬 YTClip - Professional CLI Video Tool

**YTClip** is a powerful command-line tool designed for content creators who need to quickly process videos for TikTok, Instagram Reels, and YouTube Shorts.

## ✨ Features

- 📥 **YouTube Downloader** - Download videos in highest quality with yt-dlp
- ✂️ **Smart Clipping** - Precise timestamp-based video cutting
- 🎯 **Smart Crop** - AI-powered face detection for optimal 9:16 framing
- 📱 **Platform Presets** - Pre-configured settings for TikTok, Reels, and Shorts
- ⚡ **High Performance** - Single-pass ffmpeg processing
- 🎨 **No Watermarks** - Clean professional output

## 🚀 Installation

### Prerequisites

1. **FFmpeg** (required)
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt update && sudo apt install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

2. **Python 3.8+**

### Install YTClip

```bash
# Clone repository
git clone https://github.com/yourusername/ytclip.git
cd ytclip

# Install core dependencies
pip install -r requirements.txt

# Optional: Install smart crop support
pip install -r requirements-optional.txt

# Install as CLI tool
pip install -e .
```

## 📖 Usage

### Basic Commands

#### Download and clip from YouTube
```bash
ytclip "https://youtube.com/watch?v=VIDEO_ID" \
  --start 00:01:30 \
  --end 00:02:45 \
  --preset tiktok \
  --output viral.mp4
```

#### Clip local video file
```bash
ytclip video.mp4 \
  --start 10 \
  --end 40 \
  --preset reels \
  --output reel.mp4
```

#### Use smart crop (face detection)
```bash
ytclip video.mp4 \
  --start 00:00:05 \
  --end 00:00:30 \
  --smart-crop \
  --preset shorts \
  --output short.mp4
```

#### Force center crop (no face detection)
```bash
ytclip video.mp4 \
  --start 15 \
  --end 45 \
  --center-crop \
  --preset tiktok \
  --output clip.mp4
```

#### Keep original aspect ratio
```bash
ytclip video.mp4 \
  --start 00:00:10 \
  --end 00:01:00 \
  --no-crop \
  --output original.mp4
```

### Advanced Options

#### Override preset settings
```bash
ytclip video.mp4 \
  --start 5 \
  --end 35 \
  --preset tiktok \
  --fps 60 \
  --crf 15 \
  --output high-quality.mp4
```

#### Verbose mode for debugging
```bash
ytclip video.mp4 \
  --start 0 \
  --end 30 \
  --preset reels \
  --verbose \
  --output debug.mp4
```

## 🎯 Platform Presets

### TikTok
- Resolution: 1080x1920
- FPS: 30
- Quality: CRF 18 (high quality)
- Audio: 192kbps AAC

```bash
--preset tiktok
```

### Instagram Reels
- Resolution: 1080x1920
- FPS: 30
- Quality: CRF 20 (balanced)
- Audio: 192kbps AAC

```bash
--preset reels
```

### YouTube Shorts
- Resolution: 1080x1920
- FPS: Source FPS
- Quality: CRF 18 (high quality)
- Audio: 192kbps AAC

```bash
--preset shorts
```

## 🔧 Configuration Options

### Timestamp Formats

All formats supported:
- `HH:MM:SS` - Hours:Minutes:Seconds (e.g., `01:30:45`)
- `MM:SS` - Minutes:Seconds (e.g., `2:30`)
- `SS` - Seconds only (e.g., `45`)

### Crop Modes

- `--smart-crop` - AI face detection (default)
- `--center-crop` - Center crop without detection
- `--no-crop` - Keep original aspect ratio

### Quality Settings

- `--crf <number>` - Quality (lower = better, 15-23 recommended)
- `--fps <number>` - Frames per second
- `--bitrate <value>` - Video bitrate (e.g., `5M`)

## 🎨 Smart Crop

Smart crop uses OpenCV face detection to automatically frame subjects optimally:

1. **Detects faces** in sample frames
2. **Calculates optimal crop** region centered on faces
3. **Maintains 9:16 aspect ratio** for vertical video
4. **Adds padding** above face for better composition
5. **Fallback to center crop** if no faces detected

To disable smart crop and use center crop:
```bash
ytclip video.mp4 --center-crop ...
```

## ⚡ Performance Tips

### Fast Seeking
YTClip uses input seeking (`-ss` before `-i`) for fast processing:
```bash
# ✅ Fast - seeks before decoding
ytclip video.mp4 --start 00:10:00 ...

# Processes only from start point forward
```

### Single-Pass Processing
All operations (clip, crop, scale, encode) happen in one ffmpeg pass:
- Crop → Scale → Encode (single command)
- No intermediate files
- Maximum efficiency

### Batch Processing
Process multiple clips with bash:
```bash
#!/bin/bash
for i in {1..5}; do
  start=$((i * 60))
  end=$(((i + 1) * 60))
  ytclip video.mp4 \
    --start $start \
    --end $end \
    --preset tiktok \
    --output clip_${i}.mp4
done
```

## 📁 File Structure

```
ytclip/
├── ytclip/
│   ├── __init__.py
│   ├── cli.py              # CLI interface
│   ├── downloader.py       # YouTube download
│   ├── processor.py        # Video processing
│   ├── smart_crop.py       # Face detection
│   ├── presets.py          # Platform presets
│   └── utils.py            # Utilities
├── requirements.txt
├── requirements-optional.txt
├── setup.py
└── README.md
```

## 🐛 Troubleshooting

### FFmpeg not found
```bash
# Verify installation
ffmpeg -version
ffprobe -version

# Add to PATH if needed
export PATH="/usr/local/bin:$PATH"
```

### Smart crop not working
```bash
# Install OpenCV
pip install opencv-python numpy

# Or use center crop instead
ytclip video.mp4 --center-crop ...
```

### Download fails
```bash
# Update yt-dlp
pip install --upgrade yt-dlp

# Check URL is valid
yt-dlp --list-formats "URL"
```

## 📊 Examples

### Quick TikTok Clip
```bash
ytclip "https://youtube.com/watch?v=abc123" \
  -s 00:01:15 -e 00:01:45 \
  -p tiktok -o tiktok.mp4
```

### High Quality Reel
```bash
ytclip video.mp4 \
  --start 30 --end 90 \
  --preset reels \
  --crf 15 --fps 60 \
  --smart-crop \
  --output reel-hq.mp4
```

### Fast Processing
```bash
ytclip video.mp4 \
  --start 0 --end 30 \
  --preset fast \
  --center-crop \
  --output quick.mp4
```

## 📝 Legal Notice

This tool is intended for:
- **Personal use** - Processing your own content
- **Educational purposes** - Learning video processing
- **Fair use** - Commentary, criticism, education

**User Responsibility:**
- Only process content you have rights to
- Respect copyright and platform terms
- This tool does not bypass DRM or platform protection

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Submit pull request

## 📄 License

MIT License - See LICENSE file

## 🙏 Credits

Built with:
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [FFmpeg](https://ffmpeg.org/) - Video processing
- [OpenCV](https://opencv.org/) - Face detection
- [Click](https://click.palletsprojects.com/) - CLI framework

---

Made with ❤️ for content creators
