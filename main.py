import os
import json
import subprocess
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from pytubefix import YouTube
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from slugify import slugify
from tiktok_upload import upload_to_tiktok  # optional


# ─────────────────────────────────────────────
# Load config
# ─────────────────────────────────────────────
CONFIG_PATH = "config.json"
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        CONFIG = json.load(f)
else:
    CONFIG = {"clip_duration": 60}


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def create_output_folder(title):
    safe_title = slugify(title)
    folder = os.path.join(os.getcwd(), f"{safe_title}_{datetime.now():%Y%m%d_%H%M}")
    os.makedirs(folder, exist_ok=True)
    print(f"📁 Output folder created: {folder}")
    return folder


# ─────────────────────────────────────────────
# Download highest-quality video + audio
# ─────────────────────────────────────────────
def download_video(url, custom_title=None):
    print(f"\n🔗 Fetching YouTube video: {url}")
    yt = YouTube(url)
    print(f"🎬 Found video: {yt.title}")

    title = custom_title or yt.title
    safe_title = slugify(title)
    output_path = os.path.abspath(f"{safe_title}.mp4")

    # Skip re-download if video exists
    if os.path.exists(output_path) and os.path.getsize(output_path) > 10 * 1024 * 1024:
        print(f"⚡ Found existing file: {output_path}")
        return title, output_path

    print(f"⬇️ Downloading new copy of '{yt.title}' ...")

    video_stream = (
        yt.streams.filter(adaptive=True, type="video", file_extension="mp4")
        .order_by("resolution")
        .desc()
        .first()
    )
    audio_stream = (
        yt.streams.filter(adaptive=True, type="audio", file_extension="mp4")
        .order_by("abr")
        .desc()
        .first()
    )

    if not video_stream or not audio_stream:
        raise Exception("❌ No adaptive streams found — try another video.")

    print("🎥 Downloading video stream...")
    video_path = video_stream.download(filename="video_temp.mp4")

    print("🎧 Downloading audio stream...")
    audio_path = audio_stream.download(filename="audio_temp.mp4")

    print("🛠️ Merging video + audio using ffmpeg...")
    cmd = f'ffmpeg -y -i "{video_path}" -i "{audio_path}" -c:v copy -c:a aac "{output_path}" -loglevel error'
    subprocess.run(cmd, shell=True, check=True)

    os.remove(video_path)
    os.remove(audio_path)

    print(f"✅ Download complete: {output_path}")
    return title, output_path


# ─────────────────────────────────────────────
# Save clip safely (non-blocking)
# ─────────────────────────────────────────────
def save_clip(clip, output_path):
    print(f"💾 Saving clip → {output_path}")
    try:
        clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            bitrate="8000k",
            fps=30,
            preset="ultrafast",
            threads=1,  # ⚠️ critical on Windows
            temp_audiofile=os.path.join(os.path.dirname(output_path), "temp_audio.m4a"),
            remove_temp=True,
            verbose=True,
            logger="bar",  # show progress
        )
        print(f"✅ Saved successfully: {output_path}")
    except Exception as e:
        print(f"❌ Error saving clip: {e}")


# ─────────────────────────────────────────────
# Add overlays (logo, title, part text)
# ─────────────────────────────────────────────
def add_overlays(clip, title, part_num=None, logo_path="logo.png"):
    print("🎨 Adding overlays (logo + text)...")
    layers = [clip]

    # ───── Logo ─────
    if os.path.exists(logo_path):
        try:
            print("🖼️ Adding logo overlay...")
            logo = (
                ImageClip(logo_path)
                .set_duration(clip.duration)
                .resize(height=240)  # 2x bigger
                .set_position(("left", "top"))
                .margin(left=40, top=40, opacity=0)
            )
            layers.append(logo)
        except Exception as e:
            print(f"⚠️ Logo overlay failed: {e}")
    else:
        print("⚠️ Logo not found, skipping overlay.")

    # ───── Text Overlay (via PIL) ─────
    try:
        text_content = title
        if part_num:
            text_content += f" — Part {part_num}"

        width = int(round(clip.w))
        height = 200

        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 70)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text_content, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = max(int((width - text_w) / 2), 0)
        y = max(int((height - text_h) / 2), 0)

        # translucent background bar
        rect_y = max(y - 20, 0)
        draw.rectangle(
            [(0, rect_y), (width, rect_y + text_h + 40)],
            fill=(0, 0, 0, 120)
        )

        # outline text
        outline = 2
        for dx in [-outline, 0, outline]:
            for dy in [-outline, 0, outline]:
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text_content, font=font, fill="black")

        draw.text((x, y), text_content, font=font, fill="white")

        frame = np.array(img).astype("uint8")
        if len(frame.shape) != 3 or frame.shape[2] != 4:
            raise ValueError(f"Invalid frame shape: {frame.shape}")

        txt_clip = (
            ImageClip(frame)
            .set_duration(clip.duration)
            .set_position(("center", "bottom"))
            .margin(bottom=40)
        )
        layers.append(txt_clip)
        print("✅ Text overlay added.")
    except Exception as e:
        print(f"⚠️ PIL text overlay failed: {e}")

    return CompositeVideoClip(layers)


# ─────────────────────────────────────────────
# Extract highlight only
# ─────────────────────────────────────────────
def extract_highlight(title, filepath, output_folder, logo_path="logo.png"):
    print("\n✨ Extracting highlight clip...")
    try:
        video = VideoFileClip(filepath)
        mid = video.duration / 2
        start = max(0, mid - 7.5)
        end = min(video.duration, start + 15)
        print(f"🎯 Highlight range: {start:.2f}s → {end:.2f}s")

        clip = video.subclip(start, end)
        final_clip = add_overlays(clip, title, 1, logo_path)

        highlight_path = os.path.join(output_folder, "highlight.mp4")
        save_clip(final_clip, highlight_path)

        clip.close()
        final_clip.close()
        video.close()

        print(f"✅ Highlight saved: {highlight_path}")
        return {"highlight": highlight_path}
    except Exception as e:
        print(f"❌ Failed to extract highlight: {e}")
        return None


# ─────────────────────────────────────────────
# Process full video into multiple parts
# ─────────────────────────────────────────────
def process_video(title, filepath, clip_duration, output_folder, logo_path="logo.png", parts_to_process=None):
    print("\n🎬 Loading video for splitting...")
    try:
        video = VideoFileClip(filepath)
    except Exception as e:
        print(f"❌ Failed to load video: {e}")
        return

    total_duration = int(video.duration)
    num_parts = (total_duration // clip_duration) + (1 if total_duration % clip_duration else 0)
    print(f"📼 Splitting into {num_parts} parts of {clip_duration}s each (Total duration: {total_duration}s)\n")

    summary = {"title": title, "total_parts": num_parts, "clips": []}
    parts_to_process = parts_to_process or list(range(1, num_parts + 1))

    for i in parts_to_process:
        print(f"\n▶️ Processing part {i}/{len(parts_to_process)}")
        start = (i - 1) * clip_duration
        end = min(i * clip_duration, total_duration)
        output_filename = os.path.join(output_folder, f"part_{i}.mp4")

        if os.path.exists(output_filename):
            print(f"⚠️ Part {i} already exists, skipping.")
            summary["clips"].append(output_filename)
            continue

        try:
            print(f"⏳ Extracting subclip from {start}s to {end}s ...")
            clip = video.subclip(start, end)

            final_clip = add_overlays(clip, title, i, logo_path)

            print(f"💾 Rendering part {i} ...")
            save_clip(final_clip, output_filename)

            clip.close()
            final_clip.close()
            summary["clips"].append(output_filename)

        except Exception as e:
            print(f"❌ Failed to process part {i}: {e}")

    video.close()
    with open(os.path.join(output_folder, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n✅ Done! {len(summary['clips'])} parts saved in {output_folder}")
    return summary


# ─────────────────────────────────────────────
# Main Interactive Flow
# ─────────────────────────────────────────────
def main():
    print("🎬 YouTube → TikTok Clip Maker")

    url = input("🔗 Enter YouTube URL: ").strip()
    title = input("📝 Enter custom title: ").strip()
    clip_duration = input(f"⏱️ Enter clip duration (seconds, default={CONFIG['clip_duration']}): ").strip()
    clip_duration = int(clip_duration) if clip_duration else CONFIG["clip_duration"]

    mode = input("🎯 Enter 'h' for highlight, or number of parts (press Enter for full split): ").strip()

    title, video_path = download_video(url, custom_title=title)
    output_folder = create_output_folder(title)

    if mode.lower() in ["h", "highlight"]:
        summary = extract_highlight(title, video_path, output_folder)
    else:
        parts = None
        if mode.isdigit():
            total = int(mode)
            parts = list(range(1, total + 1))
        summary = process_video(title, video_path, clip_duration, output_folder, parts_to_process=parts)

    print("\n🚀 All done! ✅")


if __name__ == "__main__":
    main()
