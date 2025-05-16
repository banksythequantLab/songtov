"""
MaiVid Studio - AI Director Integration

This module integrates the AIDirector with the existing scene generation system,
allowing the creation of more cohesive storytelling in music videos.

It also supports using local models via Ollama as alternatives to the built-in Director.
"""

import os
import logging
import json
from typing import List, Dict, Any, Optional, Tuple

# Import the AIDirector
from ..ai.director import AIDirector

# Import local models support
try:
    from ..ai.local_models import OllamaConnector
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DirectorIntegration:
    """
    Integrates the AI Director with the existing scene generation workflow.
    
    This class serves as a bridge between the existing scene generation system
    and the new AI Director, allowing for seamless enhancement of music video
    scenes with better storytelling and coherent narrative elements.
    
    It also supports using local Ollama models like Phi-3 as alternatives to
    the built-in AI Director.
    """
    
    def __init__(self, use_ollama: bool = False, ollama_model: str = "phi3:mini"):
        """
        Initialize the director integration.
        
        Args:
            use_ollama: Whether to use Ollama for generation
            ollama_model: Name of the Ollama model to use (default: phi3:mini)
        """
        self.use_ollama = use_ollama and OLLAMA_AVAILABLE
        self.ollama_model = ollama_model
        self.ollama = None
        
        # Initialize the appropriate director
        if self.use_ollama:
            try:
                self.ollama = OllamaConnector(model_name=ollama_model)
                available, error = self.ollama.check_availability()
                if not available:
                    logger.warning(f"Ollama not available: {error}. Falling back to built-in AI Director.")
                    self.use_ollama = False
                    self.director = AIDirector()
                else:
                    logger.info(f"Using Ollama with model {ollama_model}")
            except Exception as e:
                logger.warning(f"Error initializing Ollama: {e}. Falling back to built-in AI Director.")
                self.use_ollama = False
                self.director = AIDirector()
        else:
            self.director = AIDirector()
            logger.info("AI Director integration initialized (using built-in director)")
    
    def enhance_scenes_from_lyrics(self, 
                                  lyrics: str, 
                                  existing_scenes: Optional[List[Dict[str, Any]]] = None,
                                  scene_count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Enhance or generate scenes from lyrics using the AI Director.
        
        This method either enhances existing scenes with rich narrative elements
        or generates completely new scenes if none are provided.
        
        Args:
            lyrics: The raw lyrics text
            existing_scenes: Optional list of existing scenes to enhance
            scene_count: Optional number of scenes to generate
            
        Returns:
            List of enhanced scene dictionaries
        """
        # Use Ollama if configured
        if self.use_ollama and self.ollama:
            return self._enhance_scenes_with_ollama(lyrics, existing_scenes, scene_count)
        
        # Otherwise use the built-in Director
        # If no existing scenes, generate new ones
        if not existing_scenes:
            logger.info(f"Generating {scene_count if scene_count else 'auto-determined'} scenes from lyrics")
            return self.director.generate_scenes_from_lyrics(lyrics, scene_count)
        
        # If we have existing scenes, enhance them
        logger.info(f"Enhancing {len(existing_scenes)} existing scenes with AI Director")
        
        # Generate a complete story from the lyrics
        story = self.director.create_story(lyrics)
        
        # Extract key story elements
        character_desc = story["character"]["description"]
        setting_desc = story["setting"]["description"]
        visual_style = story["visual_style"]
        genre = story["genre"]
        beats = story["narrative_arc"]["beats"]
        
        # Enhance each scene with narrative elements
        enhanced_scenes = []
        
        for i, scene in enumerate(existing_scenes):
            # Create a copy of the original scene
            enhanced_scene = scene.copy()
            
            # Add section type if not present
            if "section_type" not in enhanced_scene:
                # Try to determine section type from text or default to "verse"
                section_type = "verse"
                if i == 0:
                    section_type = "intro"
                elif i == len(existing_scenes) - 1:
                    section_type = "outro"
                enhanced_scene["section_type"] = section_type
            
            # Select a narrative beat for this scene
            beat_index = i % len(beats)
            narrative_beat = beats[beat_index]
            
            # Extract text from the scene
            scene_text = enhanced_scene.get("text", "")
            if not scene_text and "description" in enhanced_scene:
                scene_text = enhanced_scene["description"]
            
            # Create rich scene description based on section type
            section_type = enhanced_scene["section_type"]
            
            if section_type == "chorus":
                # Chorus scenes tend to be more dramatic and symbolic
                scene_prompt = (
                    f"{visual_style} {genre} music video scene with {character_desc} in a " +
                    f"dramatic chorus moment set in {setting_desc}. {narrative_beat}. " +
                    f"Visual interpretation of '{scene_text}'"
                )
            elif section_type == "verse":
                # Verse scenes develop the story
                scene_prompt = (
                    f"{visual_style} {genre} music video scene showing {character_desc} in " +
                    f"{setting_desc}, exploring the verse lyrics. {narrative_beat}. " +
                    f"Visual storytelling of '{scene_text}'"
                )
            elif section_type == "bridge":
                # Bridge scenes often show transformation
                scene_prompt = (
                    f"{visual_style} {genre} music video bridge scene with {character_desc} " +
                    f"experiencing a shift or revelation in {setting_desc}. {narrative_beat}. " +
                    f"Visual metaphor for '{scene_text}'"
                )
            elif section_type == "intro":
                # Intro scenes establish the world
                scene_prompt = (
                    f"{visual_style} {genre} music video opening scene introducing {setting_desc} " +
                    f"and {character_desc}. {narrative_beat}. " +
                    f"Setting the tone with '{scene_text}'"
                )
            elif section_type == "outro":
                # Outro scenes provide resolution
                scene_prompt = (
                    f"{visual_style} {genre} music video closing scene with {character_desc} " +
                    f"in {setting_desc}, bringing resolution. {narrative_beat}. " +
                    f"Final imagery of '{scene_text}'"
                )
            else:
                # Generic scene for other section types
                scene_prompt = (
                    f"{visual_style} {genre} music video scene depicting {character_desc} " +
                    f"in {setting_desc}. {narrative_beat}. " +
                    f"Visualizing '{scene_text}'"
                )
            
            # Update scene with enhanced prompt and narrative elements
            enhanced_scene["scene_prompt"] = scene_prompt
            enhanced_scene["narrative_beat"] = narrative_beat
            enhanced_scene["story_elements"] = {
                "character": character_desc,
                "setting": setting_desc,
                "visual_style": visual_style,
                "genre": genre
            }
            
            enhanced_scenes.append(enhanced_scene)
        
        return enhanced_scenes
    
    def _enhance_scenes_with_ollama(self, 
                                   lyrics: str, 
                                   existing_scenes: Optional[List[Dict[str, Any]]] = None,
                                   scene_count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Enhance or generate scenes using Ollama.
        
        Args:
            lyrics: The raw lyrics text
            existing_scenes: Optional list of existing scenes to enhance
            scene_count: Optional number of scenes to generate
            
        Returns:
            List of enhanced scene dictionaries
        """
        logger.info(f"Using Ollama with model {self.ollama_model} for scene generation")
        
        # Generate a story with Ollama
        story, error = self.ollama.generate_story_from_lyrics(lyrics)
        
        if error:
            logger.warning(f"Error generating story with Ollama: {error}. Falling back to built-in AI Director.")
            return self.director.generate_scenes_from_lyrics(lyrics, scene_count)
            
        # If no existing scenes, generate new ones with Ollama
        if not existing_scenes:
            scenes, error = self.ollama.generate_scenes_from_lyrics(lyrics, story, scene_count)
            
            if error:
                logger.warning(f"Error generating scenes with Ollama: {error}. Falling back to built-in AI Director.")
                return self.director.generate_scenes_from_lyrics(lyrics, scene_count)
                
            return scenes
        
        # If we have existing scenes, enhance them with Ollama story
        logger.info(f"Enhancing {len(existing_scenes)} existing scenes with Ollama")
        
        # Extract key story elements
        character_desc = story.get("character", {}).get("description", "A character")
        setting_desc = story.get("setting", {}).get("description", "A setting")
        visual_style = story.get("visual_style", "cinematic")
        genre = story.get("genre", "drama")
        beats = story.get("narrative_arc", {}).get("beats", ["Beginning", "Development", "Climax", "Resolution"])
        
        # Enhance each scene
        enhanced_scenes = []
        
        for i, scene in enumerate(existing_scenes):
            # Create a copy of the original scene
            enhanced_scene = scene.copy()
            
            # Add section type if not present
            if "section_type" not in enhanced_scene:
                # Try to determine section type from text or default to "verse"
                section_type = "verse"
                if i == 0:
                    section_type = "intro"
                elif i == len(existing_scenes) - 1:
                    section_type = "outro"
                enhanced_scene["section_type"] = section_type
            
            # Select a narrative beat for this scene
            beat_index = i % len(beats)
            narrative_beat = beats[beat_index]
            
            # Extract text from the scene
            scene_text = enhanced_scene.get("text", "")
            if not scene_text and "description" in enhanced_scene:
                scene_text = enhanced_scene["description"]
            
            # Create rich scene description based on section type
            section_type = enhanced_scene["section_type"]
            
            if section_type == "chorus":
                # Chorus scenes tend to be more dramatic and symbolic
                scene_prompt = (
                    f"{visual_style} {genre} music video scene with {character_desc} in a " +
                    f"dramatic chorus moment set in {setting_desc}. {narrative_beat}. " +
                    f"Visual interpretation of '{scene_text}'"
                )
            elif section_type == "verse":
                # Verse scenes develop the story
                scene_prompt = (
                    f"{visual_style} {genre} music video scene showing {character_desc} in " +
                    f"{setting_desc}, exploring the verse lyrics. {narrative_beat}. " +
                    f"Visual storytelling of '{scene_text}'"
                )
            elif section_type == "bridge":
                # Bridge scenes often show transformation
                scene_prompt = (
                    f"{visual_style} {genre} music video bridge scene with {character_desc} " +
                    f"experiencing a shift or revelation in {setting_desc}. {narrative_beat}. " +
                    f"Visual metaphor for '{scene_text}'"
                )
            elif section_type == "intro":
                # Intro scenes establish the world
                scene_prompt = (
                    f"{visual_style} {genre} music video opening scene introducing {setting_desc} " +
                    f"and {character_desc}. {narrative_beat}. " +
                    f"Setting the tone with '{scene_text}'"
                )
            elif section_type == "outro":
                # Outro scenes provide resolution
                scene_prompt = (
                    f"{visual_style} {genre} music video closing scene with {character_desc} " +
                    f"in {setting_desc}, bringing resolution. {narrative_beat}. " +
                    f"Final imagery of '{scene_text}'"
                )
            else:
                # Generic scene for other section types
                scene_prompt = (
                    f"{visual_style} {genre} music video scene depicting {character_desc} " +
                    f"in {setting_desc}. {narrative_beat}. " +
                    f"Visualizing '{scene_text}'"
                )
            
            # Update scene with enhanced prompt and narrative elements
            enhanced_scene["scene_prompt"] = scene_prompt
            enhanced_scene["narrative_beat"] = narrative_beat
            enhanced_scene["story_elements"] = {
                "character": character_desc,
                "setting": setting_desc,
                "visual_style": visual_style,
                "genre": genre
            }
            
            enhanced_scenes.append(enhanced_scene)
        
        return enhanced_scenes
    
    def get_story_summary(self, lyrics: str) -> str:
        """
        Get a text summary of the story derived from lyrics.
        
        Args:
            lyrics: The raw lyrics text
            
        Returns:
            Formatted string with story summary
        """
        # Use Ollama if configured
        if self.use_ollama and self.ollama:
            story, error = self.ollama.generate_story_from_lyrics(lyrics)
            
            if error:
                logger.warning(f"Error generating story with Ollama: {error}. Falling back to built-in AI Director.")
                return self.director.get_story_summary(lyrics)
                
            # Format story into a readable summary
            summary = f"# Music Video Story Treatment\n\n"
            summary += f"## Genre & Style\n"
            summary += f"**Genre:** {story.get('genre', 'Drama').title()}\n"
            summary += f"**Visual Style:** {story.get('visual_style', 'Cinematic').title()}\n\n"
            
            summary += f"## Main Character\n"
            summary += f"{story.get('character', {}).get('description', 'A character')}\n\n"
            
            summary += f"## Setting\n"
            summary += f"{story.get('setting', {}).get('description', 'A setting')}\n\n"
            
            summary += f"## Synopsis\n"
            summary += f"{story.get('narrative_arc', {}).get('synopsis', 'A story')}\n\n"
            
            summary += f"## Story Beats\n"
            for i, beat in enumerate(story.get('narrative_arc', {}).get('beats', [])):
                summary += f"{i+1}. {beat}\n"
                
            return summary
        
        # Otherwise use built-in director
        return self.director.get_story_summary(lyrics)
    
    def get_story_elements(self, lyrics: str) -> Dict[str, Any]:
        """
        Get the story elements derived from lyrics.
        
        Args:
            lyrics: The raw lyrics text
            
        Returns:
            Dictionary with story elements
        """
        # Use Ollama if configured
        if self.use_ollama and self.ollama:
            story, error = self.ollama.generate_story_from_lyrics(lyrics)
            
            if error:
                logger.warning(f"Error generating story with Ollama: {error}. Falling back to built-in AI Director.")
                return self.director.create_story(lyrics)
                
            return story
        
        # Otherwise use built-in director
        return self.director.create_story(lyrics)
    
    def save_story_to_file(self, lyrics: str, output_path: str) -> bool:
        """
        Save the generated story to a JSON file.
        
        Args:
            lyrics: The raw lyrics text
            output_path: Path to save the story JSON
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the story
            story = self.get_story_elements(lyrics)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(story, f, indent=2)
            
            logger.info(f"Saved story to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving story to file: {e}")
            return False
    
    def save_scenes_to_file(self, scenes: List[Dict[str, Any]], output_path: str) -> bool:
        """
        Save the generated scenes to a JSON file.
        
        Args:
            scenes: List of scene dictionaries
            output_path: Path to save the scenes JSON
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(scenes, f, indent=2)
            
            logger.info(f"Saved {len(scenes)} scenes to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving scenes to file: {e}")
            return False


# Example usage if run directly
if __name__ == "__main__":
    # Sample lyrics for testing
    sample_lyrics = """
[Verse 1]
Walking down an empty street
Shadows dance beneath my feet
City lights begin to glow
As the daylight starts to go

[Chorus]
In the darkness I can see
All the things that call to me
Whispers from another time
Echoes in this heart of mine
"""

    # Initialize the integration
    integration = DirectorIntegration(use_ollama=True)
    
    # Generate scenes
    scenes = integration.enhance_scenes_from_lyrics(sample_lyrics)
    
    # Get story summary
    summary = integration.get_story_summary(sample_lyrics)
    
    # Print the results
    print(summary)
    print("\nGENERATED SCENES:")
    for i, scene in enumerate(scenes):
        print(f"\nSCENE {i+1}:")
        print(f"Section: {scene['section_type']}")
        print(f"Text: {scene['text']}")
        print(f"Prompt: {scene['scene_prompt']}")
        print(f"Timestamp: {scene['timestamp']}s")
