"""
MaiVid Studio - Scene Generator Integration

This module integrates the Suno song downloader with the fast renderer
to automatically generate scenes based on song lyrics for music videos.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
import json

from ..audio.suno_integration import download_from_suno as download_song_from_url
from ..comfyui.fast_renderer import initialize_fast_renderer, FastRenderer

# Configure logging
logger = logging.getLogger(__name__)

class MusicVideoGenerator:
    """Handles the generation of music video scenes from songs."""
    
    def __init__(self, comfyui_url: str = "http://127.0.0.1:8188"):
        """
        Initialize the music video generator.
        
        Args:
            comfyui_url: URL of the ComfyUI server
        """
        self.comfyui_url = comfyui_url
        self.renderer = None
        
        # Default settings
        self.default_model = "sdxl_turbo"
        self.default_aspect_ratio = "16:9"
        self.default_style = "cinematic"
        
        logger.info("MusicVideoGenerator initialized")
        
    def initialize(self) -> Tuple[bool, Optional[str]]:
        """
        Initialize the renderer connection.
        
        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        try:
            self.renderer = initialize_fast_renderer(self.comfyui_url)
            logger.info("Renderer initialized successfully")
            return True, None
        except Exception as e:
            error_msg = f"Failed to initialize renderer: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        
    def generate_from_suno_url(self, 
                              suno_url: str, 
                              output_dir: str = "outputs/videos",
                              model_type: str = None,
                              aspect_ratio: str = None,
                              scene_count: int = None,
                              style: str = None) -> Dict[str, Any]:
        """
        Generate a music video from a Suno URL.
        
        Args:
            suno_url: URL of the Suno song
            output_dir: Directory to save the output
            model_type: Model type for image generation
            aspect_ratio: Aspect ratio for the video
            scene_count: Number of scenes to generate
            style: Visual style for the scenes
            
        Returns:
            Dict: Result of the generation process with metadata
        """
        try:
            # Initialize renderer if needed
            if self.renderer is None:
                success, error = self.initialize()
                if not success:
                    return {"success": False, "error": error}
            
            # Set defaults for optional parameters
            model_type = model_type or self.default_model
            aspect_ratio = aspect_ratio or self.default_aspect_ratio
            style = style or self.default_style
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Step 1: Download song and extract lyrics
            logger.info(f"Downloading song from URL: {suno_url}")
            song_result = download_song_from_url(suno_url)
            
            if not song_result["success"]:
                return {"success": False, "error": song_result.get("error", "Failed to download song")}
            
            # Extract metadata
            song_title = song_result.get("title", "Unknown Song")
            artist = song_result.get("artist", "Unknown Artist")
            lyrics = song_result.get("lyrics", [])
            
            logger.info(f"Successfully downloaded song: {song_title} by {artist}")
            logger.info(f"Extracted {len(lyrics)} lyrics lines")
            
            if not lyrics:
                return {"success": False, "error": "No lyrics found in the song"}
            
            # Create a subfolder for this song
            import re
            safe_title = re.sub(r'[^\w\-_]', '_', song_title)
            song_dir = os.path.join(output_dir, safe_title)
            os.makedirs(song_dir, exist_ok=True)
            
            # Step 2: Generate scenes from lyrics
            logger.info(f"Generating scenes for song: {song_title}")
            scene_results = self.renderer.generate_video_scenes_from_lyrics(
                lyrics=lyrics,
                scene_count=scene_count,
                model_type=model_type,
                aspect_ratio=aspect_ratio,
                output_dir=song_dir,
                style=style
            )
            
            # Count successful generations
            successful_scenes = [scene for scene in scene_results if scene.get("success", False)]
            
            logger.info(f"Generated {len(successful_scenes)}/{len(scene_results)} scenes successfully")
            
            # Save the project data
            project_data = {
                "song": {
                    "title": song_title,
                    "artist": artist,
                    "url": suno_url,
                    "audio_path": song_result.get("audio_path", ""),
                    "lyrics": lyrics
                },
                "generation": {
                    "model_type": model_type,
                    "aspect_ratio": aspect_ratio,
                    "style": style,
                    "scene_count": len(scene_results)
                },
                "scenes": scene_results
            }
            
            # Save project data to JSON
            project_file = os.path.join(song_dir, "project.json")
            with open(project_file, 'w') as f:
                json.dump(project_data, f, indent=2)
            
            logger.info(f"Saved project data to {project_file}")
            
            # Create result summary
            result = {
                "success": True,
                "project_file": project_file,
                "song_title": song_title,
                "artist": artist,
                "audio_path": song_result.get("audio_path", ""),
                "scene_count": len(scene_results),
                "successful_scenes": len(successful_scenes),
                "scenes": scene_results
            }
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to generate music video: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "error": error_msg}


# Helper function to run the generation process
def generate_music_video_from_url(
    suno_url: str,
    output_dir: str = "outputs/videos",
    model_type: str = "sdxl_turbo",
    aspect_ratio: str = "16:9",
    scene_count: int = None,
    style: str = "cinematic",
    comfyui_url: str = "http://127.0.0.1:8188"
) -> Dict[str, Any]:
    """
    Generate a music video from a Suno URL.
    
    Args:
        suno_url: URL of the Suno song
        output_dir: Directory to save the output
        model_type: Model type for image generation
        aspect_ratio: Aspect ratio for the video
        scene_count: Number of scenes to generate
        style: Visual style for the scenes
        comfyui_url: URL of the ComfyUI server
        
    Returns:
        Dict: Result of the generation process with metadata
    """
    generator = MusicVideoGenerator(comfyui_url=comfyui_url)
    return generator.generate_from_suno_url(
        suno_url=suno_url,
        output_dir=output_dir,
        model_type=model_type,
        aspect_ratio=aspect_ratio,
        scene_count=scene_count,
        style=style
    )


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python music_video_generator.py <suno_url> [output_dir] [model_type] [aspect_ratio]")
        sys.exit(1)
    
    suno_url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "outputs/videos"
    model_type = sys.argv[3] if len(sys.argv) > 3 else "sdxl_turbo"
    aspect_ratio = sys.argv[4] if len(sys.argv) > 4 else "16:9"
    
    print(f"Generating music video from URL: {suno_url}")
    result = generate_music_video_from_url(
        suno_url=suno_url,
        output_dir=output_dir,
        model_type=model_type,
        aspect_ratio=aspect_ratio
    )
    
    if result["success"]:
        print(f"Successfully generated music video project:")
        print(f"  Song: {result['song_title']} by {result['artist']}")
        print(f"  Scenes: {result['successful_scenes']}/{result['scene_count']} generated")
        print(f"  Project file: {result['project_file']}")
    else:
        print(f"Failed to generate music video: {result.get('error', 'Unknown error')}")
