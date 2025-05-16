"""
MaiVid Studio - API Blueprint for Convo Pilot Integration

This module registers API endpoints for the Convo Pilot integration.
It allows Convo Pilot to interact with MaiVid Studio for video generation.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from flask import Blueprint, request, jsonify, current_app, g

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create blueprint
convo_pilot_api = Blueprint('convo_pilot_api', __name__)


@convo_pilot_api.route('/api/convo_pilot/video', methods=['POST'])
def create_video_from_convo_pilot():
    """Create a video using Convo Pilot."""
    try:
        # Get data from request
        data = request.get_json()
        
        # Extract parameters
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        
        # Get optional parameters with defaults
        model_type = data.get('model_type', 'sdxl_turbo')
        aspect_ratio = data.get('aspect_ratio', '16:9')
        style = data.get('style', 'cinematic')
        scene_count = int(data.get('scene_count')) if data.get('scene_count') else None
        transition_type = data.get('transition_type', 'fade')
        transition_duration = float(data.get('transition_duration', 1.0))
        
        # Create video using the video generator
        job_id, job_info = current_app.video_generator.generate_from_url(
            url=url,
            model_type=model_type,
            aspect_ratio=aspect_ratio,
            style=style,
            scene_count=scene_count,
            transition_type=transition_type,
            transition_duration=transition_duration
        )
        
        # Return job info
        logger.info(f"Started video generation from Convo Pilot job: {job_id}")
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': f"Video generation started with job ID: {job_id}",
            'job_info': job_info
        }), 202
        
    except Exception as e:
        logger.error(f"Error creating video from Convo Pilot: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@convo_pilot_api.route('/api/convo_pilot/video/<job_id>', methods=['GET'])
def get_video_status(job_id):
    """Get the status of a video generation job."""
    try:
        # Get job status
        job_status = current_app.video_generator.get_job_status(job_id)
        
        if not job_status:
            return jsonify({
                'success': False,
                'error': f"Job {job_id} not found"
            }), 404
        
        # Return job status
        return jsonify({
            'success': True,
            'job_status': job_status
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting video status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@convo_pilot_api.route('/api/convo_pilot/video/progress/<job_id>', methods=['GET'])
def get_video_progress(job_id):
    """Get the progress of a video generation job."""
    try:
        # Get job progress
        progress = current_app.video_generator.get_job_status(job_id)
        
        if not progress:
            return jsonify({
                'success': False,
                'error': f"Job {job_id} not found"
            }), 404
        
        # Return progress
        return jsonify({
            'success': True,
            'progress': progress
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting video progress: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@convo_pilot_api.route('/api/convo_pilot/models', methods=['GET'])
def get_available_models():
    """Get available AI models for video generation."""
    try:
        # Return list of available models
        models = [
            {
                'id': 'sdxl_turbo',
                'name': 'SDXL Turbo',
                'description': 'Fast generation with good quality',
                'speed': 'Fast',
                'quality': 'Good'
            },
            {
                'id': 'sd3',
                'name': 'Stable Diffusion 3',
                'description': 'High quality generation, slower than Turbo',
                'speed': 'Medium',
                'quality': 'Excellent'
            },
            {
                'id': 'flux',
                'name': 'Flux',
                'description': 'Balanced speed and quality',
                'speed': 'Medium',
                'quality': 'Very Good'
            }
        ]
        
        return jsonify({
            'success': True,
            'models': models
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting available models: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@convo_pilot_api.route('/api/convo_pilot/styles', methods=['GET'])
def get_available_styles():
    """Get available video styles."""
    try:
        # Return list of available styles
        styles = [
            {
                'id': 'cinematic',
                'name': 'Cinematic',
                'description': 'Professional movie-like style with dramatic lighting'
            },
            {
                'id': 'anime',
                'name': 'Anime',
                'description': 'Japanese animation style'
            },
            {
                'id': 'photorealistic',
                'name': 'Photorealistic',
                'description': 'Realistic photography style'
            },
            {
                'id': 'cartoon',
                'name': 'Cartoon',
                'description': 'Colorful cartoon style'
            },
            {
                'id': 'abstract',
                'name': 'Abstract',
                'description': 'Non-representational artistic style'
            },
            {
                'id': 'noir',
                'name': 'Film Noir',
                'description': 'Black and white with dramatic shadows'
            },
            {
                'id': 'cyberpunk',
                'name': 'Cyberpunk',
                'description': 'Futuristic neon-lit urban style'
            },
            {
                'id': 'fantasy',
                'name': 'Fantasy',
                'description': 'Magical and otherworldly style'
            }
        ]
        
        return jsonify({
            'success': True,
            'styles': styles
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting available styles: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
