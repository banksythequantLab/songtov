"""
MaiVid Studio - Convo Pilot Integration

This module provides integration with Convo Pilot for video generation.
"""

import os
import sys
import json
import time
import logging
import requests
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConvoPilotIntegration:
    """Integration with Convo Pilot for video generation."""
    
    def __init__(self, base_url: str = "http://localhost:420"):
        """
        Initialize the Convo Pilot integration.
        
        Args:
            base_url: Base URL for the MaiVid Studio API
        """
        self.base_url = base_url
        logger.info(f"Initialized Convo Pilot integration with base URL: {base_url}")
    
    def create_video(self, 
                    url: str, 
                    model_type: str = "sdxl_turbo",
                    style: str = "cinematic",
                    scene_count: int = 4,
                    transition_type: str = "fade",
                    transition_duration: float = 1.0) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Create a video using Convo Pilot.
        
        Args:
            url: URL to download music from
            model_type: AI model to use for generation
            style: Visual style for the scenes
            scene_count: Number of scenes to generate
            transition_type: Type of transition between scenes
            transition_duration: Duration of transitions in seconds
            
        Returns:
            Tuple: (success, job_id or error message, response data)
        """
        try:
            # Create request data
            data = {
                "url": url,
                "model_type": model_type,
                "style": style,
                "scene_count": scene_count,
                "transition_type": transition_type,
                "transition_duration": transition_duration
            }
            
            logger.info(f"Creating video with URL: {url}, model: {model_type}, style: {style}")
            
            # Send request
            response = requests.post(f"{self.base_url}/api/convo_pilot/video", json=data, timeout=30)
            
            # Check if successful
            if response.status_code == 202:
                response_data = response.json()
                if response_data.get("success", False):
                    job_id = response_data.get("job_id", "")
                    logger.info(f"Successfully created video generation job: {job_id}")
                    return True, job_id, response_data
                else:
                    error = response_data.get("error", "Unknown error")
                    logger.error(f"Error in response: {error}")
                    return False, error, response_data
            else:
                logger.error(f"Error creating video: {response.status_code} - {response.text}")
                return False, f"Error {response.status_code}: {response.text}", {}
        
        except Exception as e:
            logger.error(f"Exception creating video: {str(e)}")
            return False, str(e), {}
    
    def get_job_status(self, job_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Get the status of a video generation job.
        
        Args:
            job_id: ID of the job to check
            
        Returns:
            Tuple: (success, job status data)
        """
        try:
            # Send request
            response = requests.get(f"{self.base_url}/api/convo_pilot/video/{job_id}", timeout=10)
            
            # Check if successful
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("success", False):
                    job_status = response_data.get("job_status", {})
                    return True, job_status
                else:
                    logger.error(f"Error in response: {response_data}")
                    return False, {}
            else:
                logger.error(f"Error getting job status: {response.status_code} - {response.text}")
                return False, {}
        
        except Exception as e:
            logger.error(f"Exception getting job status: {str(e)}")
            return False, {}
    
    def get_progress(self, job_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Get the progress of a video generation job.
        
        Args:
            job_id: ID of the job to check
            
        Returns:
            Tuple: (success, progress data)
        """
        try:
            # Send request
            response = requests.get(f"{self.base_url}/api/convo_pilot/video/progress/{job_id}", timeout=10)
            
            # Check if successful
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("success", False):
                    progress = response_data.get("progress", {})
                    return True, progress
                else:
                    logger.error(f"Error in response: {response_data}")
                    return False, {}
            else:
                logger.error(f"Error getting progress: {response.status_code} - {response.text}")
                return False, {}
        
        except Exception as e:
            logger.error(f"Exception getting progress: {str(e)}")
            return False, {}
    
    def get_available_models(self) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Get available AI models for video generation.
        
        Returns:
            Tuple: (success, list of models)
        """
        try:
            # Send request
            response = requests.get(f"{self.base_url}/api/convo_pilot/models", timeout=10)
            
            # Check if successful
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("success", False):
                    models = response_data.get("models", [])
                    return True, models
                else:
                    logger.error(f"Error in response: {response_data}")
                    return False, []
            else:
                logger.error(f"Error getting models: {response.status_code} - {response.text}")
                return False, []
        
        except Exception as e:
            logger.error(f"Exception getting models: {str(e)}")
            return False, []
    
    def get_available_styles(self) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Get available video styles.
        
        Returns:
            Tuple: (success, list of styles)
        """
        try:
            # Send request
            response = requests.get(f"{self.base_url}/api/convo_pilot/styles", timeout=10)
            
            # Check if successful
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("success", False):
                    styles = response_data.get("styles", [])
                    return True, styles
                else:
                    logger.error(f"Error in response: {response_data}")
                    return False, []
            else:
                logger.error(f"Error getting styles: {response.status_code} - {response.text}")
                return False, []
        
        except Exception as e:
            logger.error(f"Exception getting styles: {str(e)}")
            return False, []
    
    def monitor_job(self, job_id: str, 
                   callback: Optional[callable] = None, 
                   interval: int = 5, 
                   max_time: int = 300) -> bool:
        """
        Monitor a video generation job until completion or timeout.
        
        Args:
            job_id: ID of the job to monitor
            callback: Optional callback function to call with status updates
            interval: Polling interval in seconds
            max_time: Maximum monitoring time in seconds
            
        Returns:
            bool: True if job completed successfully, False otherwise
        """
        # Start time
        start_time = time.time()
        
        # Monitor job
        while time.time() - start_time < max_time:
            # Get job status
            success, job_status = self.get_job_status(job_id)
            
            # Check if successful
            if not success:
                logger.error(f"Error getting job status")
                time.sleep(interval)
                continue
            
            # Get status
            status = job_status.get("status", "unknown")
            progress = job_status.get("overall_progress", 0)
            current_stage = job_status.get("current_stage", "unknown")
            
            # Call callback if provided
            if callback:
                callback(job_id, status, progress, current_stage, job_status)
            
            # Check if job is complete
            if status == "completed":
                logger.info(f"Job {job_id} completed successfully!")
                return True
            elif status == "failed":
                error = job_status.get("error", "unknown")
                logger.error(f"Job {job_id} failed: {error}")
                return False
            
            # Sleep
            time.sleep(interval)
        
        logger.error(f"Timeout waiting for job {job_id} completion")
        return False


# Example usage
if __name__ == "__main__":
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Test the Convo Pilot integration")
    parser.add_argument("--url", default="http://localhost:420", help="Base URL for the MaiVid Studio API")
    parser.add_argument("--suno-url", default="https://suno.com/s/H6JQeAvqf4SgiFoF", help="Suno URL to use for testing")
    parser.add_argument("--monitor", action="store_true", help="Monitor job after creation")
    args = parser.parse_args()
    
    # Initialize integration
    convo_pilot = ConvoPilotIntegration(base_url=args.url)
    
    # Get available models
    print("\nGetting available models...")
    success, models = convo_pilot.get_available_models()
    if success:
        print(f"Found {len(models)} models:")
        for model in models:
            print(f"  - {model['name']} ({model['id']}): {model['description']}")
    else:
        print("Failed to get models")
    
    # Get available styles
    print("\nGetting available styles...")
    success, styles = convo_pilot.get_available_styles()
    if success:
        print(f"Found {len(styles)} styles:")
        for style in styles:
            print(f"  - {style['name']} ({style['id']}): {style['description']}")
    else:
        print("Failed to get styles")
    
    # Create video
    print(f"\nCreating video from URL: {args.suno_url}")
    success, job_id, response = convo_pilot.create_video(
        url=args.suno_url,
        model_type="sdxl_turbo",
        style="cinematic",
        scene_count=4,
        transition_type="fade",
        transition_duration=1.0
    )
    
    if success:
        print(f"Created video generation job: {job_id}")
        
        # Monitor job if requested
        if args.monitor:
            print("\nMonitoring job...")
            
            def status_callback(job_id, status, progress, stage, data):
                print(f"Status: {status}, Progress: {progress:.1f}%, Stage: {stage}")
            
            result = convo_pilot.monitor_job(job_id, callback=status_callback)
            
            if result:
                print("\nJob completed successfully!")
            else:
                print("\nJob failed or timed out")
    else:
        print(f"Failed to create video: {job_id}")
