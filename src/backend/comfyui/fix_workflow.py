"""
Fix ComfyUI Workflow JSON

This script fixes the ComfyUI workflow JSON file to ensure proper node connections
and structure. It addresses the Node ID '#id' error by ensuring all node IDs 
referenced in links are properly defined in the nodes array.
"""

import json
import os
import sys
from pathlib import Path

def fix_workflow_file(input_file, output_file):
    """
    Fix ComfyUI workflow JSON file to ensure proper node structure and connections.
    
    Args:
        input_file (str): Path to the input workflow file
        output_file (str): Path to save the fixed workflow file
    """
    try:
        # Load the original workflow
        with open(input_file, 'r') as f:
            workflow = json.load(f)
        
        # Check if the workflow has a PreviewImage node (ID 25)
        preview_node_exists = any(node.get('id') == 25 for node in workflow.get('nodes', []))
        
        # If the PreviewImage node doesn't exist, add it
        if not preview_node_exists:
            preview_node = {
                "id": 25,
                "type": "PreviewImage",
                "pos": [1450, -150],
                "size": [360, 400],
                "flags": {},
                "order": 9,
                "mode": 0,
                "inputs": [
                    {
                        "name": "images",
                        "type": "IMAGE",
                        "link": 53
                    }
                ],
                "outputs": [],
                "properties": {
                    "cnr_id": "comfy-core",
                    "ver": "0.3.33",
                    "Node name for S&R": "PreviewImage",
                    "widget_ue_connectable": {}
                },
                "widgets_values": []
            }
            workflow['nodes'].append(preview_node)
            
            # Ensure the link from VAEDecode to PreviewImage exists
            # First, find if link 53 exists
            link_53_exists = any(link[0] == 53 for link in workflow.get('links', []))
            
            # If link 53 doesn't exist, add it
            if not link_53_exists:
                # Find the VAEDecode node ID (typically 8)
                vae_decode_node_id = None
                for node in workflow.get('nodes', []):
                    if node.get('type') == 'VAEDecode':
                        vae_decode_node_id = node.get('id')
                        break
                
                if vae_decode_node_id is not None:
                    # Add link 53 connecting VAEDecode output to PreviewImage input
                    link_53 = [53, vae_decode_node_id, 0, 25, 0, "IMAGE"]
                    workflow['links'].append(link_53)
        
        # Ensure proper order values for all nodes
        node_order = 0
        for node in workflow.get('nodes', []):
            if 'order' not in node:
                node['order'] = node_order
                node_order += 1
                
        # Verify all links reference nodes that exist
        node_ids = [node.get('id') for node in workflow.get('nodes', [])]
        valid_links = []
        
        for link in workflow.get('links', []):
            # Link format: [link_id, origin_node_id, origin_slot, target_node_id, target_slot, type]
            if len(link) >= 6:
                link_id, origin_node_id, origin_slot, target_node_id, target_slot, link_type = link
                
                # Check if both origin and target nodes exist
                if origin_node_id in node_ids and target_node_id in node_ids:
                    valid_links.append(link)
                else:
                    print(f"Warning: Link {link_id} references non-existent node(s): {origin_node_id} -> {target_node_id}")
        
        # Replace links with valid ones
        workflow['links'] = valid_links
        
        # Save the fixed workflow
        with open(output_file, 'w') as f:
            json.dump(workflow, f, indent=2)
            
        print(f"Successfully fixed workflow file: {output_file}")
        return True
        
    except Exception as e:
        print(f"Error fixing workflow file: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python fix_workflow.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    fix_workflow_file(input_file, output_file)
