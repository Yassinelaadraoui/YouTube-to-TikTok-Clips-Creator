import os
import json
import argparse
from datetime import datetime

from pytubefix import YouTube
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from tqdm import tqdm
from PIL import Image
from slugify import slugify  # safe filenames
from tiktok_upload import upload_to_tiktok  # optional

# Load config
with open("config.json", "r") as f:
    CONFIG = json.load(f)

def create_output_folder(title):
    safe_title = slugify(title)
    folder = os.path.join(os.getcwd(), f"{safe_title}_{datetime.now():%Y%m%d_%H%M}")
    os.makedirs(folder, exist_ok=True)
    print(f"📁 Output folder: {folder}")
    return folder

def download_video(url, resolution="720p"):
    yt = YouTube(url)
    print(f"🎬 Downloading: {yt.title}")

    stream = yt.streams.filter(progressive=True, file_extension='mp4', res=resolution).first()
    if not stream:
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

    out_file = os.path.abspath(stream.download())
    print(f"✅ Download complete: {out_file}")
    return yt.title, out_file

def process_video(title, filepath, clip_duration, output_folder, logo_path="logo.png", selected_parts=None):
    """Split video into clips, resize to vertical, add watermark, save thumbnails"""
    try:
        video = VideoFileClip(filepath)
    except Exception as e:
        print(f"❌ Failed to load video: {e}")
        return

    total_duration = int(video.duration)
    num_parts = (total_duration // clip_duration) + (1 if total_duration % clip_duration else 0)
    summary = {"title": title, "total_parts": num_parts, "duration": total_duration, "clips": []}

    print(f"📼 Splitting into {num_parts} parts of {clip_duration}s each...\n")

    # Determine which parts to process
    if selected_parts:
        parts_to_process = [p for p in selected_parts if 1 <= p <= num_parts]
    else:
        parts_to_process = range(1, num_parts + 1)

    for i in tqdm(parts_to_process, desc="Processing parts"):
        start = (i - 1) * clip_duration
        end = min(i * clip_duration, total_duration)
        output_filename = os.path.join(output_folder, f"part_{i}.mp4")

        # Check if file already exists (without Windows prefix for checking)
        if os.path.exists(output_filename):
            print(f"⚠️ Skipping {output_filename} (already exists)")
            summary["clips"].append(output_filename)
            continue

        try:
            # Create subclip from the original video
            clip = video.subclip(start, end)

            # Resize to vertical safely
            try:
                # Get original dimensions
                orig_w, orig_h = clip.size
                target_h = 1920
                target_w = 1080
                
                # Calculate scaling to fill the target height
                scale_factor = target_h / orig_h
                new_w = int(orig_w * scale_factor)
                
                # Resize and crop to vertical format
                clip = clip.resize(height=target_h)
                if new_w > target_w:
                    clip = clip.crop(x_center=clip.w / 2, width=target_w)
                else:
                    # If video is already narrow, just resize
                    clip = clip.resize((target_w, target_h))
                    
            except Exception as e:
                print(f"⚠️ Resize/crop failed for part {i}, using original resolution: {e}")

            # Add watermark/logo if exists
            if os.path.exists(logo_path):
                try:
                    logo = (ImageClip(logo_path)
                            .set_duration(clip.duration)
                            .resize(height=120)
                            .set_position(("right", "bottom"))
                            .margin(right=10, bottom=10, opacity=0))
                    clip = CompositeVideoClip([clip, logo])
                except Exception as e:
                    print(f"⚠️ Logo overlay failed for part {i}: {e}")

            print(f"💾 Saving part {i} to {output_filename}")
            
            # Write video file with error handling
            try:
                clip.write_videofile(
                    output_filename,
                    codec="libx264",
                    audio_codec="aac",
                    bitrate="2000k",
                    fps=30,
                    preset='medium',
                    threads=4,
                    verbose=False,
                    logger='bar'
                )
                
                # Verify file was created
                if not os.path.exists(output_filename):
                    raise Exception(f"File was not created: {output_filename}")
                
                file_size = os.path.getsize(output_filename)
                if file_size == 0:
                    raise Exception(f"File is empty: {output_filename}")
                    
                print(f"✅ Part {i} saved successfully ({file_size / (1024*1024):.2f} MB)")
                
            except Exception as e:
                print(f"❌ Failed to write video file for part {i}: {e}")
                clip.close()
                continue

            # Save thumbnail
            try:
                frame = clip.get_frame(1)
                thumb_path = os.path.join(output_folder, f"thumb_part_{i}.png")
                Image.fromarray(frame).save(thumb_path)
                print(f"🖼️ Thumbnail saved: {thumb_path}")
            except Exception as e:
                print(f"⚠️ Thumbnail generation failed for part {i}: {e}")

            summary["clips"].append(output_filename)
            clip.close()

        except Exception as e:
            print(f"❌ Failed to process part {i}: {e}")
            import traceback
            traceback.print_exc()
            continue

    video.close()

    # Save summary JSON
    summary_path = os.path.join(output_folder, "summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n✅ Done! {len(summary['clips'])} parts saved in {output_folder}")
    print(f"🧾 Summary file: {summary_path}")
    return summary

def main():
    parser = argparse.ArgumentParser(description="YouTube → TikTok Clips Creator")
    parser.add_argument("--url", required=True, help="YouTube video URL")
    parser.add_argument("--clip-duration", type=int, default=CONFIG["clip_duration"], help="Clip length in seconds")
    parser.add_argument("--upload-tiktok", action="store_true", help="Upload clips to TikTok after rendering")
    parser.add_argument("--parts", type=int, nargs="+", help="List of part numbers to process (e.g., 1 2 3)")
    args = parser.parse_args()

    title, video_path = download_video(args.url)
    output_folder = create_output_folder(title)

    summary = process_video(title, video_path, args.clip_duration, output_folder, selected_parts=args.parts)

    if args.upload_tiktok and summary:
        for clip_file in summary["clips"]:
            if os.path.exists(clip_file):
                print(f"🚀 Uploading {clip_file} to TikTok...")
                try:
                    upload_to_tiktok(clip_file)
                except Exception as e:
                    print(f"⚠️ TikTok upload failed for {clip_file}: {e}")
            else:
                print(f"⚠️ Skipping upload, file not found: {clip_file}")
        print("✅ All clips uploaded!")

if __name__ == "__main__":
    main()