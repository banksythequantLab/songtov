"""
Improved Update Workflow Function for ComfyUI Interface

This module provides an enhanced version of the update_workflow function
that properly handles node updates in ComfyUI workflows.
"""

import copy
import logging
from typing import Dict, Any, List, Union

# Configure logging
logger = logging.getLogger(__name__)

def improved_update_workflow(workflow: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced version of the update_workflow function with better node handling.
    
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
    
    # Collect information about nodes for better debugging
    node_types = {str(node["id"]): node["type"] for node in updated_workflow.get("nodes", [])}
    
    # Track which nodes and parameters were updated
    updated_nodes = set()
    
    for key, value in updates.items():
        try:
            # Parse the key into node_id and parameter
            if "." not in key:
                logger.warning(f"Invalid update key format: {key}. Expected format: 'node_id.parameter'")
                continue
                
            node_id, param = key.split(".", 1)
            
            # Convert node_id to string for matching
            node_id_str = str(node_id)
            
            # Log the node type we're looking for
            node_type = node_types.get(node_id_str, "Unknown")
            logger.debug(f"Looking for node {node_id_str} of type {node_type} to update parameter {param}")
            
            # Find the node with matching ID
            for node in updated_workflow.get("nodes", []):
                if str(node.get("id")) == node_id_str:
                    updated = False
                    node_type = node.get("type", "Unknown")
                    
                    # 1. Special handling for specific node types
                    if node_type == "CLIPTextEncode" and param == "text":
                        # For CLIPTextEncode, the text prompt is in widgets_values[0]
                        if "widgets_values" in node and len(node["widgets_values"]) > 0:
                            node["widgets_values"][0] = value
                            logger.debug(f"Updated {node_type} node {node_id} text prompt: {value}")
                            updated = True
                    
                    elif node_type == "EmptyLatentImage" and param in ["width", "height", "batch_size"]:
                        # For EmptyLatentImage, the dimensions are in widgets_values
                        if "widgets_values" in node:
                            if param == "width" and len(node["widgets_values"]) > 0:
                                node["widgets_values"][0] = value
                                updated = True
                            elif param == "height" and len(node["widgets_values"]) > 1:
                                node["widgets_values"][1] = value
                                updated = True
                            elif param == "batch_size" and len(node["widgets_values"]) > 2:
                                node["widgets_values"][2] = value
                                updated = True
                    
                    elif node_type == "SaveImage":
                        # For SaveImage, handle the common parameters
                        if "widgets_values" in node:
                            if param == "output_dir" and len(node["widgets_values"]) > 0:
                                node["widgets_values"][0] = value
                                updated = True
                            elif param == "filename_prefix" and len(node["widgets_values"]) > 1:
                                node["widgets_values"][1] = value
                                updated = True
                    
                    elif node_type == "CheckpointLoaderSimple" and param == "ckpt_name":
                        # For CheckpointLoaderSimple, the model name is in widgets_values[0]
                        if "widgets_values" in node and len(node["widgets_values"]) > 0:
                            node["widgets_values"][0] = value
                            updated = True
                    
                    # 2. Try to update in inputs if not already updated
                    if not updated and "inputs" in node:
                        # Find the input parameter by name
                        for input_param in node["inputs"]:
                            if input_param.get("name") == param:
                                input_param["value"] = value
                                updated = True
                                logger.debug(f"Updated {node_type} node {node_id} input parameter {param}: {value}")
                                break
                    
                    # 3. Try to find parameter index in widgets based on user-friendly name
                    if not updated and "widgets" in node and "widgets_values" in node:
                        # Try to find the parameter in widget definitions
                        for i, widget in enumerate(node.get("widgets", [])):
                            if widget.get("name") == param and i < len(node["widgets_values"]):
                                node["widgets_values"][i] = value
                                updated = True
                                logger.debug(f"Updated {node_type} node {node_id} widget {param}: {value}")
                                break
                    
                    # Log if we couldn't update the parameter
                    if not updated:
                        logger.warning(
                            f"Could not update parameter {param} in node {node_id} (type: {node_type}). "
                            f"Available node properties: {list(node.keys())}"
                        )
                        if "widgets_values" in node:
                            logger.warning(f"Node has {len(node['widgets_values'])} widget values")
                    else:
                        updated_nodes.add(node_id_str)
                    
                    # Break after processing the node
                    break
            else:
                # Node not found
                available_nodes = [str(n.get("id")) for n in updated_workflow.get("nodes", [])]
                logger.warning(
                    f"Node {node_id} not found in workflow. "
                    f"Available nodes: {available_nodes}"
                )
                
        except Exception as e:
            logger.error(f"Error updating parameter {key}: {str(e)}")
    
    logger.info(f"Updated {len(updated_nodes)} nodes in workflow")
    return updated_workflow
