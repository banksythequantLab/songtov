# MaiVid Studio - Convo Pilot Integration

This README documents the integration between MaiVid Studio and Convo Pilot, allowing for AI-driven video generation through Convo Pilot's conversational interface.

## Overview

The integration enables users to generate music videos directly from any URL (especially Suno music URLs) using Convo Pilot's natural language interface. Users can specify preferences for video style, scene count, and model type to customize their generated videos.

## API Endpoints

### 1. Create Video from URL

Start a new video generation job from a music URL.

**Endpoint**: `/api/convo_pilot/video`
**Method**: `POST`
**Content-Type**: `application/json`

**Request Body**:
```json
{
  "url": "https://suno.com/s/SONG_ID",
  "model_type": "sdxl_turbo",
  "aspect_ratio": "16:9",
  "style": "cinematic",
  "scene_count": 5,
  "transition_type": "fade",
  "transition_duration": 1.0
}
```

All parameters except `url` are optional and will use the defaults shown above if not provided.

**Response**: 
```json
{
  "success": true,
  "job_id": "job_20250516_123456_abcdef12",
  "message": "Video generation started with job ID: job_20250516_123456_abcdef12",
  "job_info": {
    "job_id": "job_20250516_123456_abcdef12",
    "status": "started",
    "url": "https://suno.com/s/SONG_ID",
    "creation_time": "20250516_123456",
    "settings": {
      "model_type": "sdxl_turbo",
      "aspect_ratio": "16:9",
      "style": "cinematic",
      "scene_count": 5,
      "transition_type": "fade",
      "transition_duration": 1.0
    }
  }
}
```

### 2. Get Video Job Status

Check the status of a video generation job.

**Endpoint**: `/api/convo_pilot/video/{job_id}`
**Method**: `GET`

**Response**:
```json
{
  "success": true,
  "job_status": {
    "job_id": "job_20250516_123456_abcdef12",
    "video_title": "Suno Song 1234abcd",
    "total_scenes": 5,
    "processed_scenes": 3,
    "current_stage": "Processing scene 3/5",
    "stage_name": "scene_generation",
    "stage_progress": 60.0,
    "overall_progress": 38.0,
    "status": "running",
    "started_at": 1747446242.891234,
    "updated_at": 1747446302.123456,
    "completed_at": null,
    "error": null
  }
}
```

### 3. Get Video Generation Progress

A simplified endpoint for tracking generation progress.

**Endpoint**: `/api/convo_pilot/video/progress/{job_id}`
**Method**: `GET`

**Response**:
```json
{
  "success": true,
  "progress": {
    "job_id": "job_20250516_123456_abcdef12",
    "overall_progress": 38.0,
    "status": "running",
    "current_stage": "Processing scene 3/5"
  }
}
```

### 4. Get Available Models

Retrieve a list of available AI models for video generation.

**Endpoint**: `/api/convo_pilot/models`
**Method**: `GET`

**Response**:
```json
{
  "success": true,
  "models": [
    {
      "id": "sdxl_turbo",
      "name": "SDXL Turbo",
      "description": "Fast generation with good quality",
      "speed": "Fast",
      "quality": "Good"
    },
    {
      "id": "sd3",
      "name": "Stable Diffusion 3",
      "description": "High quality generation, slower than Turbo",
      "speed": "Medium",
      "quality": "Excellent"
    },
    {
      "id": "flux",
      "name": "Flux",
      "description": "Balanced speed and quality",
      "speed": "Medium",
      "quality": "Very Good"
    }
  ]
}
```

### 5. Get Available Styles

Retrieve a list of available video styles.

**Endpoint**: `/api/convo_pilot/styles`
**Method**: `GET`

**Response**:
```json
{
  "success": true,
  "styles": [
    {
      "id": "cinematic",
      "name": "Cinematic",
      "description": "Professional movie-like style with dramatic lighting"
    },
    {
      "id": "anime",
      "name": "Anime",
      "description": "Japanese animation style"
    },
    // Additional styles...
  ]
}
```

## Workflow

1. User provides a music URL (e.g., from Suno) to Convo Pilot
2. Convo Pilot calls the `create_video_from_url` endpoint to start video generation
3. MaiVid Studio:
   - Downloads the audio from the URL
   - Extracts lyrics and metadata
   - Generates scene descriptions based on lyrics
   - Creates scene images using AI models
   - Renders scene videos with motion effects
   - Combines scenes with transitions
   - Adds audio to create the final video
4. Convo Pilot can track progress using the status endpoints
5. Once complete, Convo Pilot can inform the user of the generated video's location

## Example Usage

### Start a Video Generation Job

```bash
curl -X POST "http://localhost:420/api/convo_pilot/video" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://suno.com/s/H6JQeAvqf4SgiFoF",
    "style": "cyberpunk",
    "model_type": "sdxl_turbo",
    "scene_count": 6
  }'
```

### Check Job Status

```bash
curl -X GET "http://localhost:420/api/convo_pilot/video/job_20250516_123456_abcdef12"
```

## Technical Implementation

The integration is implemented using these key components:

1. **VideoGenerator class**: Orchestrates the video generation process from URL to final video
2. **Convo Pilot API Blueprint**: Flask routes for Convo Pilot integration
3. **Progress Tracker**: Monitors and provides updates on generation progress

## Troubleshooting

If you encounter issues with the integration:

1. Check the MaiVid Studio logs for errors
2. Verify ComfyUI is running and accessible
3. Ensure FFmpeg is installed and properly configured
4. Make sure the Suno URL is valid and accessible
5. Check disk space for storing temporary and output files
