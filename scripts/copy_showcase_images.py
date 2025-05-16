#!/usr/bin/env python
"""
Script to copy selected ComfyUI output images to the MaiVid Studio static directory for showcase use
"""

import os
import shutil
import random
import glob
from pathlib import Path

def main():
    """Copy a selection of ComfyUI generated images to the MaiVid Studio static showcase directory"""
    
    # Directory paths
    comfyui_output_dir = Path("K:/ComfyUI/output")
    maivid_static_img_dir = Path("K:/MaiVid_Studio/src/frontend/static/img")
    
    # Create the destination directory if it doesn't exist
    showcase_dir = maivid_static_img_dir / "showcase"
    showcase_dir.mkdir(exist_ok=True, parents=True)
    
    # Find PNG and WEBP files in the ComfyUI output directory
    image_files = []
    for ext in ['*.png', '*.webp']:
        image_files.extend(glob.glob(str(comfyui_output_dir / ext)))
    
    # Filter for certain patterns if needed
    # This example filters to get only ComfyUI_ prefixed files
    comfyui_images = [f for f in image_files if os.path.basename(f).startswith('ComfyUI_')]
    
    # Select 5 random images
    if len(comfyui_images) >= 5:
        selected_images = random.sample(comfyui_images, 5)
    else:
        selected_images = comfyui_images  # Use all if fewer than 5
    
    # Copy the selected images to the showcase directory
    for i, src_path in enumerate(selected_images, 1):
        # Generate destination path with showcase format
        dest_filename = f"showcase{i}.{src_path.split('.')[-1]}"
        dest_path = showcase_dir / dest_filename
        
        # Copy the file
        shutil.copy2(src_path, dest_path)
        print(f"Copied {src_path} to {dest_path}")
    
    print(f"Successfully copied {len(selected_images)} showcase images")

if __name__ == "__main__":
    main()