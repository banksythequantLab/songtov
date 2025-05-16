"""
MaiVid Studio - Video processing module

This module handles video creation from generated images and audio,
including transitions, effects, and final rendering.

Functions:
    create_video: Create a video from images and audio
    apply_motion: Apply motion effects to images
    add_transitions: Add transitions between scenes
    render_final: Render the final video with all effects
"""

import os
import subprocess
import tempfile
import shutil
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoProcessor:
    """Handles video processing and generation."""
    
    def __init__(self, ffmpeg_path: Optional[str] = None, temp_dir: Optional[str] = None):
        """
        Initialize the video processor.
        
        Args:
            ffmpeg_path (str): Path to FFmpeg executable
            temp_dir (str): Directory for temporary files
        """
        # Find FFmpeg executable
        self.ffmpeg_path = ffmpeg_path or "ffmpeg"
        
        # Set temporary directory
        self.temp_dir = temp_dir or tempfile.gettempdir()
        
        # Create temp directory if it doesn't exist
        os.makedirs(self.temp_dir, exist_ok=True)
        
        logger.info(f"Initialized VideoProcessor with FFmpeg: {self.ffmpeg_path}")
        logger.info(f"Using temporary directory: {self.temp_dir}")

    def _run_ffmpeg_command(self, command: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Run an FFmpeg command.
        
        Args:
            command (List[str]): FFmpeg command and arguments
            
        Returns:
            Tuple: (success, error_message)
        """
        try:
            # Create full command with ffmpeg path
            full_command = [self.ffmpeg_path] + command
            
            # Log the command (excluding sensitive info)
            logger.debug(f"Running FFmpeg command: {' '.join(full_command)}")
            
            # Run the command
            process = subprocess.Popen(
                full_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Capture output
            stdout, stderr = process.communicate()
            
            # Check return code
            if process.returncode != 0:
                error_msg = f"FFmpeg error: {stderr}"
                logger.error(error_msg)
                return False, error_msg
                
            return True, None
            
        except Exception as e:
            error_msg = f"FFmpeg execution error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def apply_motion(self, 
                    image_path: str, 
                    output_path: str, 
                    motion_type: str = "zoom",
                    duration: float = 3.0,
                    zoom_factor: float = 1.2,
                    pan_x: float = 0,
                    pan_y: float = 0) -> Tuple[bool, Optional[str]]:
        """
        Apply motion effects to an image.
        
        Args:
            image_path (str): Path to the input image
            output_path (str): Path to save the output video
            motion_type (str): Type of motion (zoom, pan, ken_burns)
            duration (float): Duration of the motion effect in seconds
            zoom_factor (float): Amount of zoom (1.0 = no zoom, 2.0 = 2x zoom)
            pan_x (float): Horizontal pan (-1.0 to 1.0)
            pan_y (float): Vertical pan (-1.0 to 1.0)
            
        Returns:
            Tuple: (success, error_message)
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Base command parts
            command = [
                "-y",  # Overwrite output file if it exists
                "-loop", "1",  # Loop the input image
                "-i", image_path,  # Input image
                "-c:v", "libx264",  # Video codec
                "-t", str(duration),  # Duration
                "-pix_fmt", "yuv420p",  # Pixel format for compatibility
                "-vf"  # Video filter flag
            ]
            
            # Apply the specified motion effect
            if motion_type == "zoom":
                # Zoom effect: start normal and zoom in or out
                # Scale from 1.0 to zoom_factor
                zf = zoom_factor
                filter_complex = f"scale=trunc(iw*{zf}):trunc(ih*{zf}),zoompan=z='min(zoom+0.0015,{zf})':d={int(duration*25)}:s=1280x720"
                command.append(filter_complex)
                
            elif motion_type == "pan":
                # Pan effect: move across the image
                # Convert pan_x and pan_y from -1.0:1.0 to pixel values
                # Assuming 1.0 means move 25% of the image size
                filter_complex = f"zoompan=z=1.0:x='iw*{pan_x*0.25}*t/{duration}':y='ih*{pan_y*0.25}*t/{duration}':d={int(duration*25)}:s=1280x720"
                command.append(filter_complex)
                
            elif motion_type == "ken_burns":
                # Ken Burns effect: combination of pan and zoom
                # Start zoomed out, zoom in and pan
                start_zoom = 1.0
                end_zoom = zoom_factor
                
                # Calculate pan coordinates
                start_x = 0
                start_y = 0
                end_x = int(pan_x * 100)  # Convert -1.0:1.0 to percentage
                end_y = int(pan_y * 100)  # Convert -1.0:1.0 to percentage
                
                filter_complex = f"zoompan=z='min({start_zoom}+({end_zoom}-{start_zoom})*t/{duration},{end_zoom})':x='iw*{start_x/100}+iw*({end_x-start_x}/100)*t/{duration}':y='ih*{start_y/100}+ih*({end_y-start_y}/100)*t/{duration}':d={int(duration*25)}:s=1280x720"
                command.append(filter_complex)
                
            else:
                # Default: no motion, just convert to video
                filter_complex = "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2"
                command.append(filter_complex)
            
            # Add output path
            command.append(output_path)
            
            # Run FFmpeg command
            success, error = self._run_ffmpeg_command(command)
            
            if success:
                logger.info(f"Applied {motion_type} effect to {image_path}, output: {output_path}")
            
            return success, error
            
        except Exception as e:
            error_msg = f"Failed to apply motion effect: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def create_scene_video(self, 
                          scene_data: Dict[str, Any],
                          output_dir: str,
                          base_filename: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Create a video for a single scene.
        
        Args:
            scene_data (Dict): Scene data including image path and motion settings
            output_dir (str): Directory to save the output video
            base_filename (str): Base name for the output file
            
        Returns:
            Tuple: (output_video_path, error_message)
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Get scene parameters
            image_path = scene_data.get("image_path")
            if not image_path or not os.path.exists(image_path):
                return None, f"Scene image not found: {image_path}"
                
            motion_type = scene_data.get("motion_type", "zoom")
            duration = float(scene_data.get("duration", 3.0))
            zoom_factor = float(scene_data.get("zoom_factor", 1.2))
            pan_x = float(scene_data.get("pan_x", 0))
            pan_y = float(scene_data.get("pan_y", 0))
            
            # Create output path for the scene video
            scene_video_path = os.path.join(output_dir, f"{base_filename}_scene_{scene_data.get('id', 'unknown')}.mp4")
            
            # Apply motion effect to create the scene video
            success, error = self.apply_motion(
                image_path=image_path,
                output_path=scene_video_path,
                motion_type=motion_type,
                duration=duration,
                zoom_factor=zoom_factor,
                pan_x=pan_x,
                pan_y=pan_y
            )
            
            if not success:
                return None, error
                
            return scene_video_path, None
            
        except Exception as e:
            error_msg = f"Failed to create scene video: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def add_transition(self, 
                      video1_path: str, 
                      video2_path: str, 
                      output_path: str,
                      transition_type: str = "fade",
                      transition_duration: float = 1.0) -> Tuple[bool, Optional[str]]:
        """
        Add a transition between two videos.
        
        Args:
            video1_path (str): Path to the first video
            video2_path (str): Path to the second video
            output_path (str): Path to save the output video
            transition_type (str): Type of transition (fade, wipe, dissolve)
            transition_duration (float): Duration of the transition in seconds
            
        Returns:
            Tuple: (success, error_message)
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Get durations of the input videos
            probe_cmd1 = [
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                video1_path
            ]
            
            process1 = subprocess.Popen(
                [self.ffmpeg_path, *probe_cmd1],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout1, stderr1 = process1.communicate()
            if process1.returncode != 0:
                return False, f"FFmpeg error getting video1 duration: {stderr1}"
                
            video1_duration = float(json.loads(stdout1)["format"]["duration"])
            
            # Calculate transition points
            transition_start = max(0, video1_duration - transition_duration)
            
            # Create filter based on transition type
            if transition_type == "fade":
                # Crossfade transition
                filter_complex = (
                    f"[0:v]trim=0:{transition_start},setpts=PTS-STARTPTS[v0start];"
                    f"[0:v]trim={transition_start}:{video1_duration},setpts=PTS-STARTPTS[v0end];"
                    f"[1:v]trim=0:{transition_duration},setpts=PTS-STARTPTS[v1start];"
                    f"[1:v]trim={transition_duration},setpts=PTS-STARTPTS[v1end];"
                    f"[v0end][v1start]xfade=transition=fade:duration={transition_duration}:offset=0[xfade];"
                    f"[v0start][xfade][v1end]concat=n=3:v=1:a=0[outv]"
                )
                
            elif transition_type == "wipe":
                # Wipe transition
                filter_complex = (
                    f"[0:v]trim=0:{transition_start},setpts=PTS-STARTPTS[v0start];"
                    f"[0:v]trim={transition_start}:{video1_duration},setpts=PTS-STARTPTS[v0end];"
                    f"[1:v]trim=0:{transition_duration},setpts=PTS-STARTPTS[v1start];"
                    f"[1:v]trim={transition_duration},setpts=PTS-STARTPTS[v1end];"
                    f"[v0end][v1start]xfade=transition=wiperight:duration={transition_duration}:offset=0[xfade];"
                    f"[v0start][xfade][v1end]concat=n=3:v=1:a=0[outv]"
                )
                
            elif transition_type == "dissolve":
                # Dissolve transition
                filter_complex = (
                    f"[0:v]trim=0:{transition_start},setpts=PTS-STARTPTS[v0start];"
                    f"[0:v]trim={transition_start}:{video1_duration},setpts=PTS-STARTPTS[v0end];"
                    f"[1:v]trim=0:{transition_duration},setpts=PTS-STARTPTS[v1start];"
                    f"[1:v]trim={transition_duration},setpts=PTS-STARTPTS[v1end];"
                    f"[v0end][v1start]xfade=transition=dissolve:duration={transition_duration}:offset=0[xfade];"
                    f"[v0start][xfade][v1end]concat=n=3:v=1:a=0[outv]"
                )
                
            else:
                # Default: simple cut (no transition)
                filter_complex = "[0:v][1:v]concat=n=2:v=1:a=0[outv]"
            
            # Build FFmpeg command
            command = [
                "-y",  # Overwrite output if exists
                "-i", video1_path,  # First input video
                "-i", video2_path,  # Second input video
                "-filter_complex", filter_complex,  # Apply the filter
                "-map", "[outv]",  # Map the output
                "-c:v", "libx264",  # Video codec
                "-pix_fmt", "yuv420p",  # Pixel format for compatibility
                output_path  # Output path
            ]
            
            # Run FFmpeg command
            success, error = self._run_ffmpeg_command(command)
            
            if success:
                logger.info(f"Added {transition_type} transition between {video1_path} and {video2_path}, output: {output_path}")
            
            return success, error
            
        except Exception as e:
            error_msg = f"Failed to add transition: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def combine_videos_with_transitions(self, 
                                      video_paths: List[str], 
                                      output_path: str,
                                      transition_type: str = "fade",
                                      transition_duration: float = 1.0) -> Tuple[bool, Optional[str]]:
        """
        Combine multiple videos with transitions between them.
        
        Args:
            video_paths (List[str]): Paths to the input videos
            output_path (str): Path to save the output video
            transition_type (str): Type of transition (fade, wipe, dissolve)
            transition_duration (float): Duration of the transition in seconds
            
        Returns:
            Tuple: (success, error_message)
        """
        try:
            # Check if we have at least one video
            if not video_paths:
                return False, "No videos provided"
                
            # If only one video, just copy it
            if len(video_paths) == 1:
                shutil.copy(video_paths[0], output_path)
                logger.info(f"Only one video provided, copied to {output_path}")
                return True, None
                
            # Create temporary directory
            temp_dir = os.path.join(self.temp_dir, f"transition_temp_{os.path.basename(output_path)}")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Combine videos pairwise with transitions
            result_path = video_paths[0]
            
            for i in range(1, len(video_paths)):
                # Create temp output path for this pair
                temp_output = os.path.join(temp_dir, f"temp_transition_{i}.mp4")
                
                # Add transition between the current result and the next video
                success, error = self.add_transition(
                    video1_path=result_path,
                    video2_path=video_paths[i],
                    output_path=temp_output,
                    transition_type=transition_type,
                    transition_duration=transition_duration
                )
                
                if not success:
                    # Clean up temp files
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return False, error
                
                # Update result path for next iteration
                result_path = temp_output
            
            # Copy the final result to the output path
            shutil.copy(result_path, output_path)
            
            # Clean up temp files
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            logger.info(f"Combined {len(video_paths)} videos with {transition_type} transitions, output: {output_path}")
            return True, None
            
        except Exception as e:
            error_msg = f"Failed to combine videos with transitions: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def add_audio(self, 
                 video_path: str, 
                 audio_path: str, 
                 output_path: str,
                 start_time: float = 0,
                 normalize_audio: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Add audio to a video.
        
        Args:
            video_path (str): Path to the input video
            audio_path (str): Path to the audio file
            output_path (str): Path to save the output video
            start_time (float): Start time in the audio to align with video start
            normalize_audio (bool): Whether to normalize audio volume
            
        Returns:
            Tuple: (success, error_message)
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Build FFmpeg command
            command = [
                "-y",  # Overwrite output if exists
                "-i", video_path,  # Input video
                "-i", audio_path,  # Input audio
                "-map", "0:v",  # Map video from first input
                "-map", "1:a",  # Map audio from second input
                "-c:v", "copy"  # Copy video codec (no re-encoding)
            ]
            
            # Add start time offset if needed
            if start_time > 0:
                command.extend(["-ss", str(start_time)])
            
            # Add audio normalization if requested
            if normalize_audio:
                command.extend(["-af", "loudnorm=I=-16:TP=-1.5:LRA=11"])
            
            # Add output path
            command.append(output_path)
            
            # Run FFmpeg command
            success, error = self._run_ffmpeg_command(command)
            
            if success:
                logger.info(f"Added audio from {audio_path} to {video_path}, output: {output_path}")
            
            return success, error
            
        except Exception as e:
            error_msg = f"Failed to add audio: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def create_music_video(self, 
                          scenes: List[Dict[str, Any]], 
                          audio_path: str, 
                          output_path: str,
                          transition_type: str = "fade",
                          transition_duration: float = 1.0) -> Tuple[bool, Optional[str]]:
        """
        Create a complete music video from scenes and audio.
        
        Args:
            scenes (List[Dict]): List of scene data including image paths and motion settings
            audio_path (str): Path to the audio file
            output_path (str): Path to save the output video
            transition_type (str): Type of transition between scenes
            transition_duration (float): Duration of the transition in seconds
            
        Returns:
            Tuple: (success, error_message)
        """
        try:
            # Check if we have at least one scene
            if not scenes:
                return False, "No scenes provided"
                
            # Check if audio file exists
            if not os.path.exists(audio_path):
                return False, f"Audio file not found: {audio_path}"
                
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Create temporary directory
            base_name = os.path.splitext(os.path.basename(output_path))[0]
            temp_dir = os.path.join(self.temp_dir, f"musicvideo_temp_{base_name}")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Step 1: Create individual scene videos
            scene_videos = []
            
            for i, scene in enumerate(scenes):
                scene_output, error = self.create_scene_video(
                    scene_data=scene,
                    output_dir=temp_dir,
                    base_filename=f"scene_{i}"
                )
                
                if not scene_output:
                    # Clean up temp files
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return False, error
                    
                scene_videos.append(scene_output)
            
            # Step 2: Combine scene videos with transitions
            video_without_audio = os.path.join(temp_dir, "video_without_audio.mp4")
            
            success, error = self.combine_videos_with_transitions(
                video_paths=scene_videos,
                output_path=video_without_audio,
                transition_type=transition_type,
                transition_duration=transition_duration
            )
            
            if not success:
                # Clean up temp files
                shutil.rmtree(temp_dir, ignore_errors=True)
                return False, error
            
            # Step 3: Add audio to the video
            success, error = self.add_audio(
                video_path=video_without_audio,
                audio_path=audio_path,
                output_path=output_path,
                normalize_audio=True
            )
            
            # Clean up temp files
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            if success:
                logger.info(f"Created music video with {len(scenes)} scenes and audio, output: {output_path}")
                
            return success, error
            
        except Exception as e:
            error_msg = f"Failed to create music video: {str(e)}"
            logger.error(error_msg)
            return False, error_msg


# Example usage
if __name__ == "__main__":
    # Initialize the video processor
    processor = VideoProcessor()
    
    # Example scene data
    scenes = [
        {
            "id": "1",
            "image_path": "scene_images/scene1.jpg",
            "motion_type": "zoom",
            "duration": 5.0,
            "zoom_factor": 1.3,
            "pan_x": 0,
            "pan_y": 0
        },
        {
            "id": "2",
            "image_path": "scene_images/scene2.jpg",
            "motion_type": "ken_burns",
            "duration": 4.0,
            "zoom_factor": 1.2,
            "pan_x": 0.3,
            "pan_y": -0.2
        }
    ]
    
    # Create a music video
    success, error = processor.create_music_video(
        scenes=scenes,
        audio_path="audio/music.mp3",
        output_path="outputs/final_music_video.mp4",
        transition_type="fade",
        transition_duration=1.0
    )
    
    if success:
        print(f"Music video created successfully")
    else:
        print(f"Failed to create music video: {error}")
