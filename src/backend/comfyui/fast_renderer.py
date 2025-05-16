"""
MaiVid Studio - Fast ComfyUI Renderer

This module extends the ComfyUI interface with specialized methods for fast image generation
using optimized models like SDXL Turbo and SD3 Turbo. It's designed for rapid scene prototype
generation in the music video creation pipeline.

Functions:
    initialize_fast_renderer: Sets up the fast renderer with ComfyUI
    batch_generate_scenes: Generate multiple scenes in a batch for a music video
    setup_turbo_workflow: Prepares a workflow file configured for speed
"""

import os
import json
import time
import random
import logging
import shutil
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path

from .interface import ComfyUIInterface

# Configure logging
logger = logging.getLogger(__name__)

# Constants
WORKFLOW_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "workflows")
DEFAULT_FAST_WORKFLOW = os.path.join(WORKFLOW_DIR, "sdxl_turbo.json")
DEFAULT_SD3_WORKFLOW = os.path.join(WORKFLOW_DIR, "sd3_fast.json")

# Default aspect ratios
ASPECT_RATIOS = {
    "16:9": (896, 504),
    "1:1": (768, 768),
    "9:16": (504, 896),
    "21:9": (1024, 440),
    "4:3": (768, 576)
}

class FastRenderer:
    """Fast renderer for music video scenes using optimized workflows."""
    
    def __init__(self, comfyui_interface: ComfyUIInterface = None, comfyui_url: str = None):
        """
        Initialize the fast renderer.
        
        Args:
            comfyui_interface: An existing ComfyUI interface, or None to create a new one
            comfyui_url: URL for the ComfyUI server if creating a new interface
        """
        if comfyui_interface:
            self.comfyui = comfyui_interface
        elif comfyui_url:
            self.comfyui = ComfyUIInterface(comfyui_url)
        else:
            self.comfyui = ComfyUIInterface()
        
        # Ensure workflow directory exists
        os.makedirs(WORKFLOW_DIR, exist_ok=True)
        
        # Check if default workflows exist, otherwise create them
        self.ensure_default_workflows()
        
        logger.info("FastRenderer initialized")
        
    def ensure_default_workflows(self):
        """
        Ensure default workflow files exist, create them if not.
        """
        sdxl_turbo_path = DEFAULT_FAST_WORKFLOW
        sd3_path = DEFAULT_SD3_WORKFLOW
        
        # Create default SDXL Turbo workflow if needed
        if not os.path.exists(sdxl_turbo_path):
            logger.info(f"Creating default SDXL Turbo workflow at {sdxl_turbo_path}")
            self._create_sdxl_turbo_workflow(sdxl_turbo_path)
            
        # Create default SD3 workflow if needed
        if not os.path.exists(sd3_path):
            logger.info(f"Creating default SD3 workflow at {sd3_path}")
            self._create_sd3_workflow(sd3_path)
    
    def _create_sdxl_turbo_workflow(self, path: str):
        """Create SDXL Turbo workflow file."""
        workflow = {
            "last_node_id": 28,
            "last_link_id": 54,
            "nodes": [
                {
                    "id": 5,
                    "type": "EmptyLatentImage",
                    "pos": [462, 398],
                    "size": [315, 106],
                    "flags": {},
                    "order": 3,
                    "mode": 0,
                    "inputs": [],
                    "outputs": [{"name": "LATENT", "type": "LATENT", "slot_index": 0, "links": [23]}],
                    "properties": {"Node name for S&R": "EmptyLatentImage"},
                    "widgets_values": [896, 504, 1]  # Default 16:9 resolution
                },
                {
                    "id": 6,
                    "type": "CLIPTextEncode",
                    "pos": [351, -45],
                    "size": [422.85, 164.31],
                    "flags": {},
                    "order": 5,
                    "mode": 0,
                    "inputs": [{"name": "clip", "type": "CLIP", "link": 38}],
                    "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "slot_index": 0, "links": [19]}],
                    "properties": {"Node name for S&R": "CLIPTextEncode"},
                    "widgets_values": ["Scene description goes here, replace at runtime"]
                },
                {
                    "id": 7,
                    "type": "CLIPTextEncode",
                    "pos": [352, 176],
                    "size": [425.28, 180.61],
                    "flags": {},
                    "order": 6,
                    "mode": 0,
                    "inputs": [{"name": "clip", "type": "CLIP", "link": 39}],
                    "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "slot_index": 0, "links": [20]}],
                    "properties": {"Node name for S&R": "CLIPTextEncode"},
                    "widgets_values": ["worst quality, normal quality, low quality, low res, blurry, distortion, watermark, banner, extra digits, cropped, jpeg artifacts, signature, username, error, sketch, duplicate, ugly, monochrome, horror, geometry, mutation, disgusting, bad anatomy, bad proportions, bad quality, deformed, disconnected limbs, out of frame, out of focus, dehydrated, disfigured"]
                },
                {
                    "id": 8,
                    "type": "VAEDecode",
                    "pos": [1183, -66],
                    "size": [210, 46],
                    "flags": {},
                    "order": 8,
                    "mode": 0,
                    "inputs": [
                        {"name": "samples", "type": "LATENT", "link": 28},
                        {"name": "vae", "type": "VAE", "link": 40}
                    ],
                    "outputs": [{"name": "IMAGE", "type": "IMAGE", "slot_index": 0, "links": [53, 54]}],
                    "properties": {"Node name for S&R": "VAEDecode"}
                },
                {
                    "id": 13,
                    "type": "SamplerCustom",
                    "pos": [800, -66],
                    "size": [355.2, 442],
                    "flags": {},
                    "order": 7,
                    "mode": 0,
                    "inputs": [
                        {"name": "model", "type": "MODEL", "link": 41},
                        {"name": "positive", "type": "CONDITIONING", "link": 19},
                        {"name": "negative", "type": "CONDITIONING", "link": 20},
                        {"name": "sampler", "type": "SAMPLER", "link": 18},
                        {"name": "sigmas", "type": "SIGMAS", "link": 49},
                        {"name": "latent_image", "type": "LATENT", "link": 23}
                    ],
                    "outputs": [
                        {"name": "output", "type": "LATENT", "slot_index": 0, "links": [28]},
                        {"name": "denoised_output", "type": "LATENT", "links": None}
                    ],
                    "properties": {"Node name for S&R": "SamplerCustom"},
                    "widgets_values": [True, 0, "fixed", 1.2]
                },
                {
                    "id": 14,
                    "type": "KSamplerSelect",
                    "pos": [452, -144],
                    "size": [315, 58],
                    "flags": {},
                    "order": 1,
                    "mode": 0,
                    "inputs": [],
                    "outputs": [{"name": "SAMPLER", "type": "SAMPLER", "links": [18]}],
                    "properties": {"Node name for S&R": "KSamplerSelect"},
                    "widgets_values": ["euler_ancestral"]
                },
                {
                    "id": 20,
                    "type": "CheckpointLoaderSimple",
                    "pos": [-17, -70],
                    "size": [343.7, 98],
                    "flags": {},
                    "order": 0,
                    "mode": 0,
                    "inputs": [],
                    "outputs": [
                        {"name": "MODEL", "type": "MODEL", "slot_index": 0, "links": [41, 45]},
                        {"name": "CLIP", "type": "CLIP", "slot_index": 1, "links": [38, 39]},
                        {"name": "VAE", "type": "VAE", "slot_index": 2, "links": [40]}
                    ],
                    "properties": {"Node name for S&R": "CheckpointLoaderSimple"},
                    "widgets_values": ["sd_xl_turbo_1.0_fp16.safetensors"]
                },
                {
                    "id": 22,
                    "type": "SDTurboScheduler",
                    "pos": [452, -248],
                    "size": [315, 82],
                    "flags": {},
                    "order": 4,
                    "mode": 0,
                    "inputs": [{"name": "model", "type": "MODEL", "link": 45}],
                    "outputs": [{"name": "SIGMAS", "type": "SIGMAS", "slot_index": 0, "links": [49]}],
                    "properties": {"Node name for S&R": "SDTurboScheduler"},
                    "widgets_values": [1, 1]
                },
                {
                    "id": 25,
                    "type": "PreviewImage",
                    "pos": [1450, -150],
                    "size": [360, 400],
                    "flags": {},
                    "order": 9,
                    "mode": 0,
                    "inputs": [
                        {"name": "images", "type": "IMAGE", "link": 53}
                    ],
                    "outputs": [],
                    "properties": {"Node name for S&R": "PreviewImage"},
                    "widgets_values": []
                },
                {
                    "id": 27,
                    "type": "SaveImage",
                    "pos": [1843, -154],
                    "size": [466.79, 516.83],
                    "flags": {},
                    "order": 10,
                    "mode": 2,
                    "inputs": [{"name": "images", "type": "IMAGE", "link": 54}],
                    "outputs": [],
                    "properties": {"Node name for S&R": "SaveImage"},
                    "widgets_values": ["MaiVid_Scenes"]
                }
            ],
            "links": [
                [18, 14, 0, 13, 3, "SAMPLER"],
                [19, 6, 0, 13, 1, "CONDITIONING"],
                [20, 7, 0, 13, 2, "CONDITIONING"],
                [23, 5, 0, 13, 5, "LATENT"],
                [28, 13, 0, 8, 0, "LATENT"],
                [38, 20, 1, 6, 0, "CLIP"],
                [39, 20, 1, 7, 0, "CLIP"],
                [40, 20, 2, 8, 1, "VAE"],
                [41, 20, 0, 13, 0, "MODEL"],
                [45, 20, 0, 22, 0, "MODEL"],
                [49, 22, 0, 13, 4, "SIGMAS"],
                [53, 8, 0, 25, 0, "IMAGE"],
                [54, 8, 0, 27, 0, "IMAGE"]
            ],
            "version": 0.4
        }
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(workflow, f, indent=2)
        
        logger.info(f"Created SDXL Turbo workflow at {path}")
        
    def _create_sd3_workflow(self, path: str):
        """Create SD3 workflow file."""
        workflow = {
            "last_node_id": 54,
            "last_link_id": 102,
            "nodes": [
                {
                    "id": 3,
                    "type": "KSampler",
                    "pos": [864, 96],
                    "size": [315, 474],
                    "flags": {},
                    "order": 5,
                    "mode": 0,
                    "inputs": [
                        {"name": "model", "type": "MODEL", "link": 99},
                        {"name": "positive", "type": "CONDITIONING", "link": 21},
                        {"name": "negative", "type": "CONDITIONING", "link": 80},
                        {"name": "latent_image", "type": "LATENT", "link": 100}
                    ],
                    "outputs": [{"name": "LATENT", "type": "LATENT", "slot_index": 0, "links": [7]}],
                    "properties": {"Node name for S&R": "KSampler"},
                    "widgets_values": [
                        random.randint(0, 9999999999),  # Random seed
                        "randomize",
                        8,  # Reduced steps for speed
                        4.01,
                        "euler",
                        "sgm_uniform",
                        1
                    ]
                },
                {
                    "id": 4,
                    "type": "CheckpointLoaderSimple",
                    "pos": [-48, 96],
                    "size": [384.76, 98],
                    "flags": {},
                    "order": 0,
                    "mode": 0,
                    "inputs": [],
                    "outputs": [
                        {"name": "MODEL", "type": "MODEL", "slot_index": 0, "links": [99]},
                        {"name": "CLIP", "type": "CLIP", "slot_index": 1, "links": [101, 102]},
                        {"name": "VAE", "type": "VAE", "slot_index": 2, "links": [53]}
                    ],
                    "properties": {"Node name for S&R": "CheckpointLoaderSimple"},
                    "widgets_values": ["sd3.5_large_fp8_scaled.safetensors"]
                },
                {
                    "id": 8,
                    "type": "VAEDecode",
                    "pos": [1200, 96],
                    "size": [210, 46],
                    "flags": {},
                    "order": 6,
                    "mode": 0,
                    "inputs": [
                        {"name": "samples", "type": "LATENT", "link": 7},
                        {"name": "vae", "type": "VAE", "link": 53}
                    ],
                    "outputs": [{"name": "IMAGE", "type": "IMAGE", "slot_index": 0, "links": [51]}],
                    "properties": {"Node name for S&R": "VAEDecode"}
                },
                {
                    "id": 9,
                    "type": "SaveImage",
                    "pos": [1440, 96],
                    "size": [952, 1007],
                    "flags": {},
                    "order": 7,
                    "mode": 0,
                    "inputs": [{"name": "images", "type": "IMAGE", "link": 51}],
                    "outputs": [],
                    "properties": {"Node name for S&R": "SaveImage"},
                    "widgets_values": ["MaiVid_Scenes"]
                },
                {
                    "id": 16,
                    "type": "CLIPTextEncode",
                    "pos": [384, 96],
                    "size": [432, 192],
                    "flags": {},
                    "order": 3,
                    "mode": 0,
                    "inputs": [{"name": "clip", "type": "CLIP", "link": 101}],
                    "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "slot_index": 0, "links": [21]}],
                    "title": "Positive Prompt",
                    "properties": {"Node name for S&R": "CLIPTextEncode"},
                    "widgets_values": ["Scene description goes here, replace at runtime"]
                },
                {
                    "id": 40,
                    "type": "CLIPTextEncode",
                    "pos": [384, 336],
                    "size": [432, 192],
                    "flags": {},
                    "order": 4,
                    "mode": 0,
                    "inputs": [{"name": "clip", "type": "CLIP", "link": 102}],
                    "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "slot_index": 0, "links": [80]}],
                    "title": "Negative Prompt",
                    "properties": {"Node name for S&R": "CLIPTextEncode"},
                    "widgets_values": ["worst quality, normal quality, low quality, low res, blurry, distortion, watermark, banner, extra digits, cropped, jpeg artifacts, signature, username, error, sketch, duplicate, ugly, monochrome, horror, geometry, mutation, disgusting, bad anatomy, bad proportions"]
                },
                {
                    "id": 53,
                    "type": "EmptySD3LatentImage",
                    "pos": [480, 576],
                    "size": [315, 106],
                    "flags": {},
                    "order": 2,
                    "mode": 0,
                    "inputs": [],
                    "outputs": [{"name": "LATENT", "type": "LATENT", "slot_index": 0, "links": [100]}],
                    "properties": {"Node name for S&R": "EmptySD3LatentImage"},
                    "widgets_values": [1024, 576, 1]  # 16:9 ratio
                }
            ],
            "links": [
                [7, 3, 0, 8, 0, "LATENT"],
                [21, 16, 0, 3, 1, "CONDITIONING"],
                [51, 8, 0, 9, 0, "IMAGE"],
                [53, 4, 2, 8, 1, "VAE"],
                [80, 40, 0, 3, 2, "CONDITIONING"],
                [99, 4, 0, 3, 0, "MODEL"],
                [100, 53, 0, 3, 3, "LATENT"],
                [101, 4, 1, 16, 0, "CLIP"],
                [102, 4, 1, 40, 0, "CLIP"]
            ],
            "version": 0.4
        }
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(workflow, f, indent=2)
        
        logger.info(f"Created SD3 workflow at {path}")
        
    def generate_scene(self, 
                      scene_description: str, 
                      model_type: str = "sdxl_turbo",
                      aspect_ratio: str = "16:9",
                      style: str = "cinematic", 
                      output_dir: str = "outputs/scenes") -> Tuple[Optional[str], Optional[str]]:
        """
        Generate a scene image using fast generation methods.
        
        Args:
            scene_description: Description of the scene to generate
            model_type: Model type to use (sdxl_turbo, sd3, flux)
            aspect_ratio: Aspect ratio for the image (16:9, 1:1, 9:16, 21:9, 4:3)
            style: Style of the image
            output_dir: Directory to save the output image
            
        Returns:
            Tuple: (path_to_generated_image, error_message)
        """
        try:
            # Select workflow based on model type
            if model_type == "sdxl_turbo":
                workflow_file = DEFAULT_FAST_WORKFLOW
                width, height = ASPECT_RATIOS.get(aspect_ratio, (896, 504))
                node_type = "EmptyLatentImage"
                model_file = "sd_xl_turbo_1.0_fp16.safetensors"
            elif model_type == "sd3":
                workflow_file = DEFAULT_SD3_WORKFLOW
                width, height = ASPECT_RATIOS.get(aspect_ratio, (1024, 576))
                node_type = "EmptySD3LatentImage"
                model_file = "sd3.5_large_fp8_scaled.safetensors"
            elif model_type == "flux":
                workflow_file = DEFAULT_FAST_WORKFLOW  # Use SDXL workflow but change model
                width, height = ASPECT_RATIOS.get(aspect_ratio, (896, 504))
                node_type = "EmptyLatentImage"
                model_file = "Flux.safetensors"
            else:
                return None, f"Unsupported model type: {model_type}"
            
            # Ensure workflow file exists
            if not os.path.exists(workflow_file):
                logger.info(f"Workflow file not found, creating default: {workflow_file}")
                if model_type == "sdxl_turbo" or model_type == "flux":
                    self._create_sdxl_turbo_workflow(workflow_file)
                else:
                    self._create_sd3_workflow(workflow_file)
            
            # Load the workflow
            try:
                workflow = self.comfyui.load_workflow(workflow_file)
            except Exception as e:
                logger.error(f"Error loading workflow file: {e}")
                # Try to fix the workflow
                from .fix_workflow import fix_workflow_file
                fixed_workflow_file = workflow_file.replace('.json', '_fixed.json')
                if fix_workflow_file(workflow_file, fixed_workflow_file):
                    logger.info(f"Fixed workflow file, using: {fixed_workflow_file}")
                    workflow_file = fixed_workflow_file
                    workflow = self.comfyui.load_workflow(workflow_file)
                else:
                    return None, f"Failed to load or fix workflow file: {str(e)}"
            
            # Update the prompt with scene description and style
            prompt = f"{scene_description}, {style} style, high quality, detailed"
            
            # Find nodes to update
            positive_node_id = None
            checkpoint_node_id = None
            resolution_node_id = None
            save_node_id = None
            
            for node in workflow["nodes"]:
                # Find positive prompt node
                if node["type"] == "CLIPTextEncode":
                    # Skip negative prompt nodes
                    if "title" in node and "negative" in node["title"].lower():
                        continue
                    if "widgets_values" in node and len(node["widgets_values"]) > 0:
                        val = node["widgets_values"][0]
                        if isinstance(val, str) and not any(neg_word in val.lower() for neg_word in ["worst quality", "bad quality"]):
                            positive_node_id = node["id"]
                
                # Find checkpoint loader
                if node["type"] == "CheckpointLoaderSimple":
                    checkpoint_node_id = node["id"]
                
                # Find resolution node
                if node["type"] == node_type:
                    resolution_node_id = node["id"]
                
                # Find save node
                if node["type"] == "SaveImage":
                    save_node_id = node["id"]
            
            # Update workflow
            updates = {}
            
            # Update prompt
            if positive_node_id is not None:
                updates[f"{positive_node_id}.text"] = prompt
            
            # Update model if needed
            if checkpoint_node_id is not None and model_type != "sdxl_turbo":
                # Only update if not using default
                updates[f"{checkpoint_node_id}.ckpt_name"] = model_file
            
            # Update resolution
            if resolution_node_id is not None:
                updates[f"{resolution_node_id}.width"] = width
                updates[f"{resolution_node_id}.height"] = height
            
            # Update output settings
            if save_node_id is not None:
                # Generate unique output name
                import time
                import uuid
                timestamp = int(time.time())
                unique_id = str(uuid.uuid4())[:8]
                output_prefix = f"scene_{timestamp}_{unique_id}"
                
                updates[f"{save_node_id}.filename_prefix"] = output_prefix
                updates[f"{save_node_id}.output_dir"] = output_dir
            
            # Apply updates
            updated_workflow = self.comfyui.update_workflow(workflow, updates)
            
            # Add random seed
            for node in updated_workflow["nodes"]:
                if node["type"] in ["KSampler", "SamplerCustom"] and "widgets_values" in node and len(node["widgets_values"]) > 0:
                    node["widgets_values"][0] = random.randint(0, 9999999999)
            
            # Queue the prompt
            logger.info(f"Queueing workflow with model {model_type}, aspect ratio {aspect_ratio}")
            prompt_id, error = self.comfyui.queue_prompt(updated_workflow)
            
            if error:
                return None, f"Failed to queue prompt: {error}"
            
            # Wait for the result
            logger.info(f"Waiting for prompt {prompt_id} to complete")
            success, result = self.comfyui.wait_for_prompt(prompt_id)
            
            if not success:
                error_msg = result.get("error", "Unknown error")
                return None, f"Error processing prompt: {error_msg}"
            
            # Download images
            logger.info("Prompt completed, downloading images")
            image_paths = self.comfyui.download_output_images(result, output_dir)
            
            if image_paths:
                # Return first image path
                return next(iter(image_paths.values())), None
            else:
                # Try to find images directly in output dir with the prefix
                try:
                    if save_node_id is not None and 'output_prefix' in locals():
                        matching_files = [f for f in os.listdir(output_dir) if f.startswith(output_prefix)]
                        if matching_files:
                            return os.path.join(output_dir, matching_files[0]), None
                except Exception as find_error:
                    logger.error(f"Error trying to find images in output dir: {find_error}")
                
                return None, "No images generated"
            
        except Exception as e:
            error_msg = f"Failed to generate scene: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            return None, error_msg
    
    def batch_generate_scenes(self, 
                             scene_descriptions: List[Dict[str, str]], 
                             model_type: str = "sdxl_turbo",
                             aspect_ratio: str = "16:9",
                             output_dir: str = "outputs/scenes") -> List[Dict[str, str]]:
        """
        Generate multiple scene images in batch.
        
        Args:
            scene_descriptions: List of scene descriptions with metadata
                Example: [
                    {
                        "description": "A motorcycle courier speeds through neon streets",
                        "style": "cyberpunk",
                        "scene_id": "1"
                    },
                    ...
                ]
            model_type: Model type to use
            aspect_ratio: Aspect ratio for the images
            output_dir: Directory to save the output images
            
        Returns:
            List of results with scene info and paths/errors
        """
        results = []
        
        logger.info(f"Batch generating {len(scene_descriptions)} scenes with {model_type}")
        start_time = time.time()
        
        for i, scene in enumerate(scene_descriptions):
            scene_id = scene.get("scene_id", str(i))
            description = scene.get("description", "")
            style = scene.get("style", "cinematic")
            
            logger.info(f"Generating scene {i+1}/{len(scene_descriptions)}: {scene_id}")
            
            # Generate the scene
            image_path, error = self.generate_scene(
                scene_description=description,
                model_type=model_type,
                aspect_ratio=aspect_ratio,
                style=style,
                output_dir=os.path.join(output_dir, f"scene_{scene_id}")
            )
            
            # Record the result
            result = {
                "scene_id": scene_id,
                "description": description,
                "style": style,
                "success": image_path is not None,
                "image_path": image_path,
                "error": error
            }
            
            results.append(result)
            
            # Log progress
            elapsed = time.time() - start_time
            avg_time = elapsed / (i + 1)
            remaining = avg_time * (len(scene_descriptions) - i - 1)
            
            logger.info(f"Scene {i+1}/{len(scene_descriptions)} complete. Avg time: {avg_time:.2f}s, Estimated remaining: {remaining:.2f}s")
        
        total_time = time.time() - start_time
        logger.info(f"Batch generation complete. Total time: {total_time:.2f}s, Average per scene: {total_time/len(scene_descriptions):.2f}s")
        
        # Compile success/failure statistics
        successful = sum(1 for r in results if r["success"])
        logger.info(f"Generated {successful}/{len(scene_descriptions)} scenes successfully")
        
        return results
    
    def generate_video_scenes_from_lyrics(self, 
                                        lyrics: List[str],
                                        scene_count: int = None,
                                        model_type: str = "sdxl_turbo",
                                        aspect_ratio: str = "16:9",
                                        output_dir: str = "outputs/video",
                                        style: str = "cinematic") -> List[Dict[str, str]]:
        """
        Generate a sequence of scenes based on song lyrics.
        
        Args:
            lyrics: List of lyric lines
            scene_count: Number of scenes to generate (default: auto-determine)
            model_type: Model type to use
            aspect_ratio: Aspect ratio for the images
            output_dir: Directory to save the output images
            style: Visual style for the scenes
            
        Returns:
            List of results with scene info and image paths
        """
        import random
        from math import ceil
        
        # Determine number of scenes if not specified
        if scene_count is None:
            # Roughly one scene per 4-8 lines of lyrics
            scene_count = max(5, ceil(len(lyrics) / 6))  # At least 5 scenes
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Group lyrics into chunks for scene generation
        chunk_size = max(1, ceil(len(lyrics) / scene_count))
        lyric_chunks = [lyrics[i:i+chunk_size] for i in range(0, len(lyrics), chunk_size)]
        
        # Ensure we don't generate more scenes than requested
        lyric_chunks = lyric_chunks[:scene_count]
        
        # Prepare scene descriptions
        scene_descriptions = []
        
        for i, chunk in enumerate(lyric_chunks):
            # Join lyrics into a single string
            lyric_text = " ".join(chunk)
            
            # Create a scene description
            scene = {
                "scene_id": str(i+1),
                "lyrics": lyric_text,
                "description": f"{lyric_text}",  # Base description on lyrics
                "style": style
            }
            
            scene_descriptions.append(scene)
        
        # Now generate imagery for each scene
        logger.info(f"Generating {len(scene_descriptions)} scenes from lyrics with {model_type}")
        
        # Prepare for batch generation
        batch_scenes = []
        for scene in scene_descriptions:
            batch_scenes.append({
                "description": scene["description"],
                "style": scene["style"],
                "scene_id": scene["scene_id"]
            })
        
        # Generate all scenes
        scene_results = self.batch_generate_scenes(
            scene_descriptions=batch_scenes,
            model_type=model_type,
            aspect_ratio=aspect_ratio,
            output_dir=output_dir
        )
        
        # Combine results with original scene data
        final_results = []
        for i, result in enumerate(scene_results):
            scene_data = scene_descriptions[i].copy()
            scene_data.update(result)
            final_results.append(scene_data)
        
        return final_results


# Helper function to initialize the renderer
def initialize_fast_renderer(comfyui_url: str = None) -> FastRenderer:
    """
    Initialize the fast renderer system.
    
    Args:
        comfyui_url: URL of the ComfyUI server
        
    Returns:
        FastRenderer: Initialized renderer
    """
    # Create the renderer
    renderer = FastRenderer(comfyui_url=comfyui_url)
    
    # Test connection
    comfyui = renderer.comfyui
    connected, error = comfyui.check_connection()
    
    if not connected:
        raise ConnectionError(f"Cannot connect to ComfyUI server: {error}")
    
    # Ensure workflows exist
    renderer.ensure_default_workflows()
    
    return renderer


if __name__ == "__main__":
    # Example usage
    try:
        renderer = initialize_fast_renderer()
        
        # Test scene generation
        image_path, error = renderer.generate_scene(
            scene_description="A motorcycle courier in a red jacket speeding through neon-lit streets at night",
            model_type="sdxl_turbo",
            aspect_ratio="16:9",
            style="cyberpunk",
            output_dir="outputs/test"
        )
        
        if image_path:
            print(f"Generated scene image: {image_path}")
        else:
            print(f"Failed to generate scene: {error}")
            
    except Exception as e:
        print(f"Error in fast renderer: {str(e)}")
        import traceback
        print(traceback.format_exc())