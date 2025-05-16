"""
MaiVid Studio - App Initialization
"""

# Register blueprints
from src.backend.api.fast_render import register_blueprint as register_fast_render
from src.backend.api.ai_settings import register_blueprint as register_ai_settings

# Import the API blueprints
try:
    from src.backend.api.convo_pilot import convo_pilot_api
except ImportError:
    print("Could not import Convo Pilot API")
    convo_pilot_api = None

def register_blueprints(app):
    """Register all blueprints with the app."""
    register_fast_render(app)
    register_ai_settings(app)
    
    # Register Convo Pilot API blueprint
    if convo_pilot_api:
        app.register_blueprint(convo_pilot_api)
        print("Registered Convo Pilot API blueprint")
    else:
        print("Convo Pilot API not available, skipping registration")
