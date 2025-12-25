# Copyright (c) 2025 Stephen G. Pope
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.



import os
import subprocess
import logging
from services.file_management import download_file
from PIL import Image
from config import LOCAL_STORAGE_PATH
logger = logging.getLogger(__name__)

# Supported aspect ratios and their corresponding dimensions
ASPECT_RATIOS = {
    "original": None,  # Will preserve original aspect ratio
    "1:1": (1, 1),
    "4:3": (4, 3),
    "3:2": (3, 2),
    "16:9": (16, 9),
    "9:16": (9, 16),
    "21:9": (21, 9),
    "2.35:1": (2.35, 1)
}

# Supported resolutions
RESOLUTIONS = {
    "original": None,  # Will use original image resolution
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "1440p": (2560, 1440),
    "4k": (3840, 2160),
    "square": (1080, 1080)
}

def calculate_dimensions(original_width, original_height, aspect_ratio, resolution, fit_mode="cover"):
    """
    Calculate output dimensions based on aspect ratio, resolution, and fit mode.
    
    Args:
        original_width, original_height: Original image dimensions
        aspect_ratio: Target aspect ratio (e.g., "16:9", "1:1")
        resolution: Target resolution (e.g., "1080p", "4k")
        fit_mode: How to fit image ("cover", "contain", "fill")
    
    Returns:
        tuple: (target_width, target_height)
    """
    # Get target resolution or use original
    if resolution and resolution in RESOLUTIONS and RESOLUTIONS[resolution]:
        target_width, target_height = RESOLUTIONS[resolution]
    else:
        # Use original resolution as base
        target_width, target_height = original_width, original_height
    
    # Handle original aspect ratio
    if aspect_ratio == "original":
        # Preserve original aspect ratio but scale to target resolution
        original_ratio = original_width / original_height
        target_ratio = target_width / target_height
        
        if fit_mode == "cover":
            # Scale to fill target dimensions, may crop
            if original_ratio > target_ratio:
                # Image is wider, scale by height
                target_height = target_height
                target_width = int(target_height * original_ratio)
            else:
                # Image is taller, scale by width
                target_width = target_width
                target_height = int(target_width / original_ratio)
        elif fit_mode == "contain":
            # Scale to fit within target dimensions, may have padding
            if original_ratio > target_ratio:
                # Image is wider, scale by width
                target_width = target_width
                target_height = int(target_width / original_ratio)
            else:
                # Image is taller, scale by height
                target_height = target_height
                target_width = int(target_height * original_ratio)
        else:  # fill
            # Force to target dimensions (may stretch)
            pass
            
    else:
        # Use specified aspect ratio
        if aspect_ratio in ASPECT_RATIOS and ASPECT_RATIOS[aspect_ratio]:
            ratio_width, ratio_height = ASPECT_RATIOS[aspect_ratio]
            target_ratio = ratio_width / ratio_height
            
            if fit_mode == "cover":
                # Scale to fill target dimensions, may crop
                if target_width / target_height > target_ratio:
                    # Target is wider, scale by height
                    target_width = int(target_height * target_ratio)
                else:
                    # Target is taller, scale by width
                    target_height = int(target_width / target_ratio)
            elif fit_mode == "contain":
                # Scale to fit within target dimensions, may have padding
                if target_width / target_height > target_ratio:
                    # Target is wider, scale by width
                    target_height = int(target_width / target_ratio)
                else:
                    # Target is taller, scale by height
                    target_width = int(target_height * target_ratio)
            else:  # fill
                # Force to target dimensions
                pass
    
    return target_width, target_height

def process_image_to_video(image_url, length, frame_rate, zoom_speed, job_id, webhook_url=None, aspect_ratio="original", resolution="1080p", fit_mode="cover"):
    try:
        # Download the image file
        image_path = download_file(image_url, LOCAL_STORAGE_PATH)
        logger.info(f"Downloaded image to {image_path}")

        # Get image dimensions using Pillow
        with Image.open(image_path) as img:
            width, height = img.size
        logger.info(f"Original image dimensions: {width}x{height}")

        # Prepare the output path
        output_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.mp4")

        # Calculate output dimensions based on user preferences
        output_width, output_height = calculate_dimensions(width, height, aspect_ratio, resolution, fit_mode)
        
        # Set scale dimensions for high-quality upscaling
        scale_factor = 4  # Upscale for better quality before downscaling
        scale_width = max(output_width * scale_factor, width)
        scale_height = max(output_height * scale_factor, height)
        scale_dims = f"{scale_width}:{scale_height}"
        output_dims = f"{output_width}x{output_height}"

        # Calculate total frames and zoom factor
        total_frames = int(length * frame_rate)
        zoom_factor = 1 + (zoom_speed * length)

        logger.info(f"Using aspect ratio: {aspect_ratio}, resolution: {resolution}, fit mode: {fit_mode}")
        logger.info(f"Scale dimensions: {scale_dims}, output dimensions: {output_dims}")
        logger.info(f"Original: {width}x{height} → Output: {output_width}x{output_height}")
        logger.info(f"Video length: {length}s, Frame rate: {frame_rate}fps, Total frames: {total_frames}")
        logger.info(f"Zoom speed: {zoom_speed}/s, Final zoom factor: {zoom_factor}")

        # Prepare FFmpeg command with fps filter to ensure correct frame rate
        cmd = [
            'ffmpeg', '-framerate', str(frame_rate), '-loop', '1', '-i', image_path,
            '-vf', f"scale={scale_dims},zoompan=z='min(1+({zoom_speed}*{length})*on/{total_frames}, {zoom_factor})':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={output_dims},fps={frame_rate}",
            '-c:v', 'libx264', '-r', str(frame_rate), '-t', str(length), '-pix_fmt', 'yuv420p', output_path
        ]

        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")

        # Run FFmpeg command
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg command failed. Error: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)

        logger.info(f"Video created successfully: {output_path}")

        # Clean up input file
        os.remove(image_path)

        return output_path
    except Exception as e:
        logger.error(f"Error in process_image_to_video: {str(e)}", exc_info=True)
        raise