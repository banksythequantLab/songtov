"""
MaiVid Studio - Scene Generator Module

This module handles the generation of scene images based on lyrics or scene descriptions.
It integrates with ComfyUI to generate high-quality images for music videos.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Import the ComfyUI interface
from .comfyui.interface import ComfyUIInterface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SceneGenerator:
    """Scene generation manager for music videos."""
    
    def __init__(self, workflow_dir: str = None, output_dir: str = None, use_ai_director: bool = True):
        """Initialize the scene generator."""
        # Use absolute paths for better reliability
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Set default directories if not provided
        self.workflow_dir = workflow_dir if workflow_dir else os.path.join(base_dir, "workflows")
        self.output_dir = output_dir if output_dir else os.path.join(base_dir, "outputs", "scenes")
        
        self.comfyui = ComfyUIInterface()
        
        # Ensure directories exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load the default workflow file path
        self.default_workflow = os.path.join(self.workflow_dir, "scene_generation.json")
        
        # Initialize AI Director if enabled
        self.use_ai_director = use_ai_director
        self.ai_director = None
        
        if self.use_ai_director:
            try:
                from .ai.integration import DirectorIntegration
                self.ai_director = DirectorIntegration()
                logger.info("AI Director initialized for enhanced scene generation")
            except ImportError:
                logger.warning("AI Director module not found, using basic scene generation")
                self.use_ai_director = False
        
        logger.info(f"Initialized SceneGenerator with workflow directory: {self.workflow_dir}")
        logger.info(f"Scene outputs will be saved to: {self.output_dir}")
        logger.info(f"Default workflow: {self.default_workflow}")
        logger.info(f"AI Director enabled: {self.use_ai_director}")

    def validate_workflow(self) -> bool:
        """Check if the workflow file exists and is valid."""
        if not os.path.exists(self.default_workflow):
            logger.error(f"Workflow file not found: {self.default_workflow}")
            return False
            
        try:
            with open(self.default_workflow, 'r') as f:
                workflow = json.load(f)
                
            # Basic validation check - make sure it has nodes
            if not workflow or "nodes" not in workflow or not workflow["nodes"]:
                logger.error(f"Invalid workflow file: {self.default_workflow}")
                return False
                
            logger.info(f"Workflow file validated: {self.default_workflow}")
            return True
        except Exception as e:
            logger.error(f"Error validating workflow file: {e}")
            return False

    def generate_scene_image(self, scene: Dict[str, Any], style: str = "cinematic") -> Tuple[Optional[str], Optional[str]]:
        """
        Generate an image for a scene.
        
        Args:
            scene (Dict): Scene data with prompt information
            style (str): Visual style to apply
            
        Returns:
            Tuple: (path_to_generated_image, error_message)
        """
        # First check if ComfyUI is available
        comfyui_available, comfyui_error = self.comfyui.check_connection()
        if not comfyui_available:
            return None, f"ComfyUI is not available: {comfyui_error}"
        
        # Then check if the workflow file exists
        if not self.validate_workflow():
            return None, f"Invalid workflow file: {self.default_workflow}"
            
        try:
            # Get the scene prompt
            scene_prompt = scene.get("scene_prompt", "")
            if not scene_prompt:
                # Fallback to text or generate a default prompt
                scene_text = scene.get("text", "A cinematic scene")
                scene_prompt = f"music video scene with {scene_text}, {style} style"
            
            logger.info(f"Generating scene image with prompt: {scene_prompt}")
            
            # Generate the image
            image_path, error = self.comfyui.generate_scene(
                workflow_file=self.default_workflow,
                scene_description=scene_prompt,
                style=style,
                output_dir=self.output_dir
            )
            
            if error:
                logger.error(f"Failed to generate scene image: {error}")
                return None, error
                
            logger.info(f"Generated scene image: {image_path}")
            return image_path, None
            
        except Exception as e:
            error_msg = f"Failed to generate scene image: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            return None, error_msg

    def generate_scenes_for_song(self, scenes: List[Dict[str, Any]], style: str = "cinematic") -> Dict[int, str]:
        """
        Generate images for all scenes in a song.
        
        Args:
            scenes (List): List of scene data
            style (str): Visual style to apply
            
        Returns:
            Dict: Mapping of scene indices to image paths
        """
        scene_images = {}
        
        for i, scene in enumerate(scenes):
            logger.info(f"Generating image for scene {i+1}/{len(scenes)}")
            
            # Generate image for this scene
            image_path, error = self.generate_scene_image(scene, style)
            
            if image_path:
                scene_images[i] = image_path
                logger.info(f"Scene {i+1} image saved to {image_path}")
            else:
                logger.error(f"Failed to generate image for scene {i+1}: {error}")
                
        return scene_images

    def process_song_metadata(self, metadata: Dict[str, Any], style: str = "cinematic") -> Dict[str, Any]:
        """
        Process song metadata to generate scene images.
        
        Args:
            metadata (Dict): Song metadata including scenes
            style (str): Visual style to apply
            
        Returns:
            Dict: Updated metadata with scene image paths
        """
        updated_metadata = metadata.copy()
        
        # Check if we have scenes to process
        if "scenes" not in updated_metadata or not updated_metadata["scenes"]:
            logger.warning("No scenes found in metadata, skipping image generation")
            return updated_metadata
        
        # Extract scenes
        scenes = updated_metadata["scenes"]
        
        # Use AI Director to enhance scenes if available
        if self.use_ai_director and self.ai_director:
            # Check if lyrics are available in metadata
            lyrics = updated_metadata.get("lyrics", "")
            if lyrics:
                # Enhance existing scenes with AI Director
                enhanced_scenes = self.ai_director.enhance_scenes_from_lyrics(lyrics, scenes)
                scenes = enhanced_scenes
                # Update scenes in metadata
                updated_metadata["scenes"] = scenes
                
                # Add story information to metadata
                story = self.ai_director.get_story_elements(lyrics)
                updated_metadata["story"] = story
                logger.info(f"Enhanced {len(scenes)} scenes with AI Director")
        
        logger.info(f"Processing {len(scenes)} scenes for image generation")
        
        # Generate images for all scenes
        scene_images = self.generate_scenes_for_song(scenes, style)
        
        # Update scenes with image paths
        for i, image_path in scene_images.items():
            if i < len(scenes):
                scenes[i]["image_path"] = image_path
                
        updated_metadata["scenes"] = scenes
        return updated_metadata


# Example usage
if __name__ == "__main__":
    # Initialize the scene generator
    generator = SceneGenerator()
    
    # Example scene
    example_scene = {
        "text": "A beautiful sunset over a calm ocean with sailboats on the horizon",
        "scene_prompt": "atmospheric music video scene with beautiful sunset, calm ocean, and sailboats on the horizon",
        "timestamp": 0
    }
    
    # Generate an image for the example scene
    image_path, error = generator.generate_scene_image(example_scene)
    
    if image_path:
        print(f"Generated scene image: {image_path}")
    else:
        print(f"Failed to generate scene image: {error}")
