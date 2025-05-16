"""
MaiVid Studio - AI Director Module

This module implements an AI "Director" that can create cohesive storytelling
and rich scene descriptions based on lyrics. It enhances the basic scene generation
with narrative elements, character development, and visual continuity.
"""

import os
import re
import json
import logging
import random
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIDirector:
    """
    AI Director class that creates cohesive stories and detailed scenes from song lyrics.
    
    The Director analyzes lyrics, creates characters, develops narrative arcs, and 
    generates detailed visuals that maintain consistency throughout the music video.
    """
    
    def __init__(self):
        """Initialize the AI Director."""
        # Story elements
        self.genres = [
            "science fiction", "fantasy", "romance", "drama", "thriller", 
            "action", "adventure", "historical", "supernatural", "noir",
            "cyberpunk", "steampunk", "post-apocalyptic", "western", "surreal"
        ]
        
        self.moods = [
            "dark", "uplifting", "melancholic", "hopeful", "tense", 
            "dreamy", "energetic", "calm", "chaotic", "mysterious",
            "nostalgic", "romantic", "eerie", "joyful", "angry"
        ]
        
        self.settings = [
            "urban city", "rural countryside", "coastal town", "desert landscape", 
            "futuristic metropolis", "ancient ruins", "mysterious forest", 
            "underwater world", "mountain range", "neon-lit streets",
            "space station", "alien planet", "medieval castle", "underground cavern", 
            "floating islands"
        ]
        
        self.visual_styles = [
            "cinematic", "anime", "noir", "experimental", "documentary", 
            "hand-drawn", "minimalist", "hyper-realistic", "surrealist", 
            "retro", "vaporwave", "watercolor", "glitch art", "gothic",
            "art deco", "impressionist", "comic book", "silhouette", "low poly"
        ]
        
        # Cache for the story elements
        self.story_cache = {}
        
    def _extract_keywords(self, lyrics: str, count: int = 10) -> List[str]:
        """
        Extract the most significant keywords from lyrics.
        
        Args:
            lyrics: The raw lyrics text
            count: Maximum number of keywords to extract
            
        Returns:
            List of extracted keywords
        """
        # Remove section markers and clean the text
        clean_lyrics = re.sub(r'\[(verse|chorus|bridge|outro|intro|repeat).*?\]', '', lyrics)
        
        # Tokenize into words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', clean_lyrics.lower())
        
        # Filter out common stopwords
        stopwords = {
            'the', 'and', 'that', 'have', 'for', 'not', 'with', 'you', 'this', 'but',
            'his', 'her', 'she', 'him', 'they', 'them', 'from', 'will', 'would', 'could',
            'should', 'what', 'when', 'where', 'which', 'who', 'whom', 'how', 'been',
            'were', 'there', 'their', 'these', 'those', 'then', 'than', 'that', 'into',
            'your', 'just', 'don', 'now', 'get', 'got', 'like', 'come', 'some', 'only',
        }
        
        filtered_words = [word for word in words if word not in stopwords]
        
        # Count word frequencies
        word_count = {}
        for word in filtered_words:
            if word in word_count:
                word_count[word] += 1
            else:
                word_count[word] = 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:count]]
    
    def _analyze_sentiment(self, lyrics: str) -> Dict[str, float]:
        """
        Analyze the sentiment and emotional tone of the lyrics.
        
        Args:
            lyrics: The raw lyrics text
            
        Returns:
            Dictionary with sentiment scores
        """
        # Very simple sentiment analysis based on keyword presence
        # In a real implementation, this would use a proper NLP model
        
        positive_words = {
            'love', 'happy', 'joy', 'wonderful', 'beautiful', 'peace', 'hope',
            'dream', 'light', 'smile', 'laugh', 'bright', 'paradise', 'heaven',
            'good', 'great', 'best', 'better', 'amazing', 'awesome', 'perfect'
        }
        
        negative_words = {
            'hate', 'sad', 'pain', 'hurt', 'angry', 'fear', 'dark', 'cry',
            'die', 'death', 'kill', 'lost', 'broken', 'alone', 'empty',
            'bad', 'worse', 'worst', 'terrible', 'hell', 'nightmare'
        }
        
        # Clean lyrics for analysis
        clean_lyrics = re.sub(r'\[(verse|chorus|bridge|outro|intro|repeat).*?\]', '', lyrics)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', clean_lyrics.lower())
        
        # Count positive and negative words
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        total_words = len(words)
        
        # Calculate sentiment scores (avoid division by zero)
        if total_words > 0:
            positive_score = positive_count / total_words
            negative_score = negative_count / total_words
        else:
            positive_score = 0.0
            negative_score = 0.0
        
        # Overall sentiment (-1.0 to 1.0)
        overall = positive_score - negative_score
        
        return {
            "positive": positive_score,
            "negative": negative_score,
            "overall": overall,
            "is_positive": overall > 0,
            "is_negative": overall < 0,
            "is_neutral": abs(overall) < 0.1,
            "intensity": abs(overall)
        }
    
    def _identify_narrative_structure(self, lyrics: str) -> Dict[str, Any]:
        """
        Identify the narrative structure in the lyrics.
        
        Args:
            lyrics: The raw lyrics text
            
        Returns:
            Dictionary with narrative structure information
        """
        # Extract sections
        section_pattern = r'\[(verse|chorus|bridge|outro|intro|repeat).*?\](.*?)(?=\[|\Z)'
        matches = re.findall(section_pattern, lyrics, re.DOTALL)
        
        # Count section types
        section_counts = {}
        section_text = {}
        
        for section_type, text in matches:
            section_type = section_type.lower()
            if section_type in section_counts:
                section_counts[section_type] += 1
            else:
                section_counts[section_type] = 1
            
            # Store text by section type
            if section_type not in section_text:
                section_text[section_type] = []
            section_text[section_type].append(text.strip())
        
        # Determine if there's a repetitive structure (common in songs)
        has_chorus = "chorus" in section_counts and section_counts["chorus"] > 1
        has_verses = "verse" in section_counts and section_counts["verse"] >= 1
        has_bridge = "bridge" in section_counts
        
        # Identify possible narrative types
        if has_verses and has_chorus:
            if has_bridge:
                narrative_type = "complete_song"  # Verse-Chorus-Bridge structure
            else:
                narrative_type = "verse_chorus"  # Simple Verse-Chorus structure
        elif has_verses and section_counts.get("verse", 0) >= 3:
            narrative_type = "ballad"  # Multiple verses telling a story
        elif len(section_counts) <= 1:
            narrative_type = "monologue"  # Single section, like a spoken word piece
        else:
            narrative_type = "freestyle"  # Mixed structure
        
        return {
            "section_counts": section_counts,
            "section_text": section_text,
            "narrative_type": narrative_type,
            "has_chorus": has_chorus,
            "has_verses": has_verses,
            "has_bridge": has_bridge,
            "total_sections": len(matches)
        }
    
    def _generate_character(self, lyrics: str, sentiment: Dict[str, float]) -> Dict[str, str]:
        """
        Generate a character based on lyrics content.
        
        Args:
            lyrics: The lyrics text
            sentiment: Sentiment analysis results
            
        Returns:
            Dictionary with character details
        """
        # Extract potential character descriptors from lyrics
        clean_lyrics = re.sub(r'\[(verse|chorus|bridge|outro|intro|repeat).*?\]', '', lyrics)
        
        # Look for character descriptors (adjectives followed by person nouns)
        person_nouns = [
            'man', 'woman', 'boy', 'girl', 'person', 'child', 'guy', 'lady',
            'friend', 'lover', 'stranger', 'hero', 'villain', 'angel', 'devil',
            'king', 'queen', 'prince', 'princess', 'warrior', 'fighter', 'soldier',
            'artist', 'singer', 'dancer', 'player', 'rider', 'driver', 'traveler'
        ]
        
        # Look for direct character mentions
        character_pattern = r'(?:the|a|my|your|our|their)\s+([a-z]+)\s+(' + '|'.join(person_nouns) + r')'
        character_matches = re.findall(character_pattern, clean_lyrics.lower())
        
        # Or any use of person nouns
        person_matches = re.findall(r'\b(' + '|'.join(person_nouns) + r')\b', clean_lyrics.lower())
        
        # Determine character gender (random if not obvious from lyrics)
        gendered_nouns = {
            'masculine': ['man', 'boy', 'guy', 'king', 'prince', 'hero', 'him', 'his', 'he'],
            'feminine': ['woman', 'girl', 'lady', 'queen', 'princess', 'heroine', 'her', 'she']
        }
        
        gender_hints = {
            'masculine': sum(1 for word in gendered_nouns['masculine'] if word in clean_lyrics.lower()),
            'feminine': sum(1 for word in gendered_nouns['feminine'] if word in clean_lyrics.lower())
        }
        
        if gender_hints['masculine'] > gender_hints['feminine']:
            gender = "masculine"
        elif gender_hints['feminine'] > gender_hints['masculine']:
            gender = "feminine"
        else:
            gender = random.choice(["masculine", "feminine", "ambiguous"])
        
        # Use sentiment to influence character traits
        if sentiment['is_positive']:
            traits = random.sample([
                "optimistic", "hopeful", "determined", "compassionate", "brave",
                "resilient", "confident", "joyful", "peaceful", "generous"
            ], 3)
        elif sentiment['is_negative']:
            traits = random.sample([
                "troubled", "melancholic", "conflicted", "desperate", "haunted",
                "rebellious", "vengeful", "lonely", "anxious", "bitter"
            ], 3)
        else:
            traits = random.sample([
                "mysterious", "contemplative", "stoic", "complex", "reserved",
                "thoughtful", "introspective", "observant", "composed", "enigmatic"
            ], 3)
        
        # Create character description
        if character_matches:
            # Use the most mentioned character type
            adj, noun = max(set(character_matches), key=character_matches.count)
            description = f"A {adj} {noun} who is {', '.join(traits[:-1])} and {traits[-1]}"
        elif person_matches:
            # Use the most mentioned person noun
            noun = max(set(person_matches), key=person_matches.count)
            description = f"A {traits[0]} {noun} who is {traits[1]} and {traits[2]}"
        else:
            # Create a generic character based on sentiment
            if gender == "masculine":
                noun = random.choice(["man", "guy", "boy"])
            elif gender == "feminine":
                noun = random.choice(["woman", "girl", "lady"])
            else:
                noun = random.choice(["person", "individual", "character", "figure"])
                
            description = f"A {traits[0]} {noun} who is {traits[1]} and {traits[2]}"
        
        return {
            "description": description,
            "traits": traits,
            "gender": gender
        }
    
    def _generate_setting(self, lyrics: str, sentiment: Dict[str, float]) -> Dict[str, str]:
        """
        Generate a setting based on lyrics content.
        
        Args:
            lyrics: The lyrics text
            sentiment: Sentiment analysis results
            
        Returns:
            Dictionary with setting details
        """
        # Look for setting keywords in lyrics
        clean_lyrics = re.sub(r'\[(verse|chorus|bridge|outro|intro|repeat).*?\]', '', lyrics)
        
        # Common setting indicators
        setting_keywords = {
            "city": ["city", "street", "building", "skyline", "urban", "downtown", "traffic"],
            "nature": ["forest", "mountain", "river", "ocean", "beach", "sky", "field", "garden"],
            "home": ["home", "house", "room", "bedroom", "kitchen", "door", "window"],
            "road": ["road", "highway", "car", "drive", "journey", "travel", "path"],
            "night": ["night", "dark", "stars", "moon", "midnight", "darkness"],
            "fantasy": ["dream", "magic", "kingdom", "castle", "dragon", "fairy", "wizard"],
            "future": ["future", "space", "planet", "robot", "cyber", "digital", "virtual"]
        }
        
        # Count setting keywords in lyrics
        setting_scores = {}
        for setting, keywords in setting_keywords.items():
            score = sum(1 for keyword in keywords if keyword in clean_lyrics.lower())
            if score > 0:
                setting_scores[setting] = score
        
        # Determine primary setting based on keywords or sentiment
        if setting_scores:
            primary_setting = max(setting_scores.items(), key=lambda x: x[1])[0]
        else:
            # Default based on sentiment
            if sentiment['is_positive']:
                primary_setting = random.choice(["nature", "home", "fantasy"])
            elif sentiment['is_negative']:
                primary_setting = random.choice(["city", "night", "road"])
            else:
                primary_setting = random.choice(list(setting_keywords.keys()))
        
        # Generate setting description based on primary setting
        if primary_setting == "city":
            time = random.choice(["night", "day", "sunset", "dawn"])
            weather = random.choice(["rainy", "clear", "foggy", "stormy"])
            
            if sentiment['is_positive']:
                setting_desc = random.choice([
                    f"A vibrant city during {time} with {weather} weather, filled with life and energy",
                    f"A bustling metropolis with gleaming skyscrapers under a {weather} {time} sky",
                    f"A lively downtown area with colorful lights and people enjoying the {weather} {time}"
                ])
            else:
                setting_desc = random.choice([
                    f"A gritty urban landscape during a {weather} {time}, shadows casting across empty streets",
                    f"A towering city of concrete and steel, cold and impersonal in the {weather} {time}",
                    f"A maze of narrow alleyways and forgotten corners in a {weather} {time} city"
                ])
        
        elif primary_setting == "nature":
            environment = random.choice(["forest", "mountains", "beach", "meadow", "lake"])
            weather = random.choice(["sunny", "misty", "rainy", "snowy", "windy"])
            
            if sentiment['is_positive']:
                setting_desc = random.choice([
                    f"A peaceful {environment} bathed in {weather} light, teeming with vibrant life",
                    f"A serene {environment} landscape under a {weather} sky, untouched and pristine",
                    f"A majestic {environment} vista with {weather} conditions creating a magical atmosphere"
                ])
            else:
                setting_desc = random.choice([
                    f"A wild, untamed {environment} during {weather} conditions, beautiful yet dangerous",
                    f"A remote {environment} isolated by {weather}, far from civilization",
                    f"An ancient {environment} with twisted forms and shadows, {weather} adding to the mood"
                ])
        
        elif primary_setting == "road":
            road_type = random.choice(["highway", "country road", "desert road", "coastal highway", "mountain pass"])
            vehicle = random.choice(["car", "motorcycle", "vintage convertible", "truck", "van"])
            
            setting_desc = random.choice([
                f"An endless {road_type} stretching to the horizon, traveled by a {vehicle}",
                f"A winding {road_type} cutting through dramatic landscapes, a {vehicle} making the journey",
                f"A {vehicle} journey along a {road_type}, symbolic of life's path and choices"
            ])
            
        elif primary_setting == "night":
            location = random.choice(["city", "countryside", "beach", "mountains", "desert"])
            feature = random.choice(["stars", "moon", "city lights", "streetlights", "campfire"])
            
            setting_desc = random.choice([
                f"A {location} at night, illuminated by {feature}, creating a world of shadows and mystery",
                f"The quiet darkness of night in a {location}, with {feature} providing the only light",
                f"A night scene in the {location} where the {feature} creates a magical atmosphere"
            ])
            
        elif primary_setting == "fantasy":
            realm = random.choice(["magical kingdom", "enchanted forest", "mythical realm", "fairy tale world", "dreamscape"])
            element = random.choice(["floating islands", "ancient magic", "mythical creatures", "crystal formations", "impossible architecture"])
            
            setting_desc = random.choice([
                f"A {realm} filled with {element}, defying the laws of reality",
                f"An otherworldly {realm} where {element} create a sense of wonder and possibility",
                f"A fantastical {realm} with {element} that tell stories of ancient magic"
            ])
        
        elif primary_setting == "future":
            tech_level = random.choice(["high-tech", "post-apocalyptic", "cyber-organic", "space-age", "neo-retro"])
            feature = random.choice(["gleaming spires", "floating structures", "holographic displays", "artificial intelligence", "space vessels"])
            
            if sentiment['is_positive']:
                setting_desc = random.choice([
                    f"A utopian {tech_level} future with {feature} representing humanity's achievements",
                    f"A bright {tech_level} world where {feature} have solved many of humanity's problems",
                    f"An optimistic vision of a {tech_level} tomorrow, with {feature} enhancing human life"
                ])
            else:
                setting_desc = random.choice([
                    f"A dystopian {tech_level} landscape where {feature} dominate a troubled society",
                    f"A harsh {tech_level} reality where {feature} highlight the divide between haves and have-nots",
                    f"A dark {tech_level} future where humanity struggles amidst {feature} of their own creation"
                ])
        
        else:  # Home or default
            home_type = random.choice(["cozy apartment", "family house", "cabin", "modern home", "studio space"])
            detail = random.choice(["warm lighting", "personal mementos", "view from the window", "comfortable furnishings"])
            
            setting_desc = random.choice([
                f"A {home_type} with {detail} that tell a story of the people who live there",
                f"The intimate space of a {home_type}, where {detail} create a sense of identity",
                f"A personal sanctuary in the form of a {home_type}, with {detail} adding character"
            ])
        
        # Add time of day if not already specified
        if "night" not in primary_setting and "night" not in setting_desc.lower():
            time_of_day = random.choice(["morning", "afternoon", "evening", "sunset", "dawn", "dusk"])
            setting_desc += f", set during the {time_of_day}"
        
        return {
            "description": setting_desc,
            "primary_type": primary_setting
        }
    
    def _craft_narrative_arc(self, lyrics: str, narrative_structure: Dict[str, Any], sentiment: Dict[str, float]) -> Dict[str, Any]:
        """
        Create a narrative arc for the music video.
        
        Args:
            lyrics: The lyrics text
            narrative_structure: The identified narrative structure
            sentiment: Sentiment analysis results
            
        Returns:
            Dictionary with narrative arc details
        """
        # Extract key sections from narrative structure
        section_text = narrative_structure["section_text"]
        narrative_type = narrative_structure["narrative_type"]
        
        # Determine story type based on narrative structure and sentiment
        if narrative_type == "ballad" or narrative_type == "complete_song":
            # These typically tell a clear story
            if sentiment["is_positive"]:
                if sentiment["intensity"] > 0.3:
                    story_type = random.choice(["triumph", "romance", "adventure", "reunion"])
                else:
                    story_type = random.choice(["growth", "discovery", "friendship", "healing"])
            elif sentiment["is_negative"]:
                if sentiment["intensity"] > 0.3:
                    story_type = random.choice(["tragedy", "conflict", "loss", "struggle"])
                else:
                    story_type = random.choice(["nostalgia", "separation", "regret", "longing"])
            else:
                story_type = random.choice(["journey", "reflection", "transformation", "connection"])
        else:
            # More abstract or theme-based for other structures
            if sentiment["is_positive"]:
                story_type = random.choice(["celebration", "hope", "beauty", "freedom"])
            elif sentiment["is_negative"]:
                story_type = random.choice(["introspection", "questioning", "solitude", "tension"])
            else:
                story_type = random.choice(["symbolism", "duality", "contrast", "cycles"])
        
        # Generate story beats based on story type
        if story_type in ["triumph", "growth", "adventure"]:
            beats = [
                "Introduction of the protagonist in their ordinary world",
                "A challenge or opportunity appears",
                "Journey of facing obstacles and growing",
                "Moment of achievement or realization",
                "Celebration of growth or new perspective"
            ]
        elif story_type in ["romance", "friendship", "connection"]:
            beats = [
                "Two characters in separate worlds or mindsets",
                "First meeting or reconnection",
                "Moments of building connection",
                "Challenge or test of the relationship",
                "Resolution and deeper understanding"
            ]
        elif story_type in ["tragedy", "loss", "regret"]:
            beats = [
                "Initial state of happiness or normalcy",
                "Signs of approaching difficulty",
                "Critical moment of loss or failure",
                "Confronting the consequences",
                "Finding meaning or acceptance in aftermath"
            ]
        elif story_type in ["journey", "transformation"]:
            beats = [
                "Beginning in a confined or limited state",
                "Catalyst for change or departure",
                "Experience of new perspectives",
                "Integration of new understanding",
                "Return with transformed identity"
            ]
        elif story_type in ["symbolism", "duality", "contrast"]:
            beats = [
                "Establishment of core visual motif",
                "Introduction of contrasting elements",
                "Interplay and tension between opposites",
                "Mergence or transformation of visual themes",
                "Resolution through visual synthesis"
            ]
        else:
            # Default abstract progression
            beats = [
                "Visual introduction of key theme",
                "Expansion and exploration of theme",
                "Intensification or complication",
                "Climactic visual moment",
                "Thematic resolution or echo"
            ]
        
        # Create a synopsis
        keywords = self._extract_keywords(lyrics, 5)
        keyword_phrase = ", ".join(keywords)
        
        if narrative_type in ["ballad", "complete_song"]:
            synopsis = f"A {story_type} story following a character through a journey of {keyword_phrase}, depicting how they navigate challenges and change."
        elif narrative_type == "verse_chorus":
            synopsis = f"A thematic exploration of {keyword_phrase}, contrasting imagery between verses and creating powerful visual metaphors during the chorus."
        else:
            synopsis = f"An abstract visual poem exploring {keyword_phrase}, using symbolism and emotional imagery to convey the song's essence."
        
        return {
            "story_type": story_type,
            "beats": beats,
            "synopsis": synopsis
        }
    
    def create_story(self, lyrics: str) -> Dict[str, Any]:
        """
        Create a complete story from lyrics.
        
        Args:
            lyrics: The raw lyrics text
            
        Returns:
            Dictionary with complete story elements
        """
        # Use cached story if already analyzed these lyrics
        lyrics_hash = hash(lyrics)
        if lyrics_hash in self.story_cache:
            return self.story_cache[lyrics_hash]
        
        # Analyze lyrics for sentiment
        sentiment = self._analyze_sentiment(lyrics)
        
        # Identify narrative structure
        narrative_structure = self._identify_narrative_structure(lyrics)
        
        # Extract keywords
        keywords = self._extract_keywords(lyrics)
        
        # Create story elements
        character = self._generate_character(lyrics, sentiment)
        setting = self._generate_setting(lyrics, sentiment)
        narrative_arc = self._craft_narrative_arc(lyrics, narrative_structure, sentiment)
        
        # Select visual style based on all these elements
        if sentiment["is_positive"]:
            if setting["primary_type"] in ["nature", "fantasy"]:
                visual_styles = ["dreamy", "colorful", "magical", "vibrant", "surreal"]
            elif setting["primary_type"] in ["city", "future"]:
                visual_styles = ["sleek", "vibrant", "dynamic", "luminous", "stylized"]
            else:
                visual_styles = ["warm", "bright", "flowing", "colorful", "lively"]
        elif sentiment["is_negative"]:
            if setting["primary_type"] in ["night", "city"]:
                visual_styles = ["noir", "moody", "contrasty", "dystopian", "gritty"]
            elif setting["primary_type"] in ["nature", "road"]:
                visual_styles = ["desolate", "atmospheric", "weathered", "stark", "moody"]
            else:
                visual_styles = ["somber", "shadowy", "muted", "tense", "dramatic"]
        else:
            visual_styles = ["atmospheric", "contemplative", "textured", "ethereal", "balanced"]
        
        # Choose the final style
        visual_style = random.choice(visual_styles)
        
        # Choose a genre based on all elements
        if setting["primary_type"] in ["future", "city"] and sentiment["is_negative"]:
            genre = "cyberpunk"
        elif setting["primary_type"] == "fantasy" and sentiment["is_positive"]:
            genre = "fantasy"
        elif narrative_arc["story_type"] in ["romance", "connection"] and sentiment["is_positive"]:
            genre = "romance"
        elif narrative_arc["story_type"] in ["triumph", "adventure"]:
            genre = "adventure"
        elif setting["primary_type"] == "night" and sentiment["is_negative"]:
            genre = "noir"
        elif narrative_arc["story_type"] in ["symbolism", "duality"]:
            genre = "surreal"
        else:
            genre = random.choice(self.genres)
        
        # Create the complete story
        story = {
            "keywords": keywords,
            "sentiment": sentiment,
            "character": character,
            "setting": setting,
            "narrative_arc": narrative_arc,
            "visual_style": visual_style,
            "genre": genre
        }
        
        # Cache the story
        self.story_cache[lyrics_hash] = story
        
        return story
    
    def generate_scenes_from_lyrics(self, lyrics: str, scene_count: int = None) -> List[Dict[str, Any]]:
        """
        Generate a sequence of scenes with rich descriptions based on lyrics.
        
        Args:
            lyrics: The raw lyrics text
            scene_count: Number of scenes to generate (default: auto-determine)
            
        Returns:
            List of scene dictionaries with rich descriptions
        """
        # Extract sections from lyrics
        section_pattern = r'\[(verse|chorus|bridge|outro|intro|repeat).*?\](.*?)(?=\[|\Z)'
        matches = re.findall(section_pattern, lyrics, re.DOTALL)
        
        # If no sections found, default to basic scenes
        if not matches:
            return self._generate_default_scenes()
        
        # Create story elements for consistency
        story = self.create_story(lyrics)
        
        # Determine scene count if not specified
        if scene_count is None:
            # Base scene count on number of sections, but with limits
            scene_count = min(max(4, len(matches)), 12)
        
        # Create a narrative distribution of scenes
        # For a typical music video, we want to balance section types
        sorted_sections = []
        
        # Prioritize key sections with this order
        priority_order = ["chorus", "verse", "bridge", "intro", "outro"]
        
        # Group sections by type
        sections_by_type = {}
        for i, (section_type, text) in enumerate(matches):
            section_type = section_type.lower()
            if section_type not in sections_by_type:
                sections_by_type[section_type] = []
            
            # Add tuple of (section_type, text, original_index)
            sections_by_type[section_type].append((section_type, text, i))
        
        # Add sections in priority order
        remaining_count = scene_count
        for priority_type in priority_order:
            if priority_type in sections_by_type:
                # Determine how many of this type to include
                if priority_type == "chorus" and remaining_count >= 2:
                    # For chorus, include all instances (they're important)
                    count = min(len(sections_by_type[priority_type]), remaining_count)
                    selected = sections_by_type[priority_type][:count]
                    sorted_sections.extend(selected)
                    remaining_count -= count
                else:
                    # For other types, be more selective
                    count = min(len(sections_by_type[priority_type]), remaining_count // 2 + 1)
                    selected = sections_by_type[priority_type][:count]
                    sorted_sections.extend(selected)
                    remaining_count -= count
        
        # If we still need more scenes, add remaining sections by original order
        if remaining_count > 0:
            remaining_sections = []
            for section_type, sections in sections_by_type.items():
                for section in sections:
                    if section not in sorted_sections:
                        remaining_sections.append(section)
            
            # Sort by original index
            remaining_sections.sort(key=lambda x: x[2])
            
            # Add up to remaining_count
            sorted_sections.extend(remaining_sections[:remaining_count])
        
        # Sort scenes by original order
        sorted_sections.sort(key=lambda x: x[2])
        
        # Limit to scene_count
        sorted_sections = sorted_sections[:scene_count]
        
        # Now create rich scenes based on the story
        scenes = []
        
        # Narrative elements for consistent storytelling
        character_desc = story["character"]["description"]
        setting_desc = story["setting"]["description"]
        visual_style = story["visual_style"]
        genre = story["genre"]
        beats = story["narrative_arc"]["beats"]
        
        # Track which beats we've used
        used_beats = []
        
        # Create scenes
        for i, (section_type, section_text, original_index) in enumerate(sorted_sections):
            # Clean the section text
            text = section_text.strip()
            
            # Extract first couple of lines for the core content
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if not lines:
                continue
                
            # Use first two lines (or one if that's all we have)
            if len(lines) > 1:
                scene_text = f"{lines[0]} {lines[1]}"
            else:
                scene_text = lines[0]
            
            # Truncate if too long
            scene_text = scene_text[:100] if len(scene_text) > 100 else scene_text
            
            # Choose a narrative beat if available
            beat_index = i % len(beats)
            while beat_index in used_beats and len(used_beats) < len(beats):
                beat_index = (beat_index + 1) % len(beats)
            
            used_beats.append(beat_index)
            narrative_beat = beats[beat_index]
            
            # Create different scene descriptions based on section type
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
            
            # Create scene dictionary
            scene = {
                "text": scene_text,  # Core text from lyrics
                "scene_prompt": scene_prompt,  # Rich scene description
                "timestamp": i * 15,  # Simple timing at 15 seconds per scene
                "section_type": section_type,  # Type of section
                "narrative_beat": narrative_beat,  # Story beat for this scene
                "scene_number": i + 1,  # Scene number
                "story_elements": {
                    "character": character_desc,
                    "setting": setting_desc,
                    "visual_style": visual_style,
                    "genre": genre
                }
            }
            
            scenes.append(scene)
        
        # If we somehow don't have enough scenes, add some generic ones
        while len(scenes) < scene_count:
            scene_idx = len(scenes)
            
            # Create a generic scene
            scene = {
                "text": f"Scene {scene_idx + 1}",
                "scene_prompt": (
                    f"{visual_style} {genre} music video scene with {character_desc} in " +
                    f"{setting_desc}, continuing the visual narrative."
                ),
                "timestamp": scene_idx * 15,
                "section_type": "extra",
                "narrative_beat": random.choice(beats),
                "scene_number": scene_idx + 1,
                "story_elements": {
                    "character": character_desc,
                    "setting": setting_desc,
                    "visual_style": visual_style,
                    "genre": genre
                }
            }
            
            scenes.append(scene)
        
        return scenes
    
    def _generate_default_scenes(self) -> List[Dict[str, Any]]:
        """Generate default scenes when no lyrics are available."""
        # Create a simple story with random elements
        character = random.choice([
            "a mysterious figure in silhouette",
            "a young dreamer with hopeful eyes",
            "a contemplative person gazing into the distance",
            "a traveler on a meaningful journey",
            "an expressive dancer in motion"
        ])
        
        setting = random.choice([
            "a dramatic urban landscape with dynamic lighting",
            "a serene natural environment with atmospheric conditions",
            "an abstract space with symbolic visual elements",
            "a road stretching toward the horizon, suggesting journey",
            "a transforming environment that shifts with the music"
        ])
        
        visual_style = random.choice(self.visual_styles)
        genre = random.choice(self.genres)
        
        default_scenes = [
            {
                "text": "Scene 1",
                "scene_prompt": f"{visual_style} {genre} music video opening scene introducing {character} in {setting}",
                "timestamp": 0,
                "section_type": "intro",
                "narrative_beat": "Establishing the mood and setting",
                "scene_number": 1,
                "story_elements": {
                    "character": character,
                    "setting": setting,
                    "visual_style": visual_style,
                    "genre": genre
                }
            },
            {
                "text": "Scene 2",
                "scene_prompt": f"{visual_style} {genre} music video scene showing {character} exploring or interacting with {setting}",
                "timestamp": 15,
                "section_type": "verse",
                "narrative_beat": "Developing the visual narrative",
                "scene_number": 2,
                "story_elements": {
                    "character": character,
                    "setting": setting,
                    "visual_style": visual_style,
                    "genre": genre
                }
            },
            {
                "text": "Scene 3",
                "scene_prompt": f"{visual_style} {genre} music video emotional climax with {character} experiencing a revelation or transformation in {setting}",
                "timestamp": 30,
                "section_type": "chorus",
                "narrative_beat": "Reaching an emotional peak",
                "scene_number": 3,
                "story_elements": {
                    "character": character,
                    "setting": setting,
                    "visual_style": visual_style,
                    "genre": genre
                }
            },
            {
                "text": "Scene 4",
                "scene_prompt": f"{visual_style} {genre} music video final scene with {character} in {setting}, bringing resolution to the visual story",
                "timestamp": 45,
                "section_type": "outro",
                "narrative_beat": "Providing visual resolution",
                "scene_number": 4,
                "story_elements": {
                    "character": character,
                    "setting": setting,
                    "visual_style": visual_style,
                    "genre": genre
                }
            }
        ]
        
        return default_scenes

    def get_story_summary(self, lyrics: str) -> str:
        """
        Get a text summary of the story derived from lyrics.
        
        Args:
            lyrics: The raw lyrics text
            
        Returns:
            Formatted string with story summary
        """
        story = self.create_story(lyrics)
        
        summary = f"# Music Video Story Treatment\n\n"
        summary += f"## Genre & Style\n"
        summary += f"**Genre:** {story['genre'].title()}\n"
        summary += f"**Visual Style:** {story['visual_style'].title()}\n\n"
        
        summary += f"## Main Character\n"
        summary += f"{story['character']['description']}\n\n"
        
        summary += f"## Setting\n"
        summary += f"{story['setting']['description']}\n\n"
        
        summary += f"## Synopsis\n"
        summary += f"{story['narrative_arc']['synopsis']}\n\n"
        
        summary += f"## Story Beats\n"
        for i, beat in enumerate(story['narrative_arc']['beats']):
            summary += f"{i+1}. {beat}\n"
        
        return summary


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

[Verse 2]
Memories of yesterday
Slowly start to fade away
New beginnings taking form
After weathering the storm

[Chorus]
In the darkness I can see
All the things that call to me
Whispers from another time
Echoes in this heart of mine

[Bridge]
Between what was and what will be
There's just this moment, just for me
A chance to choose a different path
To find the peace that always lasts

[Chorus]
In the darkness I can see
All the things that call to me
Whispers from another time
Echoes in this heart of mine
"""

    # Initialize the director
    director = AIDirector()
    
    # Generate scenes
    scenes = director.generate_scenes_from_lyrics(sample_lyrics)
    
    # Get story summary
    summary = director.get_story_summary(sample_lyrics)
    
    # Print the results
    print(summary)
    print("\nGENERATED SCENES:")
    for i, scene in enumerate(scenes):
        print(f"\nSCENE {i+1}:")
        print(f"Section: {scene['section_type']}")
        print(f"Text: {scene['text']}")
        print(f"Prompt: {scene['scene_prompt']}")
        print(f"Timestamp: {scene['timestamp']}s")
