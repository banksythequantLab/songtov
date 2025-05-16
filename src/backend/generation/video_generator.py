"""
MaiVid Studio - Video Generator Module

This module orchestrates the full video generation process, connecting the scene generation
and video rendering components together for end-to-end music video creation.
"""

import os
import logging
import json
import time
import uuid
import threading
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
from pathlib import Path

from ..audio.processor import download_from_url, extract_lyrics, clean_lyrics
from ..comfyui.interface import ComfyUIInterface
from ..comfyui.fast_renderer import FastRenderer
from ..video.processor import VideoProcessor
from ..video.progress_tracker import progress_tracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VideoGenerator:
    """Orchestrates the full video generation process from audio to final video."""
    
    def __init__(self, 
                comfyui_url: str = "http://127.0.0.1:8188",
                ffmpeg_path: str = "ffmpeg",
                output_dir: str = "outputs",
                upload_dir: str = "uploads"):
        """
        Initialize the video generator.
        
        Args:
            comfyui_url: URL of the ComfyUI server
            ffmpeg_path: Path to FFmpeg executable
            output_dir: Directory for output files
            upload_dir: Directory for uploaded files
        """
        self.comfyui_url = comfyui_url
        self.ffmpeg_path = ffmpeg_path
        self.output_dir = output_dir
        self.upload_dir = upload_dir
        
        # Initialize components
        self.comfyui = ComfyUIInterface(comfyui_url)
        self.fast_renderer = FastRenderer(comfyui_interface=self.comfyui)
        self.video_processor = VideoProcessor(ffmpeg_path=ffmpeg_path)
        
        # Create required directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "scenes"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "videos"), exist_ok=True)
        
        logger.info("VideoGenerator initialized")
    
    def generate_from_url(self, 
                         url: str, 
                         model_type: str = "sdxl_turbo",
                         aspect_ratio: str = "16:9",
                         style: str = "cinematic",
                         scene_count: int = None,
                         transition_type: str = "fade",
                         transition_duration: float = 1.0) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a music video from a URL.
        
        Args:
            url: URL to download music from
            model_type: AI model to use for generation
            aspect_ratio: Aspect ratio for the video
            style: Visual style for the scenes
            scene_count: Number of scenes to generate (None for auto)
            transition_type: Type of transition between scenes
            transition_duration: Duration of transitions in seconds
            
        Returns:
            Tuple: (job_id, job_info)
        """
        # Generate a unique job ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_id = f"job_{timestamp}_{uuid.uuid4().hex[:8]}"
        
        # Create a directory for this job
        job_dir = os.path.join(self.output_dir, "jobs", job_id)
        os.makedirs(job_dir, exist_ok=True)
        
        # Create directories for job outputs
        scenes_dir = os.path.join(job_dir, "scenes")
        os.makedirs(scenes_dir, exist_ok=True)
        
        # Initialize progress tracking
        progress_tracker.create_job(job_id, 0, f"Music Video: {url}")
        progress_tracker.update_stage(job_id, "download", "Downloading audio from URL")
        
        # Start the generation process in a background thread
        threading.Thread(
            target=self._generate_from_url_worker,
            args=(job_id, url, model_type, aspect_ratio, style, scene_count, transition_type, transition_duration)
        ).start()
        
        # Return the job ID and initial info
        job_info = {
            "job_id": job_id,
            "status": "started",
            "url": url,
            "creation_time": timestamp,
            "settings": {
                "model_type": model_type,
                "aspect_ratio": aspect_ratio,
                "style": style,
                "scene_count": scene_count,
                "transition_type": transition_type,
                "transition_duration": transition_duration
            }
        }
        
        return job_id, job_info
    
    def _generate_from_url_worker(self,
                                job_id: str,
                                url: str,
                                model_type: str,
                                aspect_ratio: str,
                                style: str,
                                scene_count: int,
                                transition_type: str,
                                transition_duration: float):
        """
        Worker function to handle the video generation process.
        
        Args:
            job_id: Unique identifier for this generation job
            url: URL to download music from
            model_type: AI model to use for generation
            aspect_ratio: Aspect ratio for the video
            style: Visual style for the scenes
            scene_count: Number of scenes to generate
            transition_type: Type of transition between scenes
            transition_duration: Duration of transitions in seconds
        """
        try:
            # Step 1: Download audio from URL
            logger.info(f"Job {job_id}: Downloading audio from {url}")
            progress_tracker.update_stage(job_id, "download", "Downloading audio from URL")
            
            file_path, error, metadata = download_from_url(url, self.upload_dir)
            
            if error:
                logger.error(f"Job {job_id}: Download failed: {error}")
                progress_tracker.fail_job(job_id, f"Download failed: {error}")
                return
            
            # Extract lyrics
            progress_tracker.update_stage(job_id, "lyrics", "Extracting lyrics from audio")
            lyrics, lyrics_error = extract_lyrics(file_path)
            cleaned_lyrics = clean_lyrics(lyrics) if lyrics else ""
            
            if not cleaned_lyrics:
                logger.warning(f"Job {job_id}: No lyrics extracted from audio, using basic scenes")
                # Continue without lyrics, we'll generate basic scenes
            else:
                logger.info(f"Job {job_id}: Extracted {len(cleaned_lyrics.split())} words of lyrics")
            
            # Parse lyrics into lines for scene generation
            lyrics_lines = cleaned_lyrics.split("\n") if cleaned_lyrics else []
            
            # Filter out empty lines
            lyrics_lines = [line.strip() for line in lyrics_lines if line.strip()]
            
            # Step 2: Determine number of scenes if not specified
            if scene_count is None:
                # Calculate based on song length or lyrics count
                if "duration" in metadata:
                    try:
                        # Extract duration in seconds
                        duration_str = metadata.get("duration", "0:00")
                        minutes, seconds = map(int, duration_str.split(":"))
                        duration_seconds = minutes * 60 + seconds
                        
                        # Roughly one scene per 15-25 seconds of audio
                        scene_count = max(4, min(12, round(duration_seconds / 20)))
                        logger.info(f"Job {job_id}: Auto-determined {scene_count} scenes based on {duration_seconds}s duration")
                    except Exception as e:
                        # Default to lyrics-based calculation
                        scene_count = None
                
                # If still None, calculate based on lyrics
                if scene_count is None and lyrics_lines:
                    # Roughly one scene per 4-8 lines of lyrics
                    scene_count = max(4, min(12, round(len(lyrics_lines) / 6)))
                    logger.info(f"Job {job_id}: Auto-determined {scene_count} scenes based on {len(lyrics_lines)} lyrics lines")
                
                # Fallback to default count
                if scene_count is None:
                    scene_count = 5
                    logger.info(f"Job {job_id}: Using default scene count of {scene_count}")
            
            # Update progress tracker with total scene count
            progress_tracker.set_total_scenes(job_id, scene_count)
            
            # Step 3: Generate scene descriptions from lyrics
            progress_tracker.update_stage(job_id, "scene_planning", "Creating scene descriptions from lyrics")
            
            scene_descriptions = []
            
            if lyrics_lines:
                # Group lyrics into chunks for scene generation
                chunk_size = max(1, len(lyrics_lines) // scene_count)
                
                # Lyrics blocks for each scene
                lyrics_chunks = []
                for i in range(0, len(lyrics_lines), chunk_size):
                    chunk = lyrics_lines[i:i + chunk_size]
                    lyrics_chunks.append(" ".join(chunk))
                
                # Ensure we don't exceed the requested scene count
                lyrics_chunks = lyrics_chunks[:scene_count]
                
                # Create scene descriptions
                for i, chunk in enumerate(lyrics_chunks):
                    scene = {
                        "scene_id": str(i + 1),
                        "description": chunk,
                        "style": style,
                        "timestamp": i * (30 if "duration" in metadata else 20)  # Approximate timestamp
                    }
                    scene_descriptions.append(scene)
            
            # If we didn't generate enough scenes from lyrics, add generic ones
            while len(scene_descriptions) < scene_count:
                i = len(scene_descriptions)
                scene = {
                    "scene_id": str(i + 1),
                    "description": f"Music video scene {i+1} in {style} style",
                    "style": style,
                    "timestamp": i * 20  # Approximate timestamp
                }
                scene_descriptions.append(scene)
            
            # Update progress with scene descriptions
            job_data = progress_tracker.get_job(job_id)
            if job_data:
                job_data["scene_descriptions"] = scene_descriptions
                progress_tracker.update_job(job_id, job_data)
            
            # Step 4: Generate scene images using ComfyUI
            progress_tracker.update_stage(job_id, "scene_generation", "Generating scene images")
            logger.info(f"Job {job_id}: Generating {len(scene_descriptions)} scenes")
            
            # Create work directory for this job's scenes
            scenes_dir = os.path.join(self.output_dir, "jobs", job_id, "scenes")
            os.makedirs(scenes_dir, exist_ok=True)
            
            # Generate scenes using the fast renderer
            scene_results = self.fast_renderer.batch_generate_scenes(
                scene_descriptions=scene_descriptions,
                model_type=model_type,
                aspect_ratio=aspect_ratio,
                output_dir=scenes_dir
            )
            
            # Count successful generations
            successful_scenes = [scene for scene in scene_results if scene.get("success", False)]
            
            logger.info(f"Job {job_id}: Generated {len(successful_scenes)}/{len(scene_results)} scenes successfully")
            
            # Check if we have enough scenes to continue
            if len(successful_scenes) < 2:
                error_msg = f"Not enough scenes were successfully generated (only {len(successful_scenes)})"
                logger.error(f"Job {job_id}: {error_msg}")
                progress_tracker.fail_job(job_id, error_msg)
                return
            
            # Step 5: Create video from scenes and audio
            progress_tracker.update_stage(job_id, "video_creation", "Creating video from scenes and audio")
            
            # Process successful scenes for video creation
            processed_scenes = []
            
            for scene in successful_scenes:
                scene_id = scene.get("scene_id", "unknown")
                image_path = scene.get("image_path")
                
                # Skip scenes without images
                if not image_path or not os.path.exists(image_path):
                    logger.warning(f"Job {job_id}: Skipping scene {scene_id}, image not found")
                    continue
                
                # Prepare scene for video processor
                processed_scenes.append({
                    'id': scene_id,
                    'image_path': image_path,
                    'duration': 5.0,  # Default duration - may vary based on song length
                    'motion_type': "ken_burns",  # Use Ken Burns effect by default
                    'zoom_factor': 1.2,
                    'pan_x': (hash(scene_id) % 20 - 10) / 10,  # Random pan between -1.0 and 1.0
                    'pan_y': (hash(scene_id + "y") % 20 - 10) / 10  # Different random pan for y
                })
            
            # Adjust scene durations based on audio length
            if "duration" in metadata and processed_scenes:
                try:
                    # Extract duration in seconds
                    duration_str = metadata.get("duration", "0:00")
                    minutes, seconds = map(int, duration_str.split(":"))
                    duration_seconds = minutes * 60 + seconds
                    
                    # Distribute time evenly across scenes
                    scene_duration = duration_seconds / len(processed_scenes)
                    
                    # Ensure reasonable duration (between 3-10 seconds per scene)
                    scene_duration = max(3.0, min(10.0, scene_duration))
                    
                    # Update durations
                    for scene in processed_scenes:
                        scene['duration'] = scene_duration
                        
                    logger.info(f"Job {job_id}: Set scene duration to {scene_duration:.1f}s based on audio length")
                except Exception as e:
                    logger.warning(f"Job {job_id}: Error calculating scene durations: {str(e)}")
            
            # Create a unique output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            song_title = metadata.get("title", "Unknown Song").replace(" ", "_")
            safe_title = ''.join(c for c in song_title if c.isalnum() or c in '._- ').strip()
            output_filename = f"{safe_title}_{timestamp}.mp4"
            output_path = os.path.join(self.output_dir, "videos", output_filename)
            
            # Create the video
            logger.info(f"Job {job_id}: Creating video with {len(processed_scenes)} scenes")
            
            # Render the video in steps to track progress
            try:
                # Step 1: Create individual scene videos
                scene_videos = []
                
                for i, scene in enumerate(processed_scenes):
                    try:
                        scene_output_dir = os.path.join(self.output_dir, "jobs", job_id, "temp")
                        os.makedirs(scene_output_dir, exist_ok=True)
                        
                        # Create scene video
                        scene_output, error = self.video_processor.create_scene_video(
                            scene_data=scene,
                            output_dir=scene_output_dir,
                            base_filename=f"scene_{i}"
                        )
                        
                        if error:
                            logger.error(f"Job {job_id}: Error creating scene {i}: {error}")
                            continue
                        
                        scene_videos.append(scene_output)
                        
                        # Update progress
                        progress_tracker.update_scene_progress(job_id, i, scene.get('id', ''))
                        
                    except Exception as e:
                        logger.error(f"Job {job_id}: Error processing scene {i}: {str(e)}")
                
                # Check if we have at least one scene
                if not scene_videos:
                    error_msg = "Failed to create any scene videos"
                    logger.error(f"Job {job_id}: {error_msg}")
                    progress_tracker.fail_job(job_id, error_msg)
                    return
                
                # Step 2: Combine scene videos with transitions
                video_without_audio = os.path.join(self.output_dir, "jobs", job_id, "temp", f"{job_id}_no_audio.mp4")
                os.makedirs(os.path.dirname(video_without_audio), exist_ok=True)
                
                # Number of transitions is scenes - 1
                num_transitions = len(scene_videos) - 1
                
                # Combine videos
                success, error = self.video_processor.combine_videos_with_transitions(
                    video_paths=scene_videos,
                    output_path=video_without_audio,
                    transition_type=transition_type,
                    transition_duration=transition_duration
                )
                
                if not success:
                    error_msg = f"Error combining scenes: {error}"
                    logger.error(f"Job {job_id}: {error_msg}")
                    progress_tracker.fail_job(job_id, error_msg)
                    return
                
                # Update progress to 75%
                progress_tracker.update_transition_progress(job_id, num_transitions, num_transitions)
                
                # Step 3: Add audio to the video
                # Add audio
                success, error = self.video_processor.add_audio(
                    video_path=video_without_audio,
                    audio_path=file_path,
                    output_path=output_path,
                    normalize_audio=True
                )
                
                if not success:
                    error_msg = f"Error adding audio: {error}"
                    logger.error(f"Job {job_id}: {error_msg}")
                    progress_tracker.fail_job(job_id, error_msg)
                    return
                
                # Update progress to 100%
                progress_tracker.update_audio_progress(job_id, 100)
                
                # Mark job as complete
                progress_tracker.complete_job(job_id, output_path)
                
                # Clean up temporary files
                try:
                    import shutil
                    temp_dir = os.path.join(self.output_dir, "jobs", job_id, "temp")
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    os.remove(video_without_audio) if os.path.exists(video_without_audio) else None
                except Exception as cleanup_error:
                    logger.warning(f"Job {job_id}: Error cleaning up temp files: {str(cleanup_error)}")
                
                logger.info(f"Job {job_id}: Video creation completed successfully: {output_path}")
                
                # Save job details to JSON
                job_result = {
                    "job_id": job_id,
                    "url": url,
                    "output_path": output_path,
                    "metadata": metadata,
                    "scenes": scene_results,
                    "settings": {
                        "model_type": model_type,
                        "aspect_ratio": aspect_ratio,
                        "style": style,
                        "scene_count": scene_count,
                        "transition_type": transition_type,
                        "transition_duration": transition_duration
                    },
                    "status": "completed",
                    "completion_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Save job result to JSON
                result_path = os.path.join(self.output_dir, "jobs", job_id, "result.json")
                with open(result_path, 'w') as f:
                    json.dump(job_result, f, indent=2)
                
            except Exception as e:
                error_msg = f"Error creating video: {str(e)}"
                logger.error(f"Job {job_id}: {error_msg}")
                import traceback
                logger.error(traceback.format_exc())
                progress_tracker.fail_job(job_id, error_msg)
        
        except Exception as e:
            error_msg = f"Error in video generation process: {str(e)}"
            logger.error(f"Job {job_id}: {error_msg}")
            import traceback
            logger.error(traceback.format_exc())
            progress_tracker.fail_job(job_id, error_msg)
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a video generation job.
        
        Args:
            job_id: ID of the job to check
            
        Returns:
            Dict: Current job status
        """
        return progress_tracker.get_progress(job_id)


# Example usage
if __name__ == "__main__":
    # Initialize the video generator
    generator = VideoGenerator()
    
    # Generate a video from a URL
    job_id, job_info = generator.generate_from_url(
        url="https://suno.com/s/H6JQeAvqf4SgiFoF",
        model_type="sdxl_turbo",
        aspect_ratio="16:9",
        style="cinematic",
        scene_count=5,
        transition_type="fade",
        transition_duration=1.0
    )
    
    print(f"Started video generation job: {job_id}")
    print(f"Job info: {job_info}")
    
    # Wait for the job to complete
    while True:
        status = generator.get_job_status(job_id)
        print(f"Job status: {status.get('status', 'unknown')}, progress: {status.get('progress', 0)}%")
        
        if status.get('status') == 'completed':
            print(f"Job completed successfully! Output: {status.get('output_path')}")
            break
        elif status.get('status') == 'failed':
            print(f"Job failed: {status.get('error')}")
            break
            
        time.sleep(5)
