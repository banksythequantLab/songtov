"""
MaiVid Studio - AI Director Settings API Blueprint

This blueprint provides API endpoints for managing AI Director settings,
including the ability to switch between built-in models and Ollama.
"""

import os
import json
import logging
from flask import Blueprint, request, jsonify, current_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create blueprint
ai_settings_bp = Blueprint('ai_settings', __name__, url_prefix='/api/ai')

# Path to store settings
settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads', 'ai_settings.json')

# Default settings
default_settings = {
    "use_ollama": False,
    "ollama_model": "phi3:mini",
    "ollama_url": "http://localhost:11434"
}

# Helper function to load settings
def get_ai_settings():
    try:
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                return json.load(f)
        
        # Create default settings if file doesn't exist
        with open(settings_path, 'w') as f:
            json.dump(default_settings, f, indent=2)
        
        return default_settings
    except Exception as e:
        logger.error(f"Error loading AI settings: {str(e)}")
        return default_settings

# Helper function to save settings
def save_ai_settings(settings):
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=2)
        
        return True
    except Exception as e:
        logger.error(f"Error saving AI settings: {str(e)}")
        return False

@ai_settings_bp.route('/settings', methods=['GET'])
def get_settings():
    """Get current AI Director settings."""
    try:
        settings = get_ai_settings()
        return jsonify(settings), 200
    except Exception as e:
        logger.error(f"Error getting AI settings: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_settings_bp.route('/settings', methods=['POST'])
def update_settings():
    """Update AI Director settings."""
    try:
        settings = request.get_json()
        
        if not settings:
            return jsonify({'error': 'No settings provided'}), 400
        
        # Validate settings
        if 'use_ollama' not in settings:
            return jsonify({'error': 'Missing use_ollama parameter'}), 400
        
        # Get current settings
        current_settings = get_ai_settings()
        
        # Update settings
        current_settings.update(settings)
        
        # Save settings
        success = save_ai_settings(current_settings)
        
        if not success:
            return jsonify({'error': 'Failed to save settings'}), 500
        
        return jsonify(current_settings), 200
    except Exception as e:
        logger.error(f"Error updating AI settings: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_settings_bp.route('/ollama/status', methods=['GET'])
def check_ollama():
    """Check if Ollama is available and working."""
    try:
        # Import the OllamaConnector
        try:
            from backend.ai.local_models import OllamaConnector
        except ImportError:
            try:
                from src.backend.ai.local_models import OllamaConnector
            except ImportError:
                return jsonify({
                    'available': False,
                    'error': 'OllamaConnector module not found'
                }), 404
        
        # Get settings
        settings = get_ai_settings()
        
        # Create connector
        ollama = OllamaConnector(
            model_name=settings.get('ollama_model', 'phi3:mini'),
            api_base=settings.get('ollama_url', 'http://localhost:11434')
        )
        
        # Check availability
        available, error = ollama.check_availability()
        
        if available:
            # Generate a test response
            test_prompt = "What is a music video? (Answer in 20 words or less)"
            response, error = ollama.generate_text(test_prompt, max_tokens=50)
            
            if error:
                return jsonify({
                    'available': True,
                    'model': settings.get('ollama_model', 'phi3:mini'),
                    'status': 'connected',
                    'test_response': None,
                    'error': error
                }), 200
            
            return jsonify({
                'available': True,
                'model': settings.get('ollama_model', 'phi3:mini'),
                'status': 'connected',
                'test_response': response
            }), 200
        else:
            return jsonify({
                'available': False,
                'model': settings.get('ollama_model', 'phi3:mini'),
                'status': 'disconnected',
                'error': error
            }), 200
    except Exception as e:
        logger.error(f"Error checking Ollama: {str(e)}")
        return jsonify({
            'available': False,
            'error': str(e)
        }), 500

@ai_settings_bp.route('/models/list', methods=['GET'])
def list_models():
    """List available models (both built-in and Ollama)."""
    try:
        # Get built-in models
        built_in_models = [
            {
                "id": "built_in",
                "name": "Built-in AI Director",
                "description": "Default AI Director with built-in story generation",
                "type": "built-in"
            }
        ]
        
        # Get Ollama models
        ollama_models = []
        try:
            import requests
            
            # Get settings
            settings = get_ai_settings()
            
            # Get Ollama models
            response = requests.get(f"{settings.get('ollama_url', 'http://localhost:11434')}/api/tags")
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                
                for model in models:
                    ollama_models.append({
                        "id": model.get("name"),
                        "name": model.get("name"),
                        "description": "Ollama local model",
                        "type": "ollama"
                    })
        except Exception as e:
            logger.error(f"Error getting Ollama models: {str(e)}")
        
        # Combine models
        all_models = built_in_models + ollama_models
        
        return jsonify({
            'models': all_models,
            'count': len(all_models)
        }), 200
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_settings_bp.route('/test/generate', methods=['POST'])
def test_generate():
    """Test scene generation with current settings."""
    try:
        # Get data from request
        data = request.get_json()
        lyrics = data.get('lyrics')
        
        if not lyrics:
            return jsonify({'error': 'No lyrics provided'}), 400
        
        # Get settings
        settings = get_ai_settings()
        
        # Import DirectorIntegration
        try:
            from backend.ai.integration import DirectorIntegration
        except ImportError:
            try:
                from src.backend.ai.integration import DirectorIntegration
            except ImportError:
                return jsonify({'error': 'DirectorIntegration module not found'}), 404
        
        # Create director with settings
        director = DirectorIntegration(
            use_ollama=settings.get('use_ollama', False),
            ollama_model=settings.get('ollama_model', 'phi3:mini')
        )
        
        # Generate scenes
        scenes = director.enhance_scenes_from_lyrics(lyrics, scene_count=1)
        
        # Get story summary
        summary = director.get_story_summary(lyrics)
        
        # Return results
        return jsonify({
            'settings': settings,
            'summary': summary,
            'scene': scenes[0] if scenes else None,
            'scene_count': len(scenes),
            'model_type': 'ollama' if settings.get('use_ollama', False) else 'built_in'
        }), 200
    except Exception as e:
        logger.error(f"Error testing generation: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Register the blueprint
def register_blueprint(app):
    app.register_blueprint(ai_settings_bp)
