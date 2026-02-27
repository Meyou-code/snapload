import os
import sys
from pathlib import Path
from time import perf_counter
import subprocess
from PIL import Image
import json
from typing import Callable, Optional
from .paths import FFMPEG_PATH, FFPROBE_PATH, ZIPS_DIR
from .logging_manager import get_logger

# Logger initialization
logger = get_logger()


def fusion_image_png(image_path, png_path, output_path, on_metadata: Optional[Callable[[str], None]] = None):
    # Merge image with transparent PNG overlay
    base_image = Image.open(image_path).convert("RGBA")
    overlay = Image.open(png_path).convert("RGBA")
    
    if overlay.size != base_image.size:
        overlay = overlay.resize(base_image.size, Image.Resampling.LANCZOS)
    
    result = Image.alpha_composite(base_image, overlay)
    result = result.convert("RGB")
    result.save(output_path, "JPEG", quality=100, subsampling=0, optimize=True, progressive=True)
    
    print(f"Image merged: {os.path.basename(output_path)}")
    
    # Preserve metadata from source
    if on_metadata:
        on_metadata(output_path)
    
    return True


def fusion_video_png(video_path, png_path, output_path, ffmpeg_path, on_log=None, on_metadata: Optional[Callable[[str], None]] = None):
    # Merge transparent PNG onto video with ffmpeg
    ffprobe_path = ffmpeg_path.replace('ffmpeg.exe', 'ffprobe.exe')
    
    # Get video dimensions and rotation
    probe_tags = [
        ffprobe_path, '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream_tags=rotate:stream=width,height',
        '-of', 'json', video_path
    ]
    
    result_tags = subprocess.run(probe_tags, capture_output=True, text=True)
    metadata = json.loads(result_tags.stdout)
    
    stream = metadata['streams'][0]
    width = int(stream['width'])
    height = int(stream['height'])
    rotation = int(stream.get('tags', {}).get('rotate', 0))
    
    # Check side_data if rotation not found in tags
    if rotation == 0:
        probe_side = [
            ffprobe_path, '-v', 'error', '-select_streams', 'v:0',
            '-print_format', 'json', '-show_entries', 'stream_side_data', video_path
        ]
        result_side = subprocess.run(probe_side, capture_output=True, text=True)
        metadata_side = json.loads(result_side.stdout)
        if 'streams' in metadata_side and metadata_side['streams']:
            for side_data in metadata_side['streams'][0].get('side_data_list', []):
                if 'rotation' in side_data:
                    rotation = int(side_data['rotation'])
                    break
    
    # Calculate final dimensions based on rotation
    if abs(rotation) == 90 or abs(rotation) == 270:
        display_width, display_height = height, width
        needs_transpose = True
    else:
        display_width, display_height = width, height
        needs_transpose = False
    
    # Build filter complex
    if needs_transpose:
        if rotation == -90 or rotation == 270:
            transpose = 'transpose=1'
        elif rotation == 90 or rotation == -270:
            transpose = 'transpose=2'
        elif rotation == 180 or rotation == -180:
            transpose = 'transpose=2,transpose=2'
        else:
            transpose = 'transpose=1'
        
        filter_complex = f'[0:v]{transpose}[rotated];[1:v]scale={display_width}:{display_height}[ovr];[rotated][ovr]overlay=0:0'
    else:
        filter_complex = f'[0:v]setsar=1[vid];[1:v]scale={display_width}:{display_height}[ovr];[vid][ovr]overlay=0:0'
    
    cmd = [
        ffmpeg_path, '-noautorotate', '-i', video_path, '-i', png_path,
        '-filter_complex', filter_complex,
        '-c:a', 'copy', '-c:v', 'libx264',
        '-preset', 'veryfast', '-crf', '19',
        '-pix_fmt', 'yuv420p', '-y', output_path
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Display ffmpeg logs
    if on_log and result.stderr:
        for line in result.stderr.split('\n'):
            if line.strip():
                on_log(f"[ffmpeg] {line}")
    
    if result.returncode == 0:
        print(f"Video merged: {os.path.basename(output_path)}")
        
        # Preserve metadata from source
        if on_metadata:
            on_metadata(output_path)
        
        return True
    else:
        print(f"ffmpeg error: {result.stderr[-500:]}")
        return False


def find_overlay(directory):
    # Find overlay PNG file
    for file in os.listdir(directory):
        if file.endswith('-overlay.png'):
            return os.path.join(directory, file)
    return None


def find_main_asset(directory):
    # Find main asset file (mp4 or jpg/jpeg)
    for file in os.listdir(directory):
        if file.endswith('-main.mp4') or file.endswith('-main.jpg') or file.endswith('-main.jpeg'):
            return os.path.join(directory, file)
    return None


def process_directory(dir_path, output_base, ffmpeg_path, on_log=None, on_metadata: Optional[Callable[[str], None]] = None):
    # Process one extracted directory
    dir_name = os.path.basename(dir_path)
    overlay = find_overlay(dir_path)
    main_asset = find_main_asset(dir_path)
    
    if not overlay or not main_asset:
        print(f"Missing files in {dir_name}")
        return False
    
    ext = os.path.splitext(main_asset)[1]
    output_file = os.path.join(output_base, f"{dir_name}_fused{ext}")
    
    print(f"\n{'='*80}")
    print(f"Processing: {os.path.basename(main_asset)}")
    print(f"{'='*80}")
    
    t0 = perf_counter()
    
    if ext.lower() in ['.mp4', '.mov', '.avi']:
        success = fusion_video_png(main_asset, overlay, output_file, ffmpeg_path, on_log, on_metadata)
    elif ext.lower() in ['.jpg', '.jpeg', '.png']:
        success = fusion_image_png(main_asset, overlay, output_file, on_metadata)
    else:
        print(f"Unsupported type: {ext}")
        return False
    
    if success:
        print(f"Time: {perf_counter() - t0:.2f}s")
    
    return success


def main():
    ffmpeg_path = str(FFMPEG_PATH)
    
    if not os.path.exists(ffmpeg_path):
        logger.log(f"FUSION: FFmpeg not found at {ffmpeg_path}")
        print(f"ffmpeg not found: {ffmpeg_path}")
        sys.exit(1)
    
    logger.log(f"FUSION: FFmpeg found at {ffmpeg_path}")
    
    zips_dir = str(ZIPS_DIR)
    
    if not os.path.exists(zips_dir):
        print(f"'zips' folder not found: {zips_dir}")
        sys.exit(1)
    
    output_dir = os.path.join(zips_dir, 'fused')
    os.makedirs(output_dir, exist_ok=True)
    
    extracted_dirs = [
        os.path.join(zips_dir, d) 
        for d in os.listdir(zips_dir) 
        if os.path.isdir(os.path.join(zips_dir, d)) and d.endswith('_extracted')
    ]
    
    if not extracted_dirs:
        print("No *_extracted directory found")
        sys.exit(1)
    
    print(f"{'='*80}")
    print(f"PROCESSING - {len(extracted_dirs)} directory(ies)")
    print(f"{'='*80}")
    
    success_count = 0
    fail_count = 0
    
    for dir_path in extracted_dirs:
        if process_directory(dir_path, output_dir, ffmpeg_path):
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\n{'='*80}")
    print(f"SUMMARY: {success_count} succeeded | {fail_count} failed")
    print(f"Output: {output_dir}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()