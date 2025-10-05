

# 🎥 YouTube → TikTok Clips Creator

Automatically download YouTube videos, split them into vertical TikTok-ready clips, add watermarks, generate thumbnails, and optionally upload them to TikTok.

---

## ✨ Features

* 📥 Download YouTube videos in high quality
* ✂️ Split videos into custom-length clips
* 📱 Auto-resize to vertical format (1080×1920)
* 🖼️ Add custom watermark/logo
* 🎬 Generate thumbnails for each clip
* 📊 Create summary JSON with metadata
* 🚀 Optional TikTok auto-upload
* 🎯 Process specific parts only

---

## 🛠️ Prerequisites

* **Python 3.7+**
* **FFmpeg** (must be installed and in your PATH)

### Installing FFmpeg

**Windows:**

```bash
# Using Chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
```

**macOS:**

```bash
brew install ffmpeg
```

**Linux:**

```bash
sudo apt update
sudo apt install ffmpeg
```

---

## 📦 Installation

1. Clone or download this repository.
2. Install required Python packages:

```bash
pip install pytubefix moviepy tqdm pillow python-slugify
```

3. Create a `config.json` file:

```json
{
  "clip_duration": 60
}
```

4. (Optional) Add a `logo.png` file in the same directory for watermarking.

---

## 🚀 Usage

### Basic Usage

```bash
python script.py --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Custom Clip Duration

```bash
python script.py --url "https://www.youtube.com/watch?v=VIDEO_ID" --clip-duration 45
```

### Process Specific Parts Only

```bash
# Only process parts 1, 3, and 5
python script.py --url "https://www.youtube.com/watch?v=VIDEO_ID" --parts 1 3 5
```

### With TikTok Upload

```bash
python script.py --url "https://www.youtube.com/watch?v=VIDEO_ID" --upload-tiktok
```

---

## ⚙️ Command Line Arguments

| Argument          | Required | Default          | Description                                      |
| ----------------- | -------- | ---------------- | ------------------------------------------------ |
| `--url`           | Yes      | -                | YouTube video URL                                |
| `--clip-duration` | No       | From config.json | Length of each clip in seconds                   |
| `--parts`         | No       | All parts        | Specific part numbers to process (e.g., `1 2 3`) |
| `--upload-tiktok` | No       | False            | Upload clips to TikTok after processing          |

---

## 📁 Output Structure

```
video-title_20250105_1430/
├── part_1.mp4
├── part_2.mp4
├── part_3.mp4
├── thumb_part_1.png
├── thumb_part_2.png
├── thumb_part_3.png
└── summary.json
```

### Summary.json Format

```json
{
  "title": "Video Title",
  "total_parts": 5,
  "duration": 300,
  "clips": [
    "/path/to/part_1.mp4",
    "/path/to/part_2.mp4",
    "/path/to/part_3.mp4"
  ]
}
```

---

## ⚙️ Configuration

### `config.json`

```json
{
  "clip_duration": 60,
  "resolution": "720p",
  "target_width": 1080,
  "target_height": 1920
}
```

### Logo / Watermark

* Place `logo.png` in the same folder as the script.
* Resized to **120px height**, maintaining aspect ratio
* Positioned at **bottom-right corner**
* Applied to all video clips

> To disable watermark, remove or rename `logo.png`.

---

## 📲 TikTok Upload (Optional)

* Install and configure `tiktok_upload`:

```bash
pip install tiktok-uploader
```

* Follow the module documentation to set up your TikTok credentials.

---

## 🛠️ Troubleshooting

### Video loading issues

* Ensure FFmpeg is installed and in PATH
* Check the downloaded video is not corrupted

### Resize / crop fails

* Script falls back to original resolution
* Verify FFmpeg installation

### Clips not saved

* Check write permissions and disk space
* Review console for errors

### Slow processing

* Reduce bitrate or resolution
* Process specific parts using `--parts`

---

## 💡 Tips

1. Test with a single part: `--parts 1`
2. Resume interrupted processing: existing clips are skipped automatically
3. Optimal clip duration: 45–60 seconds for TikTok
4. Thumbnails extracted at **1-second mark**
5. Batch processing example:

```bash
#!/bin/bash
python script.py --url "URL1" --clip-duration 60
python script.py --url "URL2" --clip-duration 45
```

---

## 📦 Requirements.txt

```
pytubefix>=6.0.0
moviepy>=1.0.3
tqdm>=4.65.0
pillow>=10.0.0
python-slugify>=8.0.0
```

---

## 📜 License

MIT License – free to use and modify.

---

## ⚠️ Disclaimer

* Respect YouTube’s Terms of Service
* Only download content you have rights to use
* TikTok uploads must comply with community guidelines

---

## 🆘 Support

* Check FFmpeg: `ffmpeg -version`
* Verify Python packages: `pip list`
* Inspect console output for errors
* Check file permissions in output folder

