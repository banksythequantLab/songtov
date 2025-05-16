"""
MaiVid Studio - Video rendering progress tracker

This module provides progress tracking for the video rendering process,
allowing the frontend to display real-time progress updates.

Classes:
    RenderProgressTracker: Tracks progress of video rendering
"""

import os
import json
import time
import threading
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RenderProgressTracker:
    """
    Tracks the progress of video rendering operations.
    Provides a way to update and retrieve progress status.
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the progress tracker.
        
        Args:
            output_dir (str): Directory to save progress files
        """
        # Set output directory
        self.output_dir = output_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'outputs', 'progress')
        
        # Create progress directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Dictionary to store progress data
        self.progress_data = {}
        
        # Thread lock for thread safety
        self.lock = threading.Lock()
        
        logger.info(f"Initialized RenderProgressTracker with output directory: {self.output_dir}")
    
    def create_job(self, job_id: str, total_scenes: int, video_title: str) -> str:
        """
        Create a new rendering job.
        
        Args:
            job_id (str): Unique identifier for the job
            total_scenes (int): Total number of scenes in the video
            video_title (str): Title of the video
            
        Returns:
            str: Job ID
        """
        with self.lock:
            # Create progress data
            self.progress_data[job_id] = {
                'job_id': job_id,
                'video_title': video_title,
                'total_scenes': total_scenes,
                'processed_scenes': 0,
                'current_stage': 'initializing',
                'stage_name': 'initializing',
                'stage_progress': 0,
                'overall_progress': 0,
                'status': 'running',
                'started_at': time.time(),
                'updated_at': time.time(),
                'completed_at': None,
                'error': None,
                'scene_descriptions': []
            }
            
            # Save progress to file
            self._save_progress(job_id)
            
            logger.info(f"Created rendering job: {job_id} for video '{video_title}' with {total_scenes} scenes")
            
            return job_id
    
    def set_total_scenes(self, job_id: str, total_scenes: int) -> None:
        """
        Update the total number of scenes for a job.
        
        Args:
            job_id (str): Job identifier
            total_scenes (int): New total number of scenes
        """
        with self.lock:
            if job_id not in self.progress_data:
                logger.warning(f"Job {job_id} not found")
                return
            
            # Update total scenes
            job_data = self.progress_data[job_id]
            job_data['total_scenes'] = total_scenes
            job_data['updated_at'] = time.time()
            
            # Save progress to file
            self._save_progress(job_id)
            
            logger.debug(f"Updated total scenes for job {job_id}: {total_scenes}")
    
    def update_stage(self, job_id: str, stage_name: str, stage_description: str) -> None:
        """
        Update the current processing stage.
        
        Args:
            job_id (str): Job identifier
            stage_name (str): Short name of the current stage
            stage_description (str): Detailed description of the current stage
        """
        with self.lock:
            if job_id not in self.progress_data:
                logger.warning(f"Job {job_id} not found")
                return
            
            # Update stage information
            job_data = self.progress_data[job_id]
            job_data['stage_name'] = stage_name
            job_data['current_stage'] = stage_description
            job_data['stage_progress'] = 0  # Reset stage progress
            job_data['updated_at'] = time.time()
            
            # Update overall progress based on stage
            # Map stages to progress percentages
            stage_weights = {
                'initializing': 0,
                'download': 5,
                'lyrics': 10,
                'scene_planning': 15,
                'scene_generation': 20,
                'video_creation': 50
            }
            
            # Set overall progress based on stage
            if stage_name in stage_weights:
                job_data['overall_progress'] = stage_weights[stage_name]
            
            # Save progress to file
            self._save_progress(job_id)
            
            logger.debug(f"Updated stage for job {job_id}: {stage_name} - {stage_description}")
    
    def update_job(self, job_id: str, job_data: Dict[str, Any]) -> None:
        """
        Update job data with custom fields.
        
        Args:
            job_id (str): Job identifier
            job_data (Dict[str, Any]): Updated job data
        """
        with self.lock:
            if job_id not in self.progress_data:
                logger.warning(f"Job {job_id} not found")
                return
            
            # Update job data
            current_data = self.progress_data[job_id]
            current_data.update(job_data)
            current_data['updated_at'] = time.time()
            
            # Save progress to file
            self._save_progress(job_id)
            
            logger.debug(f"Updated job data for job {job_id}")
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job data without copying.
        
        Args:
            job_id (str): Job identifier
            
        Returns:
            Dict[str, Any]: Job data, or None if job not found
        """
        with self.lock:
            if job_id not in self.progress_data:
                # Try to load from file
                progress_file = os.path.join(self.output_dir, f"{job_id}.json")
                if os.path.exists(progress_file):
                    try:
                        with open(progress_file, 'r') as f:
                            self.progress_data[job_id] = json.load(f)
                    except Exception as e:
                        logger.error(f"Error loading progress file: {str(e)}")
                        return None
                else:
                    logger.warning(f"Job {job_id} not found")
                    return None
            
            return self.progress_data[job_id]
    
    def update_scene_progress(self, job_id: str, scene_index: int, scene_id: str) -> None:
        """
        Update progress for a scene.
        
        Args:
            job_id (str): Job identifier
            scene_index (int): Index of the scene being processed
            scene_id (str): ID of the scene being processed
        """
        with self.lock:
            if job_id not in self.progress_data:
                logger.warning(f"Job {job_id} not found")
                return
            
            # Update progress data
            job_data = self.progress_data[job_id]
            job_data['processed_scenes'] += 1
            job_data['current_stage'] = f"Processing scene {scene_index + 1}/{job_data['total_scenes']}"
            job_data['stage_progress'] = (scene_index + 1) / max(1, job_data['total_scenes']) * 100
            
            # Calculate overall progress based on current stage
            if job_data.get('stage_name') == 'scene_generation':
                # Scene generation is 20-50% of overall progress
                scene_start_percent = 20
                scene_end_percent = 50
                job_data['overall_progress'] = min(100, scene_start_percent + 
                                               (scene_end_percent - scene_start_percent) * 
                                               job_data['stage_progress'] / 100)
            elif job_data.get('stage_name') == 'video_creation':
                # Video creation is 50-100% of overall progress
                video_start_percent = 50
                video_end_percent = 75
                job_data['overall_progress'] = min(100, video_start_percent + 
                                               (video_end_percent - video_start_percent) * 
                                               job_data['stage_progress'] / 100)
            
            job_data['updated_at'] = time.time()
            
            # Save progress to file
            self._save_progress(job_id)
            
            logger.debug(f"Updated scene progress for job {job_id}: {scene_index + 1}/{job_data['total_scenes']}")
    
    def update_transition_progress(self, job_id: str, transition_index: int, total_transitions: int) -> None:
        """
        Update progress for transitions.
        
        Args:
            job_id (str): Job identifier
            transition_index (int): Index of the transition being processed
            total_transitions (int): Total number of transitions
        """
        with self.lock:
            if job_id not in self.progress_data:
                logger.warning(f"Job {job_id} not found")
                return
            
            # Update progress data
            job_data = self.progress_data[job_id]
            job_data['current_stage'] = f"Adding transitions {transition_index + 1}/{total_transitions}"
            job_data['stage_progress'] = (transition_index + 1) / max(1, total_transitions) * 100
            
            # Calculate overall progress in video creation stage (75-90%)
            video_start_percent = 75
            video_end_percent = 90
            job_data['overall_progress'] = min(100, video_start_percent + 
                                           (video_end_percent - video_start_percent) * 
                                           job_data['stage_progress'] / 100)
            
            job_data['updated_at'] = time.time()
            
            # Save progress to file
            self._save_progress(job_id)
            
            logger.debug(f"Updated transition progress for job {job_id}: {transition_index + 1}/{total_transitions}")
    
    def update_audio_progress(self, job_id: str, progress_percent: float) -> None:
        """
        Update progress for audio processing.
        
        Args:
            job_id (str): Job identifier
            progress_percent (float): Percentage of audio processing completed
        """
        with self.lock:
            if job_id not in self.progress_data:
                logger.warning(f"Job {job_id} not found")
                return
            
            # Update progress data
            job_data = self.progress_data[job_id]
            job_data['current_stage'] = f"Adding audio"
            job_data['stage_progress'] = progress_percent
            
            # Calculate overall progress (final 10% of progress, from 90-100%)
            audio_start_percent = 90
            audio_end_percent = 100
            job_data['overall_progress'] = min(100, audio_start_percent + 
                                           (audio_end_percent - audio_start_percent) * 
                                           progress_percent / 100)
            
            job_data['updated_at'] = time.time()
            
            # Save progress to file
            self._save_progress(job_id)
            
            logger.debug(f"Updated audio progress for job {job_id}: {progress_percent}%")
    
    def complete_job(self, job_id: str, video_path: str) -> None:
        """
        Mark a job as completed.
        
        Args:
            job_id (str): Job identifier
            video_path (str): Path to the completed video
        """
        with self.lock:
            if job_id not in self.progress_data:
                logger.warning(f"Job {job_id} not found")
                return
            
            # Update progress data
            job_data = self.progress_data[job_id]
            job_data['current_stage'] = "Completed"
            job_data['stage_progress'] = 100
            job_data['overall_progress'] = 100
            job_data['status'] = 'completed'
            job_data['completed_at'] = time.time()
            job_data['video_path'] = video_path
            
            # Save progress to file
            self._save_progress(job_id)
            
            logger.info(f"Completed rendering job {job_id}")
    
    def fail_job(self, job_id: str, error_message: str) -> None:
        """
        Mark a job as failed.
        
        Args:
            job_id (str): Job identifier
            error_message (str): Error message
        """
        with self.lock:
            if job_id not in self.progress_data:
                logger.warning(f"Job {job_id} not found")
                return
            
            # Update progress data
            job_data = self.progress_data[job_id]
            job_data['status'] = 'failed'
            job_data['error'] = error_message
            job_data['completed_at'] = time.time()
            
            # Save progress to file
            self._save_progress(job_id)
            
            logger.error(f"Failed rendering job {job_id}: {error_message}")
    
    def get_progress(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get progress for a job.
        
        Args:
            job_id (str): Job identifier
            
        Returns:
            Dict[str, Any]: Progress data, or None if job not found
        """
        with self.lock:
            if job_id not in self.progress_data:
                # Try to load from file
                progress_file = os.path.join(self.output_dir, f"{job_id}.json")
                if os.path.exists(progress_file):
                    try:
                        with open(progress_file, 'r') as f:
                            self.progress_data[job_id] = json.load(f)
                    except Exception as e:
                        logger.error(f"Error loading progress file: {str(e)}")
                        return None
                else:
                    logger.warning(f"Job {job_id} not found")
                    return None
            
            return self.progress_data[job_id].copy()
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """
        Get progress for all jobs.
        
        Returns:
            List[Dict[str, Any]]: Progress data for all jobs
        """
        with self.lock:
            # Load all progress files
            self._load_all_progress_files()
            
            # Return list of progress data
            return [job_data.copy() for job_data in self.progress_data.values()]
    
    def _save_progress(self, job_id: str) -> None:
        """
        Save progress to file.
        
        Args:
            job_id (str): Job identifier
        """
        if job_id not in self.progress_data:
            return
        
        progress_file = os.path.join(self.output_dir, f"{job_id}.json")
        
        try:
            with open(progress_file, 'w') as f:
                json.dump(self.progress_data[job_id], f)
        except Exception as e:
            logger.error(f"Error saving progress file: {str(e)}")
    
    def _load_all_progress_files(self) -> None:
        """
        Load all progress files.
        """
        try:
            for filename in os.listdir(self.output_dir):
                if filename.endswith('.json'):
                    job_id = filename[:-5]  # Remove .json extension
                    
                    # Skip if already loaded
                    if job_id in self.progress_data:
                        continue
                    
                    progress_file = os.path.join(self.output_dir, filename)
                    
                    try:
                        with open(progress_file, 'r') as f:
                            self.progress_data[job_id] = json.load(f)
                    except Exception as e:
                        logger.error(f"Error loading progress file {filename}: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading progress files: {str(e)}")


# Create a global instance for use across the application
progress_tracker = RenderProgressTracker()


# Example usage
if __name__ == "__main__":
    # Create a job
    job_id = "test_job_123"
    tracker = RenderProgressTracker()
    tracker.create_job(job_id, total_scenes=5, video_title="Test Video")
    
    # Update scene progress
    for i in range(5):
        tracker.update_scene_progress(job_id, i, f"scene_{i}")
        time.sleep(1)
    
    # Update transition progress
    for i in range(4):
        tracker.update_transition_progress(job_id, i, 4)
        time.sleep(1)
    
    # Update audio progress
    for i in range(0, 101, 20):
        tracker.update_audio_progress(job_id, i)
        time.sleep(1)
    
    # Complete the job
    tracker.complete_job(job_id, "outputs/videos/test_video.mp4")
    
    # Get progress
    progress = tracker.get_progress(job_id)
    print(f"Job progress: {json.dumps(progress, indent=2)}")
