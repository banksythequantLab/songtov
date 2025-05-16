# MaiVid Studio Fast Renderer

This module provides optimized image generation for music videos using ComfyUI's fast models such as SDXL Turbo, SD3, and Flux.

## Overview

The Fast Renderer is designed to quickly generate multiple scene images for music videos, prioritizing speed over maximum quality for rapid prototyping and initial video assembly. It integrates with MaiVid Studio's Suno downloader to create an end-to-end solution for generating music videos from Suno links.

## Features

- **Fast Image Generation**: Optimized ComfyUI workflows for sub-second image generation
- **Multiple Model Support**: 
  - `sdxl_turbo`: Fastest generation, good for initial prototyping
  - `sd3`: Higher quality with reasonable speed
  - `flux`: Alternative model with different visual characteristics
- **Batch Scene Generation**: Generate all scenes for a music video in a single operation
- **Automatic Scene Planning**: Intelligently determines scene count based on lyrics
- **Seamless Integration**: Works with the Suno downloader to create end-to-end workflow
- **Customizable Aspect Ratios**: Supports 16:9, 1:1, 9:16, 21:9, and 4:3 formats
- **Style Controls**: Apply different visual styles to scenes
- **Project State Persistence**: Saves all generation data in JSON format for later access

## Workflow Files

- `sdxl_turbo.json`: Optimized workflow for SDXL Turbo (<1 second generation)
- `sd3_fast.json`: Configured SD3 workflow with reduced steps for speed

## Command-Line Interface

A command-line tool is provided for easy generation:

```bash
python generate_music_video.py https://suno.com/song/your-song-id --model sdxl_turbo --aspect 16:9 --style cyberpunk
```

Options:
- `--output-dir`: Directory to save output (default: outputs/videos)
- `--model`: Model to use (sdxl_turbo, sd3, flux)
- `--aspect`: Aspect ratio (16:9, 1:1, 9:16, 21:9, 4:3)
- `--scenes`: Number of scenes to generate (default: auto-determined)
- `--style`: Visual style (cinematic, anime, realistic, etc.)
- `--comfyui`: ComfyUI server URL (default: http://127.0.0.1:8188)

## Requirements

- ComfyUI running and accessible
- Appropriate models installed in ComfyUI:
  - `sd_xl_turbo_1.0_fp16.safetensors`
  - `sd3.5_large_fp8_scaled.safetensors`
  - `Flux.safetensors` (optional)
- Python libraries:
  - requests
  - json
  - logging
  - uuid
  - bs4 (for Suno download)
  - whisper (for lyrics extraction)

## Integration with MaiVid Studio

The Fast Renderer is integrated into MaiVid Studio's backend and can be accessed through:

1. The command-line tool for direct generation
2. The web interface through the music video generation workflow
3. Programmatically through the Python API:

```python
from src.backend.generation.music_video_generator import generate_music_video_from_url

result = generate_music_video_from_url(
    suno_url="https://suno.com/song/your-song-id",
    model_type="sdxl_turbo",
    aspect_ratio="16:9",
    style="cinematic"
)

if result["success"]:
    print(f"Generated {result['successful_scenes']} scenes")
    print(f"Project saved to {result['project_file']}")
```
