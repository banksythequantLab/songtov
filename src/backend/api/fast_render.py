"""
MaiVid Studio - Fast Renderer Module API Endpoints
"""

import os
import sys
import json
import logging
import uuid
import threading
from datetime import datetime
from werkzeug.utils import secure_filename

from flask import Blueprint, request, jsonify, current_app
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set up the blueprint
fast_render_bp = Blueprint('fast_render', __name__)

# Expected global variables from app context:
# - fast_renderer: FastRenderer instance
# - music_video_generator: MusicVideoGenerator instance


@fast_render_bp.route('/api/fast_render/generate', methods=['POST'])
def fast_render_generate():
    """API endpoint to generate scenes using the fast renderer."""
    try:
        # Get data from request
        data = request.get_json()
        scene_description = data.get('description')
        model_type = data.get('model_type', 'sdxl_turbo')
        aspect_ratio = data.get('aspect_ratio', '16:9')
        style = data.get('style', 'cinematic')
        
        if not scene_description:
            return jsonify({'error': 'No scene description provided'}), 400
        
        # Get the fast renderer from the app context
        fast_renderer = current_app.fast_renderer
        
        # Generate the scene using fast renderer
        output_dir = os.path.join(current_app.config['OUTPUT_FOLDER'], 'scenes', 'fast_render')
        os.makedirs(output_dir, exist_ok=True)
        
        image_path, error = fast_renderer.generate_scene(
            scene_description=scene_description,
            model_type=model_type,
            aspect_ratio=aspect_ratio,
            style=style,
            output_dir=output_dir
        )
        
        if error:
            logger.error(f"Error generating scene: {error}")
            return jsonify({'error': error}), 500
        
        # Create relative paths for the frontend
        rel_path = os.path.relpath(image_path, os.path.join(current_app.config['BASE_DIR'], current_app.config['OUTPUT_FOLDER']))
        image_url = f"/outputs/{rel_path.replace(os.path.sep, '/')}"
        
        scene_data = {
            "id": str(uuid.uuid4()),
            "description": scene_description,
            "model_type": model_type,
            "aspect_ratio": aspect_ratio,
            "style": style,
            "image_path": image_path,
            "image_url": image_url
        }
        
        logger.info(f"Generated scene with fast renderer: {image_path}")
        return jsonify(scene_data), 200
        
    except Exception as e:
        logger.error(f"Error in fast render generation: {str(e)}")
        return jsonify({'error': str(e)}), 500


@fast_render_bp.route('/api/fast_render/music_video', methods=['POST'])
def fast_render_music_video():
    """API endpoint to generate a complete music video from a Suno URL."""
    try:
        # Get data from request
        data = request.get_json()
        suno_url = data.get('suno_url')
        model_type = data.get('model_type', 'sdxl_turbo')
        aspect_ratio = data.get('aspect_ratio', '16:9')
        scene_count = data.get('scene_count')
        style = data.get('style', 'cinematic')
        
        if not suno_url:
            return jsonify({'error': 'No Suno URL provided'}), 400
        
        # Parse scene count
        if scene_count and isinstance(scene_count, str):
            try:
                scene_count = int(scene_count)
            except ValueError:
                scene_count = None
        
        # Get the music video generator from the app context
        music_video_generator = current_app.music_video_generator
        
        # Generate output directory
        output_dir = os.path.join(current_app.config['OUTPUT_FOLDER'], 'videos')
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a job ID for tracking
        job_id = f"mvgen_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Create a background job
        def generate_music_video_job():
            try:
                # Generate the music video
                result = music_video_generator.generate_from_suno_url(
                    suno_url=suno_url,
                    output_dir=output_dir,
                    model_type=model_type,
                    aspect_ratio=aspect_ratio,
                    scene_count=scene_count,
                    style=style
                )
                
                # Save job result to file for retrieval
                job_result_path = os.path.join(current_app.config['OUTPUT_FOLDER'], 'progress', f"{job_id}.json")
                with open(job_result_path, 'w') as f:
                    json.dump(result, f, indent=2)
                
                logger.info(f"Music video generation completed for job {job_id}: {result.get('success')}")
                
            except Exception as e:
                logger.error(f"Error in music video generation job {job_id}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                
                # Save error to job result
                job_result_path = os.path.join(current_app.config['OUTPUT_FOLDER'], 'progress', f"{job_id}.json")
                with open(job_result_path, 'w') as f:
                    json.dump({
                        'success': False,
                        'error': str(e),
                        'job_id': job_id
                    }, f, indent=2)
        
        # Start the background job
        threading.Thread(target=generate_music_video_job).start()
        
        # Return the job ID for tracking
        return jsonify({
            'job_id': job_id,
            'status': 'processing',
            'message': 'Music video generation started',
            'params': {
                'suno_url': suno_url,
                'model_type': model_type,
                'aspect_ratio': aspect_ratio,
                'scene_count': scene_count,
                'style': style
            }
        }), 202  # 202 Accepted
        
    except Exception as e:
        logger.error(f"Error in music video generation: {str(e)}")
        return jsonify({'error': str(e)}), 500


@fast_render_bp.route('/api/fast_render/job/<job_id>', methods=['GET'])
def fast_render_job_status(job_id):
    """API endpoint to check the status of a music video generation job."""
    try:
        # Check if job result file exists
        job_result_path = os.path.join(current_app.config['OUTPUT_FOLDER'], 'progress', f"{job_id}.json")
        
        if os.path.exists(job_result_path):
            # Read the job result
            with open(job_result_path, 'r') as f:
                result = json.load(f)
            
            # Create relative paths for frontend
            if result.get('success') and result.get('scenes'):
                for scene in result.get('scenes', []):
                    if scene.get('image_path'):
                        try:
                            rel_path = os.path.relpath(scene['image_path'], current_app.config['BASE_DIR'])
                            scene['image_url'] = f"/{rel_path.replace(os.path.sep, '/')}"
                        except:
                            # Keep the original path if we can't make it relative
                            pass
            
            # Add job ID
            result['job_id'] = job_id
            
            return jsonify(result), 200
        else:
            # Job is still processing or does not exist
            return jsonify({
                'job_id': job_id,
                'status': 'processing',
                'message': 'Music video generation in progress'
            }), 200
        
    except Exception as e:
        logger.error(f"Error checking job status: {str(e)}")
        return jsonify({'error': str(e)}), 500


@fast_render_bp.route('/api/fast_render/models', methods=['GET'])
def list_fast_render_models():
    """API endpoint to list available fast render models."""
    try:
        models = [
            {
                "id": "sdxl_turbo",
                "name": "SDXL Turbo",
                "description": "Ultra-fast image generation (<1 second)",
                "speed": "Ultra Fast",
                "quality": "Good",
                "recommended_for": "Rapid prototyping and initial scene generation"
            },
            {
                "id": "sd3",
                "name": "SD 3",
                "description": "Higher quality with moderate speed",
                "speed": "Medium",
                "quality": "Excellent",
                "recommended_for": "Final scene generation and high-quality outputs"
            },
            {
                "id": "flux",
                "name": "Flux",
                "description": "Fast with unique visual characteristics",
                "speed": "Fast",
                "quality": "Very Good",
                "recommended_for": "Style-focused scene generation with good speed"
            }
        ]
        
        return jsonify(models), 200
        
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        return jsonify({'error': str(e)}), 500


def register_blueprint(app):
    """Register the blueprint with the app."""
    app.register_blueprint(fast_render_bp)
