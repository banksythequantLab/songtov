"""
MaiVid Studio - Suno Downloader Integration

This module integrates the enhanced Suno downloader with the MaiVid Studio audio processor.
It also handles scene generation for downloaded songs.
"""

import os
import logging
from typing import Dict, Optional, Tuple, Any

# Import the suno_downloader module
from .downloaders.suno_downloader import download_suno_song

# Import scene generator (relative import from parent directory)
try:
    from ..scene_generator import SceneGenerator
    SCENE_GENERATOR_AVAILABLE = True
except ImportError:
    SCENE_GENERATOR_AVAILABLE = False
    
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def download_from_suno(url: str, output_dir: str = "uploads") -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
    """
    Download a song from Suno using the enhanced downloader.
    
    Args:
        url (str): Suno song URL
        output_dir (str): Directory to save the MP3 file
        
    Returns:
        Tuple containing:
            - Path to downloaded file (or None if failed)
            - Error message (or None if successful)
            - Metadata dictionary
    """
    try:
        logger.info(f"Downloading song from Suno URL: {url}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Download the song
        song_data = download_suno_song(
            url=url,
            output_dir=output_dir,
            project_dir=output_dir,
            verbose=True,
            cookie_file=None,  # Add support for cookies later if needed
            use_whisper=True
        )
        
        if not song_data:
            error_msg = "Failed to download song from Suno"
            logger.error(error_msg)
            return None, error_msg, {}
        
        # Extract the important metadata
        metadata = {
            "id": song_data.get("id", ""),
            "platform": "suno",
            "title": song_data.get("title", "Unknown Suno Track"),
            "artist": song_data.get("artist", "Suno AI"),
            "genre": song_data.get("metadata", {}).get("styles", ["Unknown"])[0] if song_data.get("metadata", {}).get("styles") else "Unknown",
            "url": url,
            "lyrics": song_data.get("lyrics", ""),
            "duration": song_data.get("duration", ""),
            "description": song_data.get("description", ""),
            "source_url": song_data.get("source_url", url),
            "download_date": song_data.get("download_date", ""),
            "scenes": []  # This will be populated by the Scene Generator later
        }
        
        # Generate scene information if lyrics are available
        if song_data.get("lyrics"):
            from .downloaders.suno_downloader import generate_scenes_from_lyrics
            metadata["scenes"] = generate_scenes_from_lyrics(song_data["lyrics"])
            
            # Generate scene images if the scene generator is available
            if SCENE_GENERATOR_AVAILABLE:
                try:
                    logger.info("Generating scene images with SceneGenerator")
                    scene_generator = SceneGenerator()
                    
                    # Generate scene images and update metadata
                    updated_metadata = scene_generator.process_song_metadata(metadata)
                    
                    # Update the metadata with the scene images
                    metadata = updated_metadata
                    
                    logger.info(f"Successfully generated {len([s for s in metadata['scenes'] if 'image_path' in s])} scene images")
                except Exception as e:
                    logger.error(f"Error generating scene images: {e}")
                    # Continue without scene images if there's an error
        
        logger.info(f"Successfully downloaded song: {metadata['title']}")
        
        return song_data.get("mp3_path"), None, metadata
        
    except Exception as e:
        error_msg = f"Error downloading from Suno: {str(e)}"
        logger.error(error_msg)
        import traceback
        logger.error(traceback.format_exc())
        return None, error_msg, {}