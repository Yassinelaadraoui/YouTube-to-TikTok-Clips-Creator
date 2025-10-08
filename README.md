

---
# 🎬 YouTube → TikTok Clip Maker

A **Python automation script** that turns long YouTube videos into **short clips** ready for **TikTok, Instagram Reels, or YouTube Shorts** — with custom titles, logo overlays, and optional highlight extraction.

---

## ✨ Features

✅ **Split long videos automatically** into 90-second (or custom-length) clips  
✅ **Download highest-quality video + audio** with automatic merging (via FFmpeg)  
✅ **Add text and logo overlays** (with safe fallbacks)  
✅ **Highlight mode** – extract a short 15s highlight from the middle of the video  
✅ **Windows-safe rendering** (non-blocking, visible progress bars)  
✅ **Smart resume** – skips already processed parts  
✅ **Automatic folder naming** by title and timestamp  
✅ **Debug-friendly logging** at every step  
✅ **JSON summary** of all generated clips  

---

## 🧱 Requirements

Make sure you have these installed:

### 1️⃣ Python 3.10+
Download from [python.org/downloads](https://www.python.org/downloads/)

### 2️⃣ FFmpeg (required for merging video + audio)
Install it via:
```bash
choco install ffmpeg
````

or [download manually](https://ffmpeg.org/download.html) and add it to your PATH.

### 3️⃣ ImageMagick (optional, only if you want text rendering via `TextClip`)

> Not required by default (we use PIL overlays), but you can still install it:

```bash
choco install imagemagick
```

### 4️⃣ Dependencies

Install all required packages:

```bash
pip install moviepy pillow pytubefix python-slugify tqdm
```

---

## ⚙️ Setup

1. Clone or download this project.
2. Place your **logo.png** in the same directory as `main.py`.
3. (Optional) Edit `config.json` to set default clip duration:

```json
{
  "clip_duration": 90
}
```

---

## 🚀 Usage

Run the script from your terminal:

```bash
python main.py
```

Then follow the interactive prompts:

| Prompt           | Description                                                                  |
| ---------------- | ---------------------------------------------------------------------------- |
| 🔗 YouTube URL   | Paste any YouTube video link                                                 |
| 📝 Custom Title  | Enter a custom name for your clips                                           |
| ⏱️ Clip Duration | Set duration in seconds (default 90)                                         |
| 🎯 Mode          | Press **Enter** for full split, type **h** for highlight, or number of parts |

---

### 🧩 Examples

#### ▶️ Full split into 90s clips

```bash
python main.py
🔗 https://www.youtube.com/watch?v=abc123
📝 Solo 2 Days Eating Only What I Catch
⏱️ 90
🎯 [Enter]
```

Output:

```
/solo-2-days-eating-only-what-i-catch_20251008_2111/
 ├── part_1.mp4
 ├── part_2.mp4
 ├── ...
 └── summary.json
```

#### ✂️ Highlight mode (15s short)

```bash
🎯 h
```

Output:

```
highlight.mp4
```

#### 🔢 Specific number of parts

```bash
🎯 3
```

→ Will process only 3 parts, regardless of total duration.

---

## 🧠 How It Works

1. **Download video & audio** separately from YouTube (highest quality).
2. **Merge** them using FFmpeg.
3. **Split** into chunks or highlight.
4. **Add overlays**:

   * ✅ Logo (top-left)
   * ✅ Title (bottom center, white bold text)
   * ✅ Optional part number (Part 1, Part 2, …)
5. **Render** using MoviePy (`libx264`, `aac`, `ultrafast`, `threads=1`).
6. **Save** each part to a timestamped folder.

---

## 📁 Output Structure

Each run creates a new folder named after the title and timestamp:

```
📂 solo-2-days-eating-only-what-i-catch_20251008_2111/
 ├── part_1.mp4
 ├── part_2.mp4
 ├── highlight.mp4  (if in highlight mode)
 ├── summary.json
 └── temp_audio.m4a  (auto-removed after render)
```

`summary.json` includes:

```json
{
  "title": "Solo 2 Days Eating Only What I Catch",
  "total_parts": 17,
  "clips": ["part_1.mp4", "part_2.mp4", "..."]
}
```

---

## 🪄 Debug & Logging

Every step prints out:

* 🧱 Downloading / Merging progress
* 🎨 Overlay creation
* 💾 Rendering start & completion
* ⚠️ Warnings if files or fonts missing

If the script seems “stuck”, check:

* ✅ FFmpeg is installed & on PATH
* ✅ You’re using **threads=1** (already set)
* ✅ You’re not opening output folder while saving

---

## 🛠️ Troubleshooting

| Error                                                                  | Fix                                                               |
| ---------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `WinError 2: The system cannot find the file specified`                | Install **FFmpeg** and ensure it’s in your PATH                   |
| `Logo not found`                                                       | Place `logo.png` in same folder                                   |
| `PIL text overlay failed`                                              | Ensure `arial.ttf` or fallback font exists                        |
| `AttributeError: 'NoneType' object has no attribute 'write_videofile'` | Happens if `clip` failed — check earlier logs for the root cause  |
| Stuck at 0%                                                            | ✅ Already fixed (`threads=1`, `preset=ultrafast`, visible logger) |

---

## 🧰 Extending

* 🔄 Automate TikTok uploads by connecting `tiktok_upload.py`
* 💬 Add captions from transcript using `whisper`
* 🎵 Add background music layer

---

## 💡 Tips

* Run from **PowerShell** (not VSCode terminal) for smoother progress output.
* Keep each clip < 90s for TikTok/Reels compatibility.
* Use **short titles** for overlays to avoid overflow.

---

## 🧑‍💻 Author

**Yassine Laadraoui**
🚀 Passionate about automation, AI, and content tools.

---

## 🧾 License

MIT License — use freely, modify, distribute.

```
