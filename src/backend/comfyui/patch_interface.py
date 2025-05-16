"""
Patch for ComfyUI interface to integrate the improved workflow updater.

This patch adds a hook to the ComfyUI interface to use the improved
workflow updater function instead of the original one.
"""

import sys
import os
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

def apply_patch():
    """
    Apply the improved_update_workflow patch to the ComfyUIInterface class.
    This should be called before using the ComfyUIInterface.
    """
    try:
        # Import original module
        from src.backend.comfyui.interface import ComfyUIInterface
        
        # Import the improved workflow updater
        from src.backend.comfyui.workflow_updater import improved_update_workflow
        
        # Backup the original method
        original_update_workflow = ComfyUIInterface.update_workflow
        
        # Replace with improved version
        def patched_update_workflow(self, workflow: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
            logger.info("Using improved workflow updater")
            return improved_update_workflow(workflow, updates)
        
        # Apply the patch
        ComfyUIInterface.update_workflow = patched_update_workflow
        
        logger.info("Successfully applied improved_update_workflow patch to ComfyUIInterface")
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply improved_update_workflow patch: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# Apply the patch when this module is imported
success = apply_patch()
