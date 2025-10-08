import os
import json
import subprocess
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from pytubefix import YouTube
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, vfx
from tqdm import tqdm
from slugify import slugify
from concurrent.futures import ThreadPoolExecutor, as_completed  # ✅ Windows-safe threads

# ─────────────────────────────────────────────
# Load config
# ─────────────────────────────────────────────
CONFIG_PATH = "config.json"
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        CONFIG = json.load(f)
else:
    CONFIG = {
        "clip_duration": 90,
        "font": "arial.ttf",
        "font_size": 70,
        "font_color": "white",
        "font_outline": 2,
        "bitrate": "8000k",
        "fps": 30,
        "preset": "ultrafast",
        "threads": 1,
        "logo_path": "logo.png",
        "scene_detect": False,
        "scene_threshold": 0.3,
        "parallel_renders": 2,
        "vertical_format": True,  # ✅ New: Auto 9:16 conversion
        "vertical_resolution": 1080
    }

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def create_output_folder(title):
    safe_title = slugify(title)
    folder = os.path.join(os.getcwd(), f"{safe_title}_{datetime.now():%Y%m%d_%H%M}")
    os.makedirs(folder, exist_ok=True)
    print(f"📁 Output folder: {folder}")
    return folder


def run_ffmpeg_scene_detect(filepath, threshold=0.3):
    print(f"🔍 Detecting scene changes (threshold={threshold})...")
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "info",
        "-i", filepath,
        "-filter_complex", f"select='gt(scene,{threshold})',showinfo",
        "-f", "null", "-"
    ]
    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    timestamps = []
    for line in process.stderr:
        if "pts_time:" in line:
            try:
                ts = float(line.split("pts_time:")[1].split(" ")[0])
                timestamps.append(ts)
            except:
                continue
    process.wait()
    print(f"🎬 Detected {len(timestamps)} scene changes.")
    return timestamps


def build_scene_segments(duration, scenes, target_length):
    if not scenes:
        print("⚙️ No scene data found — falling back to fixed splitting.")
        return [(i, min(i + target_length, duration)) for i in range(0, int(duration), target_length)]

    segments = []
    start = 0
    for ts in scenes:
        if ts - start >= target_length:
            segments.append((start, ts))
            start = ts
    if start < duration:
        segments.append((start, duration))
    print(f"🎞️ Generated {len(segments)} scene-based segments.")
    return segments


# ─────────────────────────────────────────────
# Download video
# ─────────────────────────────────────────────
def download_video(url, custom_title=None):
    yt = YouTube(url)
    print(f"🎬 Checking: {yt.title}")

    title = custom_title or yt.title
    safe_title = slugify(title)
    output_path = os.path.abspath(f"{safe_title}.mp4")

    if os.path.exists(output_path) and os.path.getsize(output_path) > 10 * 1024 * 1024:
        print(f"⚡ Found existing video: {output_path}")
        return title, output_path

    print(f"⬇️ Downloading new copy of: {yt.title}")

    video_stream = (
        yt.streams.filter(adaptive=True, type="video", file_extension="mp4")
        .order_by("resolution").desc().first()
    )
    audio_stream = (
        yt.streams.filter(adaptive=True, type="audio", file_extension="mp4")
        .order_by("abr").desc().first()
    )

    if not video_stream or not audio_stream:
        raise Exception("No adaptive streams found — try another video.")

    video_path = video_stream.download(filename="video_temp.mp4")
    audio_path = audio_stream.download(filename="audio_temp.mp4")

    cmd = f'ffmpeg -y -i "{video_path}" -i "{audio_path}" -c:v copy -c:a aac "{output_path}" -loglevel error'
    subprocess.run(cmd, shell=True, check=True)

    os.remove(video_path)
    os.remove(audio_path)

    print(f"✅ Download complete: {output_path}")
    return title, output_path


# ─────────────────────────────────────────────
# Add overlays + vertical format
# ─────────────────────────────────────────────
def add_overlays(clip, title, part_num=None):
    layers = []

    # ✅ Auto vertical conversion
    if CONFIG.get("vertical_format", True):
        target_h = CONFIG.get("vertical_resolution", 1080)
        target_w = int(target_h * 9 / 16)
        clip = clip.resize(height=target_h)
        clip = clip.fx(vfx.crop, width=target_w, height=target_h, x_center=clip.w/2, y_center=clip.h/2)

    layers.append(clip)

    logo_path = CONFIG.get("logo_path", "logo.png")
    font_path = CONFIG.get("font", "arial.ttf")
    font_size = CONFIG.get("font_size", 70)
    font_color = CONFIG.get("font_color", "white")
    outline = CONFIG.get("font_outline", 2)

    # Logo
    if os.path.exists(logo_path):
        try:
            logo_height = CONFIG.get("logo_height", 240)  # use config, default 240
            logo = (
                ImageClip(logo_path)
                .set_duration(clip.duration)
                .resize(height=logo_height)
                .set_position(("left", "top"))
                .margin(left=20, top=20, opacity=0)
            )
            layers.append(logo)
        except Exception as e:
            print(f"⚠️ Logo overlay failed: {e}")

    try:
        text_content = title if not part_num else f"{title} — Part {part_num}"

        width = int(round(clip.w))
        height = 200
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text_content, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = max(int((width - text_w) / 2), 0)
        y = max(int((height - text_h) / 2), 0)

        for dx in [-outline, 0, outline]:
            for dy in [-outline, 0, outline]:
                if dx != 0 or dy != 0:
                    draw.text((x+dx, y+dy), text_content, font=font, fill="black")
        draw.text((x, y), text_content, font=font, fill=font_color)

        frame = np.array(img).astype("uint8")
        txt_clip = (
            ImageClip(frame)
            .set_duration(clip.duration)
            .set_position(("center", "bottom"))
            .margin(bottom=40)
        )
        layers.append(txt_clip)
    except Exception as e:
        print(f"⚠️ Text overlay failed: {e}")

    return CompositeVideoClip(layers)


# ─────────────────────────────────────────────
# Save clip
# ─────────────────────────────────────────────
def save_clip(args):
    output_path, start, end, filepath, title, part_num = args
    print(f"🚀 Starting part {part_num}: {start:.1f}s → {end:.1f}s")
    try:
        with VideoFileClip(filepath).subclip(start, end) as clip:
            final_clip = add_overlays(clip, title, part_num)
            final_clip.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                bitrate=CONFIG["bitrate"],
                fps=CONFIG["fps"],
                preset=CONFIG["preset"],
                threads=CONFIG["threads"],
                logger="bar"
            )
            final_clip.close()
        print(f"✅ Finished part {part_num}: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Failed part {part_num}: {e}")
        return None


# ─────────────────────────────────────────────
# Process video
# ─────────────────────────────────────────────
def process_video(title, filepath, output_folder):
    with VideoFileClip(filepath) as video:
        total_duration = int(video.duration)

    if CONFIG.get("scene_detect", False):
        scenes = run_ffmpeg_scene_detect(filepath, CONFIG["scene_threshold"])
        segments = build_scene_segments(total_duration, scenes, CONFIG["clip_duration"])
    else:
        segments = [(i, min(i + CONFIG["clip_duration"], total_duration))
                    for i in range(0, total_duration, CONFIG["clip_duration"])]

    print(f"📼 Preparing {len(segments)} parts...")

    tasks = []
    for idx, (start, end) in enumerate(segments, 1):
        output_filename = os.path.join(output_folder, f"part_{idx}.mp4")
        if os.path.exists(output_filename):
            print(f"⚠️ Skipping part {idx} (exists)")
            continue
        tasks.append((output_filename, start, end, filepath, title, idx))

    summary = {"title": title, "clips": []}

    with ThreadPoolExecutor(max_workers=CONFIG["parallel_renders"]) as executor:
        futures = [executor.submit(save_clip, t) for t in tasks]
        for f in tqdm(as_completed(futures), total=len(futures), desc="Rendering"):
            result = f.result()
            if result:
                summary["clips"].append(result)

    with open(os.path.join(output_folder, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n✅ Done! {len(summary['clips'])} parts saved in {output_folder}")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    print("🎬 YouTube → TikTok Clip Maker")
    url = input("🔗 Enter YouTube URL: ").strip()
    title = input("📝 Enter custom title: ").strip()

    title, video_path = download_video(url, custom_title=title)
    output_folder = create_output_folder(title)

    process_video(title, video_path, output_folder)
    print("\n🚀 All done!")


if __name__ == "__main__":
    main()
