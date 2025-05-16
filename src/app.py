"""
MaiVid Studio - Main application

This is the main Flask application for MaiVid Studio,
handling routing, API endpoints, and frontend rendering.
"""

import os
import sys
import json
import logging
import uuid
import random
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path

# Flask imports
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory

# Initialize logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to load dotenv package
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv package not found, loading .env manually")
    # Simple manual dotenv loader for fallback
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'), 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    except Exception as e:
        logger.error(f"Error loading .env file manually: {str(e)}")

# Import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from src.backend.audio.processor import download_from_url, extract_lyrics, clean_lyrics
    from src.backend.comfyui.interface import ComfyUIInterface
    from src.backend.comfyui.fast_renderer import FastRenderer
    from src.backend.firebase.manager import FirebaseManager
    from src.backend.video.processor import VideoProcessor
    from src.backend.video.progress_tracker import progress_tracker
    from src.backend.generation.music_video_generator import generate_music_video_from_url, MusicVideoGenerator
    from src.backend.generation.video_generator import VideoGenerator
except ImportError:
    try:
        # Alternative import path
        from backend.audio.processor import download_from_url, extract_lyrics, clean_lyrics
        from backend.comfyui.interface import ComfyUIInterface
        from backend.comfyui.fast_renderer import FastRenderer
        from backend.firebase.manager import FirebaseManager
        from backend.video.processor import VideoProcessor
        from backend.video.progress_tracker import progress_tracker
        from backend.generation.music_video_generator import generate_music_video_from_url, MusicVideoGenerator
        from backend.generation.video_generator import VideoGenerator
    except ImportError as e:
        logger.error(f"Failed to import modules: {str(e)}")
        raise

# Set the correct paths relative to this file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'src', 'frontend', 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'src', 'frontend', 'static')

# Create Flask app
app = Flask(__name__, 
            template_folder=TEMPLATE_DIR,
            static_folder=STATIC_DIR)

# Configure app
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['ALLOWED_EXTENSIONS'] = {'mp3', 'wav', 'ogg', 'jpg', 'jpeg', 'png'}
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload size
app.config['DEBUG'] = True

# Enable CORS to prevent connection reset issues
@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize components
comfyui = ComfyUIInterface(os.getenv('COMFYUI_URL', 'http://127.0.0.1:8188'))
fast_renderer = FastRenderer(comfyui_interface=comfyui)
music_video_generator = MusicVideoGenerator(comfyui_url=os.getenv('COMFYUI_URL', 'http://127.0.0.1:8188'))
video_generator = VideoGenerator(
    comfyui_url=os.getenv('COMFYUI_URL', 'http://127.0.0.1:8188'),
    ffmpeg_path=os.getenv('FFMPEG_PATH', 'ffmpeg'),
    output_dir=os.path.join(BASE_DIR, app.config['OUTPUT_FOLDER']),
    upload_dir=os.path.join(BASE_DIR, app.config['UPLOAD_FOLDER'])
)
firebase = FirebaseManager(
    credentials_path=os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH'),
    storage_bucket=os.getenv('FIREBASE_STORAGE_BUCKET'),
    project_id=os.getenv('FIREBASE_PROJECT_ID')
)
video_processor = VideoProcessor(ffmpeg_path=os.getenv('FFMPEG_PATH', 'ffmpeg'))

# Create required directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['OUTPUT_FOLDER'], 'scenes'), exist_ok=True)
os.makedirs(os.path.join(app.config['OUTPUT_FOLDER'], 'scenes', 'temp'), exist_ok=True)
os.makedirs(os.path.join(app.config['OUTPUT_FOLDER'], 'scenes', 'fast_render'), exist_ok=True)
os.makedirs(os.path.join(app.config['OUTPUT_FOLDER'], 'videos'), exist_ok=True)
os.makedirs(os.path.join(app.config['OUTPUT_FOLDER'], 'videos', 'temp'), exist_ok=True)
os.makedirs(os.path.join(app.config['OUTPUT_FOLDER'], 'progress'), exist_ok=True)

# Make instances available to blueprint modules
app.fast_renderer = fast_renderer
app.music_video_generator = music_video_generator
app.video_generator = video_generator
app.BASE_DIR = BASE_DIR

# Register API blueprints
try:
    from src.backend.api.register import register_blueprints
    register_blueprints(app)
except ImportError as e:
    logger.error(f"Failed to import blueprints: {str(e)}")
    pass


def allowed_file(filename: str) -> bool:
    """Check if a file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    """Render the homepage."""
    return render_template('index.html')


@app.route('/login')
def login():
    """Render the login page."""
    return render_template('login.html')


@app.route('/register')
def register():
    """Render the registration page."""
    return render_template('register.html')


@app.route('/profile')
def profile():
    """Render the user profile page."""
    return render_template('profile.html')


@app.route('/projects')
def projects():
    """Render the projects page."""
    return render_template('projects.html')


@app.route('/concept')
def concept():
    """Render the concept development page."""
    return render_template('concept.html')


@app.route('/storyline')
def storyline():
    """Render the storyline creation page."""
    return render_template('storyline.html')


@app.route('/settings')
def settings():
    """Render the settings and cast page."""
    return render_template('settings.html')


@app.route('/scenes')
def scenes():
    """Render the scene breakdown page."""
    return render_template('scenes.html')


@app.route('/storyboard')
def storyboard():
    """Render the storyboard creation page."""
    return render_template('storyboard.html')


@app.route('/timeline')
def timeline():
    """Render the timeline editing page."""
    return render_template('timeline.html')


@app.route('/motion')
def motion():
    """Render the motion editing page."""
    return render_template('motion.html')


@app.route('/fast_render')
def fast_render():
    """Render the fast renderer page."""
    return render_template('fast_render.html')


@app.route('/api/music/download', methods=['POST'])
def download_music():
    """API endpoint to download music from a URL."""
    try:
        # Get URL from request
        data = None
        if request.is_json:
            data = request.get_json()
        else:
            # Handle form data if not JSON
            data = request.form.to_dict()
            
        if not data:
            logger.error("No data in request")
            return jsonify({'error': 'Invalid request format'}), 400
            
        url = data.get('url')
        if not url:
            logger.error("No URL provided in request")
            return jsonify({'error': 'No URL provided'}), 400
        
        # Log the request
        logger.info(f"Downloading music from URL: {url}")
        
        # Download the music
        file_path, error, metadata = download_from_url(url, app.config['UPLOAD_FOLDER'])
        
        if error:
            logger.error(f"Download failed: {error}")
            return jsonify({'error': error}), 400
        
        # Extract lyrics if file was downloaded
        lyrics, lyrics_error = extract_lyrics(file_path)
        cleaned_lyrics = clean_lyrics(lyrics) if lyrics else ""
        
        # Return success response
        response = {
            'file_path': file_path,
            'metadata': metadata,
            'lyrics': cleaned_lyrics
        }
        
        if lyrics_error:
            response['error_lyrics'] = lyrics_error
            
        logger.info(f"Download successful: {file_path}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error downloading music: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/video/progress/<job_id>', methods=['GET'])
def get_video_progress(job_id):
    """API endpoint to get the progress of a video rendering job."""
    try:
        # Get progress from tracker
        progress = progress_tracker.get_progress(job_id)
        
        if not progress:
            return jsonify({'error': 'Job not found'}), 404
        
        # Return progress data
        return jsonify(progress), 200
        
    except Exception as e:
        logger.error(f"Error getting video progress: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/video/progress', methods=['GET'])
def get_all_video_progress():
    """API endpoint to get the progress of all video rendering jobs."""
    try:
        # Get all jobs
        jobs = progress_tracker.get_all_jobs()
        
        # Return job data
        return jsonify({
            'jobs': jobs,
            'count': len(jobs)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting all video progress: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/video/create_from_url', methods=['POST'])
def create_video_from_url():
    """API endpoint to create a video directly from a music URL."""
    try:
        # Get data from request
        data = None
        if request.is_json:
            data = request.get_json()
        else:
            # Handle form data if not JSON
            data = request.form.to_dict()
            
        if not data:
            logger.error("No data in request")
            return jsonify({'error': 'Invalid request format'}), 400
            
        url = data.get('url')
        if not url:
            logger.error("No URL provided in request")
            return jsonify({'error': 'No URL provided'}), 400
        
        # Get optional parameters with defaults
        model_type = data.get('model_type', 'sdxl_turbo')
        aspect_ratio = data.get('aspect_ratio', '16:9')
        style = data.get('style', 'cinematic')
        scene_count = int(data.get('scene_count')) if data.get('scene_count') else None
        transition_type = data.get('transition_type', 'fade')
        transition_duration = float(data.get('transition_duration', 1.0))
        
        # Create video using the video generator
        job_id, job_info = video_generator.generate_from_url(
            url=url,
            model_type=model_type,
            aspect_ratio=aspect_ratio,
            style=style,
            scene_count=scene_count,
            transition_type=transition_type,
            transition_duration=transition_duration
        )
        
        # Return job info with 202 Accepted status
        logger.info(f"Started video generation from URL job: {job_id}")
        return jsonify(job_info), 202
        
    except Exception as e:
        logger.error(f"Error creating video from URL: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/concept/generate', methods=['POST'])
def generate_concept():
    """API endpoint to generate a video concept based on lyrics."""
    try:
        # Get data from request
        data = request.get_json()
        lyrics = data.get('lyrics')
        style = data.get('style', 'cinematic')
        mood = data.get('mood', 'reflective')
        
        if not lyrics:
            return jsonify({'error': 'No lyrics provided'}), 400
        
        # For MVP, we'll create a basic concept based on lyrics and selected style
        logger.info(f"Generating concept with style: {style}, mood: {mood}")
        
        # Extract key phrases from lyrics (simplified version)
        lines = lyrics.strip().split('\n')
        key_phrases = [line for line in lines if len(line.split()) >= 3][:3]
        if not key_phrases:
            key_phrases = ["emotional journey", "visual storytelling", "musical expression"]
        
        # Generate visual elements based on style
        visual_elements = []
        if style == 'cinematic':
            visual_elements = ["Dramatic landscapes", "Character close-ups", "Atmospheric lighting"]
        elif style == 'animated':
            visual_elements = ["Stylized characters", "Vibrant colors", "Dynamic movements"]
        elif style == 'abstract':
            visual_elements = ["Geometric shapes", "Color gradients", "Symbolic imagery"]
        elif style == 'documentary':
            visual_elements = ["Real-world settings", "Natural lighting", "Authentic moments"]
        elif style == 'noir':
            visual_elements = ["Shadows and contrast", "Urban settings", "Moody atmosphere"]
        else:
            visual_elements = ["Evocative imagery", "Visual metaphors", "Scene transitions"]
        
        # Generate color palette based on mood
        color_palette = []
        if mood == 'upbeat':
            color_palette = ["#FF5E5B", "#FFED66", "#00CECB", "#FFAAAA"]
        elif mood == 'reflective':
            color_palette = ["#1A2A3A", "#4B5A6A", "#7C8A9A", "#ACBACA"]
        elif mood == 'melancholic':
            color_palette = ["#2E294E", "#541388", "#F1E9DA", "#FFD400"]
        elif mood == 'intense':
            color_palette = ["#D00000", "#DC2F02", "#F48C06", "#FFBA08"]
        elif mood == 'dreamy':
            color_palette = ["#CDB4DB", "#FFC8DD", "#FFAFCC", "#BDE0FE"]
        else:
            color_palette = ["#264653", "#2A9D8F", "#E9C46A", "#F4A261"]
        
        # Create the concept
        concept = {
            "title": f"{style.capitalize()} {mood.capitalize()} Music Video",
            "description": f"A {mood} journey through {style} visuals that capture the essence of the lyrics, creating an immersive audiovisual experience.",
            "style": style,
            "themes": key_phrases,
            "color_palette": color_palette,
            "mood": mood,
            "visual_elements": visual_elements
        }
        
        logger.info(f"Generated concept: {concept['title']}")
        return jsonify(concept), 200
        
    except Exception as e:
        logger.error(f"Error generating concept: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/storyline/generate', methods=['POST'])
def generate_storyline():
    """API endpoint to generate a storyline based on concept and lyrics."""
    try:
        # Get data from request
        data = request.get_json()
        concept = data.get('concept')
        lyrics = data.get('lyrics')
        structure = data.get('structure', 'linear')
        focus = data.get('focus', 'emotion')
        notes = data.get('notes', '')
        
        if not concept or not lyrics:
            return jsonify({'error': 'Concept and lyrics are required'}), 400
        
        logger.info(f"Generating storyline with structure: {structure}, focus: {focus}")
        
        # Split lyrics into segments for scenes
        lines = lyrics.strip().split('\n')
        
        # Remove empty lines
        lines = [line for line in lines if line.strip()]
        
        # Create segments based on structure
        segments = []
        if structure == 'linear':
            # Linear structure - beginning, middle, end
            if len(lines) >= 4:
                # Divide lines into 4 segments
                segment_size = len(lines) // 4
                segments = [
                    '\n'.join(lines[:segment_size]),
                    '\n'.join(lines[segment_size:segment_size*2]),
                    '\n'.join(lines[segment_size*2:segment_size*3]),
                    '\n'.join(lines[segment_size*3:])
                ]
            else:
                # Not enough lines, use what we have
                segments = lines + [''] * (4 - len(lines))
        elif structure == 'circular':
            # Circular structure - end similar to beginning
            if len(lines) >= 4:
                segments = [
                    lines[0],
                    '\n'.join(lines[1:len(lines)//2]),
                    '\n'.join(lines[len(lines)//2:-1]),
                    lines[-1] if lines[-1] != lines[0] else "Return to the beginning"
                ]
            else:
                segments = lines + [''] * (4 - len(lines))
        elif structure == 'non-linear':
            # Non-linear - fragmented scenes
            indices = list(range(len(lines)))
            random.shuffle(indices)
            segments = [
                '\n'.join([lines[i] for i in indices[:len(indices)//4]]),
                '\n'.join([lines[i] for i in indices[len(indices)//4:len(indices)//2]]),
                '\n'.join([lines[i] for i in indices[len(indices)//2:3*len(indices)//4]]),
                '\n'.join([lines[i] for i in indices[3*len(indices)//4:]])
            ]
        else:
            # Default to simple segments
            if len(lines) >= 4:
                segment_size = len(lines) // 4
                segments = [
                    '\n'.join(lines[:segment_size]),
                    '\n'.join(lines[segment_size:segment_size*2]),
                    '\n'.join(lines[segment_size*2:segment_size*3]),
                    '\n'.join(lines[segment_size*3:])
                ]
            else:
                segments = lines + [''] * (4 - len(lines))
        
        # Generate scene descriptions based on focus and concept
        scenes = []
        mood_progression = ["opening", "building", "climax", "resolution"]
        
        for i in range(4):
            scene_id = f"scene{i+1}"
            scene_focus = focus
            scene_lyrics = segments[i] if i < len(segments) else ""
            
            # Generate description based on focus
            if focus == 'character':
                if i == 0:
                    description = f"Introducing the protagonist in a {concept['style']} setting, establishing their character."
                elif i == 1:
                    description = f"The protagonist faces challenges in an environment reflecting {concept['mood']} emotions."
                elif i == 2:
                    description = f"The protagonist reaches a pivotal moment, with {concept['visual_elements'][0]} emphasizing the emotional intensity."
                else:
                    description = f"The protagonist finds resolution, with visuals showing {concept['visual_elements'][1]} to signify growth."
            elif focus == 'emotion':
                if i == 0:
                    description = f"Opening with {concept['visual_elements'][0]} to establish a {concept['mood']} atmosphere."
                elif i == 1:
                    description = f"Transitioning to scenes with {concept['visual_elements'][1]}, building emotional intensity."
                elif i == 2:
                    description = f"Reaching emotional peak with dramatic visuals featuring {concept['visual_elements'][2]}."
                else:
                    description = f"Concluding with visuals that express emotional resolution through {concept['style']} imagery."
            elif focus == 'symbolic':
                if i == 0:
                    description = f"Opening with symbolic imagery of {concept['themes'][0] if i < len(concept['themes']) else 'beginnings'}."
                elif i == 1:
                    description = f"Developing symbolism related to {concept['themes'][1] if 1 < len(concept['themes']) else 'challenges'}."
                elif i == 2:
                    description = f"Symbolic climax representing {concept['themes'][2] if 2 < len(concept['themes']) else 'transformation'}."
                else:
                    description = f"Concluding with symbolic imagery of {concept['themes'][0] if i < len(concept['themes']) else 'resolution'}."
            else:
                # Default to visual-driven
                if i == 0:
                    description = f"Opening with a {concept['style']} visual sequence featuring {concept['visual_elements'][0] if i < len(concept['visual_elements']) else 'establishing shots'}."
                elif i == 1:
                    description = f"Transitioning to scenes with {concept['visual_elements'][1] if 1 < len(concept['visual_elements']) else 'dynamic visuals'}."
                elif i == 2:
                    description = f"Visual climax with striking {concept['style']} imagery."
                else:
                    description = f"Concluding visuals that tie back to the {concept['mood']} theme of the music."
            
            # Calculate approximate timing
            start_time = i * 30
            end_time = (i + 1) * 30
            timing = f"{start_time//60}:{start_time%60:02d}-{end_time//60}:{end_time%60:02d}"
            
            # Create scene
            scenes.append({
                "id": scene_id,
                "description": description,
                "timing": timing,
                "lyrics_segment": scene_lyrics,
                "mood": mood_progression[i]
            })
        
        # Create a narrative description
        narrative = f"A {structure} narrative with a {focus}-driven approach, showcasing {concept['style']} visuals that capture the {concept['mood']} essence of the music."
        
        # Incorporate user notes if provided
        if notes:
            narrative += f" Special emphasis on: {notes}"
        
        # Create character arcs based on focus
        character_arcs = []
        if focus == 'character':
            character_arcs.append({
                "character": "Protagonist",
                "arc": "Begins in contemplation, faces challenges, overcomes obstacles, achieves resolution"
            })
        elif focus == 'emotion':
            character_arcs.append({
                "character": "Emotional Journey",
                "arc": f"Progression from {mood_progression[0]} to {mood_progression[-1]} through visual storytelling"
            })
        
        # Create the storyline
        storyline = {
            "narrative": narrative,
            "scenes": scenes,
            "character_arcs": character_arcs
        }
        
        logger.info(f"Generated storyline with {len(scenes)} scenes")
        return jsonify(storyline), 200
        
    except Exception as e:
        logger.error(f"Error generating storyline: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/scene/generate', methods=['POST'])
def generate_scene():
    """API endpoint to generate a scene image based on description."""
    try:
        # Get data from request
        data = request.get_json()
        scene_description = data.get('description')
        style = data.get('style', 'cinematic')
        
        if not scene_description:
            return jsonify({'error': 'No scene description provided'}), 400
        
        # This would call ComfyUI to generate the image
        # For demonstration, we'll assume it works
        
        # In a real implementation, you would call:
        # image_path, error = comfyui.generate_scene(
        #     workflow_file="workflows/scene_generation.json",
        #     scene_description=scene_description,
        #     style=style,
        #     output_dir=os.path.join(app.config['OUTPUT_FOLDER'], 'scenes')
        # )
        
        # For now, return a placeholder path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_filename = f"scene_{timestamp}.png"
        image_path = os.path.join(app.config['OUTPUT_FOLDER'], 'scenes', image_filename)
        
        # In a real scenario, ComfyUI would have generated this file
        # For demo purposes, assume it exists
        
        scene_data = {
            "id": str(uuid.uuid4()),
            "description": scene_description,
            "style": style,
            "image_path": image_path,
            "image_url": f"/outputs/scenes/{image_filename}"
        }
        
        return jsonify(scene_data), 200
        
    except Exception as e:
        logger.error(f"Error generating scene: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/video/create', methods=['POST'])
def create_video():
    """API endpoint to create a video from scenes and audio."""
    try:
        # Get data from request
        data = request.get_json()
        scenes = data.get('scenes')
        audio_path = data.get('audio_path')
        video_title = data.get('video_title', 'Music Video')
        resolution = data.get('resolution', '720p')
        format = data.get('format', 'mp4')
        transition_type = data.get('transition_type', 'fade')
        transition_duration = float(data.get('transition_duration', 1.0))
        
        if not scenes or not audio_path:
            return jsonify({'error': 'Scenes and audio path are required'}), 400
        
        # Convert from relative path to absolute path if needed
        if not os.path.isabs(audio_path):
            # Relative path from app root
            if audio_path.startswith('uploads/'):
                audio_path = os.path.join(BASE_DIR, audio_path)
            # Path with just filename
            else:
                audio_path = os.path.join(BASE_DIR, 'uploads', audio_path)
        
        # Check if the audio file exists
        if not os.path.exists(audio_path):
            return jsonify({'error': f'Audio file not found: {audio_path}'}), 400
        
        # Generate a unique output filename and job ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_title = ''.join(c for c in video_title if c.isalnum() or c in ' .-_').replace(' ', '_')
        output_filename = f"{sanitized_title}_{timestamp}.{format}"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], 'videos', output_filename)
        
        # Generate a unique job ID and create tracking job
        job_id = f"job_{timestamp}_{uuid.uuid4().hex[:8]}"
        progress_tracker.create_job(job_id, len(scenes), video_title)
        
        # Create the output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Prepare the scene data for video processing
        processed_scenes = []
        
        for scene in scenes:
            # Get the scene image path
            image_path = scene.get('image_path')
            
            # If no direct image path, try to find it from the scene_id
            if not image_path and scene.get('scene_id'):
                # Find the scene in the database or previous API calls
                try:
                    # Try to find in other scenes that might be in the request
                    for s in data.get('all_scenes', []):
                        if s.get('id') == scene.get('scene_id'):
                            image_path = s.get('image_path')
                            break
                except Exception as scene_error:
                    logger.warning(f"Error finding scene: {str(scene_error)}")
                    pass
            
            # If still no image path, try using the image_url
            if not image_path and scene.get('image_url'):
                image_url = scene.get('image_url')
                if image_url.startswith('/outputs/'):
                    # Convert relative URL to file path
                    rel_path = image_url[1:]  # Remove leading slash
                    image_path = os.path.join(BASE_DIR, rel_path)
            
            # Skip if we still can't find an image path
            if not image_path or not os.path.exists(image_path):
                logger.warning(f"Skipping scene, image not found: {scene}")
                continue
            
            # Add to processed scenes
            processed_scenes.append({
                'id': scene.get('id'),
                'image_path': image_path,
                'duration': float(scene.get('duration', 3.0)),
                'motion_type': scene.get('motion', 'zoom'),
                'zoom_factor': float(scene.get('zoom_factor', 1.2)),
                'pan_x': float(scene.get('pan_x', 0)),
                'pan_y': float(scene.get('pan_y', 0))
            })
        
        if not processed_scenes:
            return jsonify({'error': 'No valid scenes found with images'}), 400
        
        # Set video resolution
        if resolution == '1080p':
            output_width, output_height = 1920, 1080
        elif resolution == '720p':
            output_width, output_height = 1280, 720
        elif resolution == '480p':
            output_width, output_height = 854, 480
        else:
            output_width, output_height = 1280, 720  # Default to 720p
        
        # Log the scenes and settings
        logger.info(f"Creating video with {len(processed_scenes)} scenes, transition: {transition_type}")
        logger.info(f"Resolution: {resolution} ({output_width}x{output_height}), Format: {format}")
        
        # Start the video creation process in a background thread
        def create_video_job():
            try:
                # Process each scene with progress tracking
                scene_videos = []
                
                # Step 1: Create individual scene videos
                for i, scene in enumerate(processed_scenes):
                    try:
                        scene_output_dir = os.path.join(app.config['OUTPUT_FOLDER'], 'scenes', 'temp', job_id)
                        os.makedirs(scene_output_dir, exist_ok=True)
                        
                        # Create scene video
                        scene_output, error = video_processor.create_scene_video(
                            scene_data=scene,
                            output_dir=scene_output_dir,
                            base_filename=f"scene_{i}"
                        )
                        
                        if error:
                            progress_tracker.fail_job(job_id, f"Error creating scene {i}: {error}")
                            return False
                        
                        scene_videos.append(scene_output)
                        
                        # Update progress
                        progress_tracker.update_scene_progress(job_id, i, scene.get('id', ''))
                        
                    except Exception as e:
                        progress_tracker.fail_job(job_id, f"Error processing scene {i}: {str(e)}")
                        logger.error(f"Error processing scene {i}: {str(e)}")
                        return False
                
                # Step 2: Combine scene videos with transitions
                try:
                    video_without_audio = os.path.join(app.config['OUTPUT_FOLDER'], 'videos', 'temp', f"{job_id}_no_audio.mp4")
                    os.makedirs(os.path.dirname(video_without_audio), exist_ok=True)
                    
                    # Number of transitions is scenes - 1
                    num_transitions = len(scene_videos) - 1
                    
                    # Combine videos
                    success, error = video_processor.combine_videos_with_transitions(
                        video_paths=scene_videos,
                        output_path=video_without_audio,
                        transition_type=transition_type,
                        transition_duration=transition_duration
                    )
                    
                    if not success:
                        progress_tracker.fail_job(job_id, f"Error combining scenes: {error}")
                        return False
                    
                    # Update progress to 75%
                    progress_tracker.update_transition_progress(job_id, num_transitions, num_transitions)
                    
                except Exception as e:
                    progress_tracker.fail_job(job_id, f"Error combining scenes: {str(e)}")
                    logger.error(f"Error combining scenes: {str(e)}")
                    return False
                
                # Step 3: Add audio to the video
                try:
                    # Add audio
                    success, error = video_processor.add_audio(
                        video_path=video_without_audio,
                        audio_path=audio_path,
                        output_path=output_path,
                        normalize_audio=True
                    )
                    
                    if not success:
                        progress_tracker.fail_job(job_id, f"Error adding audio: {error}")
                        return False
                    
                    # Update progress to 100%
                    progress_tracker.update_audio_progress(job_id, 100)
                    
                    # Mark job as complete
                    progress_tracker.complete_job(job_id, output_path)
                    
                    # Clean up temporary files
                    try:
                        import shutil
                        shutil.rmtree(os.path.join(app.config['OUTPUT_FOLDER'], 'scenes', 'temp', job_id), ignore_errors=True)
                        os.remove(video_without_audio)
                    except Exception as cleanup_error:
                        logger.warning(f"Error cleaning up temp files: {str(cleanup_error)}")
                    
                    return True
                    
                except Exception as e:
                    progress_tracker.fail_job(job_id, f"Error adding audio: {str(e)}")
                    logger.error(f"Error adding audio: {str(e)}")
                    return False
                    
            except Exception as e:
                progress_tracker.fail_job(job_id, f"Unexpected error: {str(e)}")
                logger.error(f"Unexpected error in video creation: {str(e)}")
                return False
        
        # Start the video creation process in a background thread
        threading.Thread(target=create_video_job).start()
        
        # Return immediately with the job ID for tracking
        initial_progress = progress_tracker.get_progress(job_id)
        
        # Log job started
        logger.info(f"Started video creation job: {job_id} for {output_path}")
        
        # Return the job information for tracking
        return jsonify({
            'job_id': job_id,
            'video_title': video_title,
            'scenes_count': len(processed_scenes),
            'expected_duration': sum(scene.get('duration', 3.0) for scene in processed_scenes),
            'status': 'processing',
            'progress': initial_progress,
            'expected_output': f"/outputs/videos/{output_filename}",
            'format': format,
            'resolution': resolution
        }), 202  # 202 Accepted indicates the request is being processed
        
    except Exception as e:
        logger.error(f"Error creating video: {str(e)}")
        return jsonify({'error': str(e)}), 500


# Firebase Authentication API Endpoints
@app.route('/api/auth/user', methods=['GET'])
def get_current_user():
    """Get the currently authenticated user."""
    try:
        # Get the auth token from request
        auth_token = request.headers.get('Authorization')
        if not auth_token or not auth_token.startswith('Bearer '):
            return jsonify({'error': 'No valid token provided'}), 401
        
        token = auth_token.split('Bearer ')[1]
        
        # Verify the token with Firebase
        user_data, error = firebase.verify_id_token(token)
        
        if error:
            return jsonify({'error': error}), 401
        
        return jsonify(user_data), 200
        
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects', methods=['GET'])
def get_user_projects():
    """Get projects for the authenticated user."""
    try:
        # Get the auth token from request
        auth_token = request.headers.get('Authorization')
        if not auth_token or not auth_token.startswith('Bearer '):
            return jsonify({'error': 'No valid token provided'}), 401
        
        token = auth_token.split('Bearer ')[1]
        
        # Verify the token with Firebase
        user_data, error = firebase.verify_id_token(token)
        
        if error:
            return jsonify({'error': error}), 401
        
        # Get projects for this user
        projects, error = firebase.query_collection(
            collection='projects',
            field='userId',
            operator='==',
            value=user_data['uid']
        )
        
        if error:
            return jsonify({'error': error}), 500
        
        return jsonify(projects), 200
        
    except Exception as e:
        logger.error(f"Error getting projects: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get a specific project."""
    try:
        # Get the auth token from request
        auth_token = request.headers.get('Authorization')
        if not auth_token or not auth_token.startswith('Bearer '):
            return jsonify({'error': 'No valid token provided'}), 401
        
        token = auth_token.split('Bearer ')[1]
        
        # Verify the token with Firebase
        user_data, error = firebase.verify_id_token(token)
        
        if error:
            return jsonify({'error': error}), 401
        
        # Get the project
        project, error = firebase.get_document(
            collection='projects',
            document_id=project_id
        )
        
        if error:
            return jsonify({'error': error}), 500
        
        # Check if user has access to this project
        if project['userId'] != user_data['uid']:
            return jsonify({'error': 'You do not have access to this project'}), 403
        
        return jsonify(project), 200
        
    except Exception as e:
        logger.error(f"Error getting project: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project."""
    try:
        # Get the auth token from request
        auth_token = request.headers.get('Authorization')
        if not auth_token or not auth_token.startswith('Bearer '):
            return jsonify({'error': 'No valid token provided'}), 401
        
        token = auth_token.split('Bearer ')[1]
        
        # Verify the token with Firebase
        user_data, error = firebase.verify_id_token(token)
        
        if error:
            return jsonify({'error': error}), 401
        
        # Get data from request
        data = request.get_json()
        
        # Add user ID and timestamps
        data['userId'] = user_data['uid']
        data['createdAt'] = {'__type': 'serverTimestamp'}
        data['updatedAt'] = {'__type': 'serverTimestamp'}
        
        # Create project in Firestore
        project_id = str(uuid.uuid4())
        success, error = firebase.set_document(
            collection='projects',
            document_id=project_id,
            data=data
        )
        
        if error:
            return jsonify({'error': error}), 500
        
        return jsonify({'id': project_id}), 201
        
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/outputs/<path:filename>')
def output_file(filename):
    """Serve output files."""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)


if __name__ == '__main__':
    # Start the Flask application
    app.run(host='0.0.0.0', port=420, debug=True)