#!/usr/bin/env python3
"""
MaiVid Studio - Convo Pilot Integration Test

This script tests the Convo Pilot API for video generation from a URL.
"""

import os
import sys
import json
import time
import requests
import argparse

# Default settings
DEFAULT_URL = "http://localhost:420"
DEFAULT_SUNO_URL = "https://suno.com/s/H6JQeAvqf4SgiFoF"  # Replace with a valid Suno URL


def test_create_video(base_url, suno_url, model_type="sdxl_turbo", style="cinematic"):
    """Test the create_video_from_url endpoint."""
    print(f"\n=== Testing create_video_from_url endpoint ===")
    
    # Create request data
    data = {
        "url": suno_url,
        "model_type": model_type,
        "style": style,
        "scene_count": 4,
        "transition_type": "fade",
        "transition_duration": 1.0
    }
    
    print(f"Request data: {json.dumps(data, indent=2)}")
    
    # Send request
    response = requests.post(f"{base_url}/api/convo_pilot/video", json=data)
    
    # Print response
    print(f"Status code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    
    # Check if successful
    if response.status_code == 202 and response.json().get("success", False):
        print("\nVideo generation job started successfully!")
        return response.json().get("job_id")
    else:
        print("\nFailed to start video generation job")
        return None


def monitor_job(base_url, job_id, interval=5, max_time=300):
    """Monitor a video generation job until completion or timeout."""
    print(f"\n=== Monitoring job {job_id} ===")
    
    # Start time
    start_time = time.time()
    
    # Monitor job
    while time.time() - start_time < max_time:
        # Get job status
        response = requests.get(f"{base_url}/api/convo_pilot/video/{job_id}")
        
        # Check if successful
        if response.status_code != 200:
            print(f"Error getting job status: {response.status_code}")
            print(f"Response: {response.text}")
            time.sleep(interval)
            continue
        
        # Get job status
        data = response.json()
        if not data.get("success", False):
            print(f"Error in response: {data}")
            time.sleep(interval)
            continue
        
        # Get job status
        job_status = data.get("job_status", {})
        status = job_status.get("status", "unknown")
        progress = job_status.get("overall_progress", 0)
        current_stage = job_status.get("current_stage", "unknown")
        
        # Print status
        print(f"Status: {status}, Progress: {progress:.1f}%, Stage: {current_stage}")
        
        # Check if job is complete
        if status == "completed":
            print("\nJob completed successfully!")
            print(f"Video path: {job_status.get('video_path', 'unknown')}")
            return True
        elif status == "failed":
            print("\nJob failed!")
            print(f"Error: {job_status.get('error', 'unknown')}")
            return False
        
        # Sleep
        time.sleep(interval)
    
    print("\nTimeout waiting for job completion")
    return False


def test_get_models(base_url):
    """Test the get_models endpoint."""
    print(f"\n=== Testing get_models endpoint ===")
    
    # Send request
    response = requests.get(f"{base_url}/api/convo_pilot/models")
    
    # Print response
    print(f"Status code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    
    # Check if successful
    if response.status_code == 200 and response.json().get("success", False):
        print("\nGot models successfully!")
        return response.json().get("models", [])
    else:
        print("\nFailed to get models")
        return []


def test_get_styles(base_url):
    """Test the get_styles endpoint."""
    print(f"\n=== Testing get_styles endpoint ===")
    
    # Send request
    response = requests.get(f"{base_url}/api/convo_pilot/styles")
    
    # Print response
    print(f"Status code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    
    # Check if successful
    if response.status_code == 200 and response.json().get("success", False):
        print("\nGot styles successfully!")
        return response.json().get("styles", [])
    else:
        print("\nFailed to get styles")
        return []


def main():
    """Main function."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Test the Convo Pilot API integration")
    parser.add_argument("--url", default=DEFAULT_URL, help="Base URL for the MaiVid Studio API")
    parser.add_argument("--suno-url", default=DEFAULT_SUNO_URL, help="Suno URL to use for testing")
    parser.add_argument("--model", default="sdxl_turbo", help="Model type to use for testing")
    parser.add_argument("--style", default="cinematic", help="Style to use for testing")
    parser.add_argument("--monitor", action="store_true", help="Monitor job after creation")
    parser.add_argument("--interval", type=int, default=5, help="Polling interval in seconds")
    parser.add_argument("--max-time", type=int, default=300, help="Maximum monitoring time in seconds")
    parser.add_argument("--test-models", action="store_true", help="Test get_models endpoint")
    parser.add_argument("--test-styles", action="store_true", help="Test get_styles endpoint")
    args = parser.parse_args()
    
    # Welcome message
    print(f"MaiVid Studio - Convo Pilot Integration Test")
    print(f"Base URL: {args.url}")
    print(f"Suno URL: {args.suno_url}")
    
    # Test endpoints based on arguments
    if args.test_models:
        test_get_models(args.url)
    
    if args.test_styles:
        test_get_styles(args.url)
    
    # Create video
    job_id = test_create_video(args.url, args.suno_url, args.model, args.style)
    
    # Monitor job if requested
    if args.monitor and job_id:
        monitor_job(args.url, job_id, args.interval, args.max_time)
    
    print("\nTest completed")


if __name__ == "__main__":
    main()
