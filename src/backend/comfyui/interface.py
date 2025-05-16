"""
MaiVid Studio - ComfyUI integration module

This module handles the communication with ComfyUI for image generation,
including workflow management, prompt creation, and result processing.

Functions:
    generate_scene: Generates a scene image based on description
    load_workflow: Loads a workflow from a JSON file
    update_workflow: Updates parameters in a workflow
    queue_prompt: Sends a prompt to ComfyUI for processing
    get_results: Gets the results of a queued prompt
"""

import os
import json
import time
import uuid
import requests
import logging
import base64
import copy
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default ComfyUI connection settings
DEFAULT_COMFYUI_URL = "http://127.0.0.1:8188"


class ComfyUIInterface:
    """Interface for communicating with ComfyUI."""
    
    def __init__(self, comfyui_url: str = DEFAULT_COMFYUI_URL):
        """
        Initialize the ComfyUI interface.
        
        Args:
            comfyui_url (str): URL of the ComfyUI server
        """
        self.comfyui_url = comfyui_url
        self.client_id = str(uuid.uuid4())
        logger.info(f"Initialized ComfyUI interface with client ID {self.client_id}")
        
    def check_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Check if ComfyUI server is available and responding.
        
        Returns:
            Tuple[bool, Optional[str]]: (connection_status, error_message)
        """
        try:
            # Try to hit the simple /system_stats endpoint which should always respond
            response = requests.get(f"{self.comfyui_url}/system_stats", timeout=5)
            response.raise_for_status()
            
            # If we get here, the connection is good
            logger.info("ComfyUI server is available and responding")
            return True, None
        except requests.exceptions.RequestException as e:
            error_msg = f"ComfyUI server is not available: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        
    def load_workflow(self, workflow_file: str) -> Dict[str, Any]:
        """
        Load a workflow from a JSON file.
        
        Args:
            workflow_file (str): Path to the workflow JSON file
            
        Returns:
            Dict: The loaded workflow
        """
        try:
            with open(workflow_file, 'r') as f:
                workflow = json.load(f)
            logger.info(f"Loaded workflow from {workflow_file}")
            return workflow
        except Exception as e:
            logger.error(f"Failed to load workflow from {workflow_file}: {str(e)}")
            raise
            
    def update_workflow(self, workflow: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update parameters in a workflow.
        
        Args:
            workflow (Dict): The workflow to update
            updates (Dict): Dictionary of updates to apply
                Format: {
                    "node_id.parameter": value,
                    ...
                }
                
        Returns:
            Dict: The updated workflow
        """
        updated_workflow = copy.deepcopy(workflow)
        
        for key, value in updates.items():
            try:
                node_id, param = key.split('.')
                
                # Convert node_id to string for matching
                node_id_str = str(node_id)
                
                # Find the node with matching ID
                for node in updated_workflow.get("nodes", []):
                    if str(node.get("id")) == node_id_str:
                        # Check for parameters in various locations
                        # 1. Check in inputs
                        if "inputs" in node and param in node["inputs"]:
                            node["inputs"][param] = value
                            logger.debug(f"Updated node {node_id} parameter {param} to {value}")
                        # 2. Check in widgets_values (for some node types)
                        elif "widgets_values" in node:
                            # Find the parameter index in widgets
                            param_index = None
                            if "inputs" in node:
                                for i, input_param in enumerate(node["inputs"]):
                                    if input_param.get("name") == param:
                                        param_index = i
                                        break
                            
                            if param_index is not None and param_index < len(node["widgets_values"]):
                                node["widgets_values"][param_index] = value
                                logger.debug(f"Updated node {node_id} widget value {param} at index {param_index} to {value}")
                            else:
                                # Special handling for specific node types
                                # For CLIPTextEncode nodes, the first widget value is typically the text
                                if node.get("type") == "CLIPTextEncode" and param == "text" and len(node["widgets_values"]) > 0:
                                    node["widgets_values"][0] = value
                                    logger.debug(f"Updated CLIPTextEncode node {node_id} text to {value}")
                                # For SaveImage nodes, handle common parameters
                                elif node.get("type") == "SaveImage":
                                    if param == "filename_prefix" and len(node["widgets_values"]) > 1:
                                        node["widgets_values"][1] = value
                                        logger.debug(f"Updated SaveImage node {node_id} filename_prefix to {value}")
                                    elif param == "output_dir" and len(node["widgets_values"]) > 0:
                                        node["widgets_values"][0] = value
                                        logger.debug(f"Updated SaveImage node {node_id} output_dir to {value}")
                                else:
                                    logger.warning(f"Parameter {param} not found in node {node_id} widgets, or index mismatch")
                        else:
                            logger.warning(f"Parameter {param} not found in node {node_id}")
                        
                        # We found and processed the node, break the loop
                        break
                else:
                    # Node not found (the for-else construct in Python)
                    logger.warning(f"Node {node_id} not found in workflow")
            except Exception as e:
                logger.error(f"Error updating parameter {key}: {str(e)}")
                
        return updated_workflow
    
    def queue_prompt(self, prompt: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """
        Queue a prompt for processing by ComfyUI.
        
        Args:
            prompt (Dict): The prompt to queue
            
        Returns:
            Tuple: (prompt_id, error_message)
        """
        try:
            p = {"prompt": prompt, "client_id": self.client_id}
            logger.debug(f"Sending prompt to ComfyUI: {json.dumps(p, indent=2)}")
            
            response = requests.post(f"{self.comfyui_url}/prompt", json=p)
            
            if response.status_code != 200:
                error_msg = f"Failed to queue prompt. Status code: {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg += f", Error: {error_data['error']}"
                    if 'node_errors' in error_data:
                        error_msg += f", Node Errors: {error_data['node_errors']}"
                except:
                    error_msg += f", Response: {response.text[:200]}"
                
                logger.error(error_msg)
                return None, error_msg
            
            try:
                response_data = response.json()
                prompt_id = response_data.get("prompt_id")
                if not prompt_id:
                    logger.error(f"No prompt_id in response: {response_data}")
                    return None, "No prompt_id in response"
                
                logger.info(f"Queued prompt with ID {prompt_id}")
                return prompt_id, None
            except Exception as parse_error:
                error_msg = f"Failed to parse response: {str(parse_error)}, Response: {response.text[:200]}"
                logger.error(error_msg)
                return None, error_msg
            
        except Exception as e:
            error_msg = f"Failed to queue prompt: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
            
    def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """
        Get the history for a prompt.
        
        Args:
            prompt_id (str): The ID of the prompt
            
        Returns:
            Dict: The prompt history
        """
        try:
            response = requests.get(f"{self.comfyui_url}/history/{prompt_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get history for prompt {prompt_id}: {str(e)}")
            return {}
            
    def get_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> Optional[bytes]:
        """
        Get an image from ComfyUI.
        
        Args:
            filename (str): Name of the image file
            subfolder (str): Subfolder within the main folder
            folder_type (str): Type of folder (output, input, temp)
            
        Returns:
            Optional[bytes]: The image data
        """
        try:
            url = f"{self.comfyui_url}/view"
            params = {
                "filename": filename,
                "subfolder": subfolder,
                "type": folder_type
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.content
            
        except Exception as e:
            logger.error(f"Failed to get image {filename}: {str(e)}")
            return None
            
    def wait_for_prompt(self, prompt_id: str, timeout: int = 300, check_interval: int = 1) -> Tuple[bool, Dict[str, Any]]:
        """
        Wait for a prompt to complete.
        
        Args:
            prompt_id (str): The ID of the prompt
            timeout (int): Maximum time to wait in seconds
            check_interval (int): Time between checks in seconds
            
        Returns:
            Tuple: (success, result)
        """
        logger.info(f"Waiting for prompt {prompt_id} to complete")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check the execution status
                status_response = requests.get(f"{self.comfyui_url}/prompt/status")
                if status_response.status_code != 200:
                    logger.warning(f"Error getting status: {status_response.status_code}, retrying...")
                    time.sleep(check_interval)
                    continue
                
                status_data = status_response.json()
                
                # Check if execution has failed
                if "error" in status_data:
                    error_msg = f"Prompt {prompt_id} failed: {status_data['error']}"
                    logger.error(error_msg)
                    return False, {"error": status_data["error"]}
                
                # Check if the prompt is still being executed
                if status_data.get("executing", {}).get("prompt_id") == prompt_id:
                    logger.debug(f"Prompt {prompt_id} is still executing...")
                    # Still executing, wait and check again
                    time.sleep(check_interval)
                    continue
                
                # Check if the prompt is in the history (which means it's completed)
                history = self.get_history(prompt_id)
                
                if prompt_id in history:
                    # Extract outputs
                    outputs = self.get_prompt_outputs(history, prompt_id)
                    if outputs:
                        logger.info(f"Prompt {prompt_id} completed successfully")
                        return True, outputs
                
                # If prompt is not being executed and not in history yet, it might be queued
                if status_data.get("pending", {}).get("prompt_id") == prompt_id:
                    logger.debug(f"Prompt {prompt_id} is queued, waiting...")
                    time.sleep(check_interval)
                    continue
                
                # If the prompt is neither being executed, nor in history, nor queued, it might be completed
                # but we missed it in history, or it might have failed. Let's check history again.
                if prompt_id not in history:
                    # Not found in history, so let's check one more time
                    time.sleep(check_interval * 2)  # Wait a bit longer
                    history = self.get_history(prompt_id)
                    
                    if prompt_id in history:
                        outputs = self.get_prompt_outputs(history, prompt_id)
                        if outputs:
                            logger.info(f"Prompt {prompt_id} completed successfully")
                            return True, outputs
                    
                    # If still not found, it might have failed silently
                    logger.warning(f"Prompt {prompt_id} not found in execution or history, it may have failed silently")
                
            except Exception as e:
                logger.error(f"Error checking prompt status: {str(e)}")
            
            # Wait before checking again
            time.sleep(check_interval)
        
        logger.error(f"Timeout waiting for prompt {prompt_id}")
        return False, {"error": "Timeout waiting for prompt to complete"}

    
    def get_prompt_outputs(self, history: Dict[str, Any], prompt_id: str) -> Dict[str, Any]:
        """
        Extract outputs from prompt history.
        
        Args:
            history (Dict): The prompt history
            prompt_id (str): The ID of the prompt
            
        Returns:
            Dict: The extracted outputs
        """
        outputs = {}
        
        if prompt_id in history:
            prompt_data = history[prompt_id]
            
            if "outputs" in prompt_data:
                for node_id, node_outputs in prompt_data["outputs"].items():
                    for output_name, output_data in node_outputs.items():
                        if isinstance(output_data, list) and len(output_data) > 0:
                            # Handle image outputs
                            if output_data[0].get("type") == "image":
                                image_data = output_data[0]
                                outputs[f"{node_id}_{output_name}"] = {
                                    "type": "image",
                                    "filename": image_data.get("filename", ""),
                                    "subfolder": image_data.get("subfolder", ""),
                                }
                            # Handle other output types as needed
                            else:
                                outputs[f"{node_id}_{output_name}"] = {
                                    "type": output_data[0].get("type", "unknown"),
                                    "data": output_data
                                }
        
        return outputs
    
    def download_output_images(self, outputs: Dict[str, Any], output_dir: str) -> Dict[str, str]:
        """
        Download output images from ComfyUI.
        
        Args:
            outputs (Dict): Output data from get_prompt_outputs
            output_dir (str): Directory to save images to
            
        Returns:
            Dict: Mapping of output keys to local file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        result = {}
        
        for key, output in outputs.items():
            if output.get("type") == "image":
                filename = output.get("filename", "")
                subfolder = output.get("subfolder", "")
                
                if filename:
                    image_data = self.get_image(filename, subfolder)
                    
                    if image_data:
                        # Create a local path for the image
                        local_filename = f"{key}_{filename}"
                        local_path = os.path.join(output_dir, local_filename)
                        
                        # Save the image
                        with open(local_path, "wb") as f:
                            f.write(image_data)
                            
                        logger.info(f"Saved image to {local_path}")
                        result[key] = local_path
                    else:
                        logger.warning(f"Failed to download image {filename}")
        
        return result
    
    def generate_scene(self, 
                       workflow_file: str, 
                       scene_description: str, 
                       style: str = "cinematic", 
                       output_dir: str = "outputs/scenes") -> Tuple[Optional[str], Optional[str]]:
        """
        Generate a scene image based on description.
        
        Args:
            workflow_file (str): Path to the workflow JSON file
            scene_description (str): Description of the scene to generate
            style (str): Style of the image to generate
            output_dir (str): Directory to save the output image
            
        Returns:
            Tuple: (path_to_generated_image, error_message)
        """
        try:
            # Verify ComfyUI connection
            connected, error = self.check_connection()
            if not connected:
                return None, f"ComfyUI server is not available: {error}"
                
            # Make sure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Load the workflow
            workflow = self.load_workflow(workflow_file)
            
            # Update the workflow with the scene description and style
            # Create a prompt that includes the scene description and style
            prompt = f"{scene_description}, {style} style, high quality, detailed"
            
            # Find the text prompt node (looking for CLIPTextEncode nodes)
            text_node_id = None
            save_node_id = None
            
            for node in workflow["nodes"]:
                # Look for text input nodes (positive prompt)
                if node["type"] == "CLIPTextEncode":
                    # Check if this might be a positive prompt node (avoiding negative prompts)
                    if "inputs" in node and "text" in node["inputs"]:
                        input_text = node["inputs"]["text"]
                        if input_text and isinstance(input_text, str):
                            if not any(neg_word in input_text.lower() for neg_word in ["negative", "bad", "ugly", "low quality"]):
                                text_node_id = str(node["id"])
                                break
                    # Also check widgets_values
                    elif "widgets_values" in node and len(node["widgets_values"]) > 0:
                        if isinstance(node["widgets_values"][0], str):
                            if not any(neg_word in node["widgets_values"][0].lower() for neg_word in ["negative", "bad", "ugly", "low quality"]):
                                text_node_id = str(node["id"])
                                break
                
                # Find SaveImage node
                if node["type"] == "SaveImage":
                    save_node_id = str(node["id"])
            
            # Generate a unique ID for the output image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            output_name = f"scene_{timestamp}_{unique_id}"
            
            # Create parameter updates
            updates = {}
            
            # Update the text prompt if found
            if text_node_id:
                updates[f"{text_node_id}.text"] = prompt
            else:
                # If no suitable text node found, log a warning
                logger.warning("No suitable text input node found in workflow, looking for any input node")
                
                # Last resort: Try any node with a text input
                for node in workflow["nodes"]:
                    if "inputs" in node and "text" in node["inputs"]:
                        text_node_id = str(node["id"])
                        updates[f"{text_node_id}.text"] = prompt
                        logger.warning(f"Using node {text_node_id} for text input as fallback")
                        break
            
            # If we still don't have a node to update, return error
            if not updates:
                logger.error("No text input node found in workflow")
                return None, "Could not find text input node in workflow"
            
            # Update SaveImage node if found
            if save_node_id:
                updates[f"{save_node_id}.filename_prefix"] = output_name
                updates[f"{save_node_id}.output_dir"] = output_dir
            
            # Apply updates to workflow
            logger.info(f"Updating workflow with: {updates}")
            updated_workflow = self.update_workflow(workflow, updates)
            
            # Add a random seed to the KSampler node if present
            for node in updated_workflow["nodes"]:
                if node["type"] == "KSampler" and "widgets_values" in node and len(node["widgets_values"]) > 0:
                    # First parameter should be the seed
                    import random
                    node["widgets_values"][0] = random.randint(0, 9999999999)
                    logger.debug(f"Set random seed for KSampler: {node['widgets_values'][0]}")
            
            # Queue the prompt
            logger.info("Queueing updated workflow")
            prompt_id, error = self.queue_prompt(updated_workflow)
            
            if error:
                logger.error(f"Failed to queue prompt: {error}")
                return None, error
            
            logger.info(f"Workflow queued with prompt ID: {prompt_id}")
                
            # Wait for the prompt to complete
            success, result = self.wait_for_prompt(prompt_id)
            
            if not success:
                error_message = result.get("error", "Unknown error")
                logger.error(f"Error processing prompt: {error_message}")
                return None, error_message
            
            logger.info("Prompt processed successfully, checking for image outputs")
                
            # Download the output images
            image_paths = self.download_output_images(result, output_dir)
            
            if image_paths:
                # Return the path to the first image
                first_image_path = next(iter(image_paths.values()))
                
                # Log the successful generation
                logger.info(f"Generated scene image: {first_image_path}")
                
                # Check if the file actually exists
                if not os.path.exists(first_image_path):
                    logger.error(f"Generated image file does not exist: {first_image_path}")
                    return None, f"Generated image file does not exist: {first_image_path}"
                    
                return first_image_path, None
            else:
                logger.warning("No images were found in the prompt output, checking for files matching the output name")
                # Check if there are any files in the output directory matching our naming pattern
                # This is a fallback in case download_output_images didn't work correctly
                output_files = [f for f in os.listdir(output_dir) if f.startswith(output_name) and f.endswith((".png", ".jpg", ".jpeg"))]
                if output_files:
                    first_image_path = os.path.join(output_dir, output_files[0])
                    logger.info(f"Found generated scene image through fallback: {first_image_path}")
                    return first_image_path, None
                
                logger.error("No image outputs found in prompt result or directory")
                return None, "No images were generated"
                
        except Exception as e:
            error_msg = f"Failed to generate scene: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            return None, error_msg


# Example usage
if __name__ == "__main__":
    # Initialize the ComfyUI interface
    comfyui = ComfyUIInterface()
    
    # Path to a workflow file
    workflow_file = "workflows/scene_generation.json"
    
    # Generate a scene
    image_path, error = comfyui.generate_scene(
        workflow_file=workflow_file,
        scene_description="A beautiful sunset over a calm ocean with sailboats on the horizon",
        style="cinematic",
        output_dir="outputs/scenes"
    )
    
    if image_path:
        print(f"Generated scene image: {image_path}")
    else:
        print(f"Failed to generate scene: {error}")
