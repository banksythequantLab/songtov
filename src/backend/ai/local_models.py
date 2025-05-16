"""
MaiVid Studio - Local Models Integration Module

This module provides integration with local LLM models through Ollama.
It allows the AI Director to use local models like Phi-3 as alternatives
to the built-in capabilities.
"""

import os
import json
import requests
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OllamaConnector:
    """
    Connector for local Ollama models like Phi-3.
    
    This class provides methods to interact with locally running Ollama models
    to generate content for the AI Director.
    """
    
    def __init__(self, model_name: str = "phi3:mini", api_base: str = "http://localhost:11434"):
        """
        Initialize the Ollama connector.
        
        Args:
            model_name: Name of the Ollama model to use (default: phi3:mini)
            api_base: Base URL for the Ollama API
        """
        self.model_name = model_name
        self.api_base = api_base
        self.api_url = f"{api_base}/api/generate"
        
        logger.info(f"Initialized OllamaConnector with model {model_name}")
        
    def check_availability(self) -> Tuple[bool, Optional[str]]:
        """
        Check if the Ollama service and specified model are available.
        
        Returns:
            Tuple: (is_available, error_message)
        """
        try:
            # Check if Ollama service is running
            response = requests.get(f"{self.api_base}/api/tags")
            
            if response.status_code != 200:
                return False, f"Ollama service is not available. Status code: {response.status_code}"
                
            # Check if model is available
            models = response.json().get("models", [])
            if not any(model.get("name") == self.model_name for model in models):
                return False, f"Model {self.model_name} is not available. Available models: {[model.get('name') for model in models]}"
                
            return True, None
            
        except requests.RequestException as e:
            return False, f"Error connecting to Ollama: {str(e)}"
    
    def generate_text(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate text using the Ollama model.
        
        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature parameter for generation
            
        Returns:
            Tuple: (generated_text, error_message)
        """
        try:
            # Check if Ollama is available
            available, error = self.check_availability()
            if not available:
                return None, error
            
            # Prepare request payload
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            # Send request to Ollama
            response = requests.post(self.api_url, json=data)
            
            if response.status_code != 200:
                return None, f"Error generating text. Status code: {response.status_code}"
                
            result = response.json()
            generated_text = result.get("response", "")
            
            return generated_text, None
            
        except requests.RequestException as e:
            return None, f"Error calling Ollama API: {str(e)}"
        except json.JSONDecodeError:
            return None, "Invalid response from Ollama API"
        except Exception as e:
            return None, f"Unexpected error: {str(e)}"
    
    def generate_story_from_lyrics(self, lyrics: str) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Generate a complete story from lyrics using the local Ollama model.
        
        Args:
            lyrics: The raw lyrics text
            
        Returns:
            Tuple: (story_dict, error_message)
        """
        # Create a prompt for story generation
        prompt = f"""
You're an AI story creator for music videos. Based on these lyrics, create a cohesive story with characters, setting, and narrative arc.
Analyze the lyrics for tone, themes, and imagery. Return a JSON object with the following structure:

{{
  "keywords": ["list", "of", "key", "themes"],
  "sentiment": {{
    "overall": 0.5,  // -1.0 to 1.0
    "is_positive": true,
    "is_negative": false,
    "intensity": 0.5  // 0.0 to 1.0
  }},
  "character": {{
    "description": "Detailed character description",
    "traits": ["trait1", "trait2", "trait3"]
  }},
  "setting": {{
    "description": "Detailed setting description",
    "primary_type": "urban/nature/fantasy/etc"
  }},
  "narrative_arc": {{
    "story_type": "journey/transformation/love/loss/etc",
    "beats": ["story beat 1", "story beat 2", "story beat 3", "story beat 4", "story beat 5"],
    "synopsis": "Short story synopsis"
  }},
  "visual_style": "atmospheric/dreamy/gritty/vibrant/etc",
  "genre": "drama/fantasy/romance/sci-fi/etc"
}}

LYRICS:
{lyrics}

JSON:
"""
        
        # Generate the story using Ollama
        generated_text, error = self.generate_text(prompt)
        
        if error:
            return {}, error
            
        # Extract the JSON content
        try:
            # Sometimes the model might surround the JSON with ```json or other markers
            json_text = generated_text
            
            # Try to find the JSON object within the text
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0].strip()
                
            # Parse the JSON
            story = json.loads(json_text)
            
            return story, None
            
        except json.JSONDecodeError as e:
            return {}, f"Error parsing generated JSON: {str(e)}"
        except Exception as e:
            return {}, f"Unexpected error processing story: {str(e)}"
    
    def generate_scenes_from_lyrics(self, lyrics: str, story: Dict[str, Any], scene_count: int = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Generate scenes from lyrics using the local Ollama model.
        
        Args:
            lyrics: The raw lyrics text
            story: The story dict generated by generate_story_from_lyrics
            scene_count: Number of scenes to generate (default: auto-determine)
            
        Returns:
            Tuple: (scenes_list, error_message)
        """
        # Extract key story elements
        character_desc = story.get("character", {}).get("description", "A main character")
        setting_desc = story.get("setting", {}).get("description", "A setting")
        visual_style = story.get("visual_style", "cinematic")
        genre = story.get("genre", "drama")
        narrative_beats = story.get("narrative_arc", {}).get("beats", ["Beginning", "Middle", "Climax", "Resolution", "End"])
        
        # Determine scene count if not specified
        if scene_count is None:
            # Extract sections from lyrics
            section_pattern = r'\[(verse|chorus|bridge|outro|intro|repeat).*?\](.*?)(?=\[|\Z)'
            import re
            matches = re.findall(section_pattern, lyrics, re.DOTALL)
            
            # Base count on number of sections (min 4, max 12)
            scene_count = min(max(4, len(matches)), 12)
        
        # Create a prompt for scene generation
        prompt = f"""
You're an AI director for music videos. Based on these lyrics and the provided story elements, create {scene_count} detailed scene descriptions.
Each scene should include a textual prompt that can be used to generate an image, and should fit into the overall narrative.
Return a JSON array with the following structure for each scene:

[
  {{
    "text": "Short text from lyrics this scene is based on",
    "scene_prompt": "Detailed visual scene description for image generation",
    "timestamp": 0,  // Time in seconds when this scene appears
    "section_type": "verse/chorus/bridge/intro/outro",
    "narrative_beat": "Which part of the story arc this represents",
    "scene_number": 1  // Sequential number
  }},
  // More scenes...
]

STORY ELEMENTS:
- Character: {character_desc}
- Setting: {setting_desc}
- Visual Style: {visual_style}
- Genre: {genre}
- Narrative Beats: {", ".join(narrative_beats)}

LYRICS:
{lyrics}

JSON:
"""
        
        # Generate the scenes using Ollama
        generated_text, error = self.generate_text(prompt)
        
        if error:
            return [], error
            
        # Extract the JSON content
        try:
            # Sometimes the model might surround the JSON with ```json or other markers
            json_text = generated_text
            
            # Try to find the JSON array within the text
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0].strip()
                
            # Parse the JSON
            scenes = json.loads(json_text)
            
            # Ensure it's a list
            if not isinstance(scenes, list):
                return [], "Generated content is not a list of scenes"
                
            # Add story elements to each scene
            for scene in scenes:
                scene["story_elements"] = {
                    "character": character_desc,
                    "setting": setting_desc,
                    "visual_style": visual_style,
                    "genre": genre
                }
                
            return scenes, None
            
        except json.JSONDecodeError as e:
            return [], f"Error parsing generated JSON: {str(e)}"
        except Exception as e:
            return [], f"Unexpected error processing scenes: {str(e)}"


# Example usage if run directly
if __name__ == "__main__":
    # Initialize the connector
    connector = OllamaConnector(model_name="phi3:mini")
    
    # Check if Ollama is available
    available, error = connector.check_availability()
    if not available:
        print(f"Ollama is not available: {error}")
        exit(1)
        
    # Example lyrics
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
    
    # Generate a story
    print("Generating story...")
    story, error = connector.generate_story_from_lyrics(sample_lyrics)
    
    if error:
        print(f"Error generating story: {error}")
        exit(1)
        
    print("Story generation successful!")
    print(json.dumps(story, indent=2))
    
    # Generate scenes
    print("\nGenerating scenes...")
    scenes, error = connector.generate_scenes_from_lyrics(sample_lyrics, story)
    
    if error:
        print(f"Error generating scenes: {error}")
        exit(1)
        
    print("Scene generation successful!")
    print(json.dumps(scenes, indent=2))
