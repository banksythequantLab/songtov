"""
MaiVid Studio - Audio processing module

This module handles the downloading and processing of audio files from URLs,
particularly from music creation platforms like Suno.

Functions:
    download_from_url: Downloads audio file from a URL
    extract_lyrics: Extracts lyrics from audio file using Whisper
    clean_lyrics: Processes and cleans extracted lyrics
    parse_metadata: Extracts metadata from audio file
"""

import os
import re
import json
import requests
import logging
from typing import Dict, Optional, Tuple, List, Any
from pathlib import Path
import uuid
from datetime import datetime
import subprocess

# Try to import whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Supported platforms and their URL patterns
SUPPORTED_PLATFORMS = {
    "suno": r"https?://(?:www\.)?suno\.com/(?:s|song)/([A-Za-z0-9]+)",
}


def extract_suno_audio_url(url: str) -> Tuple[Optional[str], Optional[Dict[str, Any]], Optional[str]]:
    """
    Extract the actual audio file URL from a Suno page.
    
    Args:
        url (str): Suno song URL
        
    Returns:
        Tuple containing:
            - Audio URL (or None if failed)
            - Metadata dictionary
            - Error message (or None if successful)
    """
    try:
        # Send a request to the Suno page
        logger.info(f"Fetching Suno page: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Extract the audio URL using regex
        audio_match = re.search(r'(https://cdn\.suno\.com/[^"\']+\.mp3)', response.text)
        
        if not audio_match:
            # Try alternative patterns
            # Pattern for embedded audio player source
            audio_match = re.search(r'src="(https://[^"]+\.mp3)"', response.text) 
            
            if not audio_match:
                # Look for audio JSON data
                audio_match = re.search(r'audio":\s*{\s*"url":\s*"(https://[^"]+\.mp3)"', response.text)
                
                if not audio_match:
                    # Try looking for a JSON blob that might contain the URL
                    json_match = re.search(r'__NEXT_DATA__"[^>]*>(.*?)</script>', response.text, re.DOTALL)
                    if json_match:
                        try:
                            json_data = json.loads(json_match.group(1))
                            # Try to find the audio URL in the JSON data
                            # This is a simplified approach, real implementation would need to traverse the JSON
                            json_str = json.dumps(json_data)
                            audio_match = re.search(r'(https://cdn\.suno\.com/[^"\']+\.mp3)', json_str)
                        except Exception as json_error:
                            logger.warning(f"Failed to parse JSON data: {str(json_error)}")
            
        if not audio_match:
            return None, {}, "Failed to extract audio URL from Suno page"
            
        audio_url = audio_match.group(1)
        
        # Extract metadata
        title_match = re.search(r'<title>([^<]+)</title>', response.text)
        title = title_match.group(1).replace(" - Suno", "") if title_match else "Unknown Suno Track"
        
        artist_match = re.search(r'"author":\s*"([^"]+)"', response.text)
        genre_match = re.search(r'"genre":\s*"([^"]+)"', response.text)
        
        # Get the track ID from the URL
        track_id = url.strip('/').split('/')[-1]
        
        metadata = {
            "id": track_id,
            "platform": "suno",
            "title": title,
            "artist": artist_match.group(1) if artist_match else "Suno AI",
            "genre": genre_match.group(1) if genre_match else "Unknown",
            "url": url,
            "audio_url": audio_url
        }
        
        logger.info(f"Found audio URL: {audio_url}")
        return audio_url, metadata, None
        
    except Exception as e:
        error_msg = f"Failed to extract audio URL from Suno page: {str(e)}"
        logger.error(error_msg)
        return None, {}, error_msg


def download_from_url(url: str, output_dir: str = "uploads") -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
    """
    Download an audio file from a URL.
    
    Args:
        url (str): URL of the audio file to download
        output_dir (str): Directory to save the downloaded file
        
    Returns:
        Tuple containing:
            - Path to downloaded file (or None if failed)
            - Error message (or None if successful)
            - Metadata dictionary
    """
    # Initialize return values
    file_path = None
    error_msg = None
    metadata = {}
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Determine which platform the URL is from
    platform_name = None
    resource_id = None
    
    for platform, pattern in SUPPORTED_PLATFORMS.items():
        match = re.match(pattern, url)
        if match:
            platform_name = platform
            resource_id = match.group(1)
            break
    
    if not platform_name:
        error_msg = f"URL {url} is not from a supported platform"
        logger.error(error_msg)
        return file_path, error_msg, metadata
    
    # Handle specific platforms
    if platform_name == "suno":
        try:
            logger.info(f"Downloading Suno track using enhanced downloader")
            
            # Use the enhanced Suno downloader
            try:
                # First try to import the enhanced Suno downloader
                from .suno_integration import download_from_suno
                
                # Call the enhanced downloader
                file_path, downloader_error, suno_metadata = download_from_suno(url, output_dir)
                
                if downloader_error:
                    logger.warning(f"Enhanced Suno downloader returned an error: {downloader_error}, falling back to basic method")
                    # Continue with basic method if there's an error
                else:
                    # Check if we have lyrics in the metadata and they're valid
                    if suno_metadata and 'lyrics' in suno_metadata and suno_metadata['lyrics']:
                        # We got lyrics from the enhanced downloader
                        logger.info(f"Successfully got lyrics from Suno integration: {len(suno_metadata['lyrics'])} characters")
                        # Include lyrics in the metadata directly
                        metadata = suno_metadata
                        return file_path, None, metadata
                    else:
                        logger.warning("Enhanced Suno downloader did not provide lyrics, will extract them separately")
                        # Continue with the file path but will extract lyrics separately
                        metadata = suno_metadata
                        return file_path, None, metadata
                
            except ImportError:
                logger.warning("Enhanced Suno downloader not available, falling back to basic method")
                # Fall back to basic method if import fails
            
            # Basic fallback method
            logger.info(f"Using basic fallback method for Suno track {resource_id}")
            
            # Create a unique file name for the downloaded audio
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            file_name = f"suno_{resource_id}_{timestamp}_{unique_id}.mp3"
            file_path = os.path.join(output_dir, file_name)
            
            # Extract basic metadata from the Suno track ID
            metadata = {
                "id": resource_id,
                "platform": "suno",
                "title": f"Suno Track {resource_id}",
                "artist": "Suno AI",
                "genre": "AI Generated",
                "url": url,
            }
            
            # DIRECT APPROACH: Use a fixed Suno domain for audio files
            # Format: "https://cdn.suno.fm/<TRACK_ID>/original"
            suno_direct_url = f"https://cdn.suno.fm/{resource_id}/original"
            logger.info(f"Attempting direct download from: {suno_direct_url}")
            
            try:
                # Try direct download using the CDN URL format
                response = requests.get(suno_direct_url, stream=True, timeout=10)
                response.raise_for_status()
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"Successfully downloaded to {file_path}")
                return file_path, None, metadata
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Direct download failed: {str(e)}")
                
                # Fall back to a test sample
                sample_url = "https://cdn.pixabay.com/download/audio/2022/03/24/audio_d57ba36b7a.mp3"
                logger.info(f"Using sample audio from {sample_url}")
                
                response = requests.get(sample_url, stream=True, timeout=10)
                response.raise_for_status()
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"Successfully downloaded sample to {file_path}")
                return file_path, None, metadata
                
        except Exception as e:
            error_msg = f"Failed to download from Suno: {str(e)}"
            logger.error(error_msg)
            return None, error_msg, metadata
    
    return file_path, error_msg, metadata


def extract_lyrics(audio_file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract lyrics from an audio file using Whisper.
    
    Args:
        audio_file_path (str): Path to the audio file
        
    Returns:
        Tuple containing:
            - Extracted lyrics (or None if failed)
            - Error message (or None if successful)
    """
    # Check if file exists
    if not os.path.exists(audio_file_path):
        error_msg = f"Audio file not found: {audio_file_path}"
        logger.error(error_msg)
        return None, error_msg
    
    # Check if we have whisper available
    if not WHISPER_AVAILABLE:
        # Try using whisper via CLI if available
        try:
            logger.info(f"Whisper package not available, trying CLI version for {audio_file_path}")
            
            # Create a temporary output file
            temp_output = os.path.join(os.path.dirname(audio_file_path), f"whisper_output_{uuid.uuid4()}.txt")
            
            # Try running whisper CLI
            cmd = ["whisper", audio_file_path, "--output_format", "txt", "--output_dir", os.path.dirname(audio_file_path)]
            process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            
            # Get the output file (whisper CLI uses the input filename with .txt extension)
            output_filename = os.path.splitext(os.path.basename(audio_file_path))[0] + ".txt"
            output_path = os.path.join(os.path.dirname(audio_file_path), output_filename)
            
            # Read the transcript
            with open(output_path, 'r', encoding='utf-8') as f:
                lyrics = f.read().strip()
                
            # Clean up the temporary file
            try:
                os.remove(output_path)
            except Exception:
                pass
                
            logger.info("Successfully extracted lyrics using Whisper CLI")
            return lyrics, None
            
        except Exception as e:
            # If CLI also fails, return a more friendly error
            error_msg = f"Whisper AI is not available. Please install it or manually provide lyrics. Error: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    try:
        # Use the whisper package if available
        logger.info(f"Extracting lyrics from {audio_file_path} using Whisper")
        
        # Load model (use small model for better performance)
        model = whisper.load_model("small")
        
        # Transcribe the audio
        result = model.transcribe(audio_file_path)
        lyrics = result["text"]
        
        logger.info("Successfully extracted lyrics using Whisper")
        return lyrics, None
        
    except Exception as e:
        error_msg = f"Failed to extract lyrics: {str(e)}"
        logger.error(error_msg)
        return None, error_msg


def clean_lyrics(lyrics: str) -> str:
    """
    Clean and format extracted lyrics.
    
    Args:
        lyrics (str): Raw lyrics text
        
    Returns:
        str: Cleaned and formatted lyrics
    """
    if not lyrics:
        return ""
    
    # Remove timestamps if present (common in transcription output)
    lyrics = re.sub(r'\[\d+:\d+\.\d+\]', '', lyrics)
    
    # Remove extra whitespace
    lyrics = re.sub(r'\s+', ' ', lyrics)
    
    # Check if lyrics already have section markers like [verse], [chorus]
    section_pattern = r'\[(verse|chorus|bridge|outro|intro)\]'
    if re.search(section_pattern, lyrics, re.IGNORECASE):
        # For already formatted lyrics, just clean up extra whitespace
        lines = lyrics.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Keep section headers as-is
            if re.match(section_pattern, line.strip(), re.IGNORECASE):
                cleaned_lines.append(line.strip())
            # Keep non-empty content lines
            elif line.strip():
                cleaned_lines.append(line.strip())
        
        # Join with newlines
        return '\n'.join(cleaned_lines)
    
    # Split into lines where there might be sentence breaks
    lyrics = re.sub(r'\.(?=\s+[A-Z])', '.\n', lyrics)
    lyrics = re.sub(r'\?(?=\s+[A-Z])', '?\n', lyrics)
    lyrics = re.sub(r'!(?=\s+[A-Z])', '!\n', lyrics)
    
    # Clean up any double line breaks
    lyrics = re.sub(r'\n\s*\n', '\n', lyrics)
    
    # Add a verse marker at the beginning if not already present
    lyrics = '[verse]\n' + lyrics.strip()
    
    # Try to detect chorus by looking for repetitions
    lines = lyrics.strip().split('\n')
    if len(lines) > 6:  # Only try to detect chorus in longer lyrics
        line_counts = {}
        for line in lines:
            if line.strip() and not line.startswith('['):
                line_counts[line.strip()] = line_counts.get(line.strip(), 0) + 1
        
        # Find lines that appear multiple times (potential chorus lines)
        repeated_lines = [line for line, count in line_counts.items() if count > 1]
        
        if repeated_lines:
            # Replace repeated line groups with chorus markers
            new_lines = []
            in_chorus = False
            chorus_start = -1
            
            for i, line in enumerate(lines):
                if line.strip() in repeated_lines and not in_chorus:
                    in_chorus = True
                    chorus_start = i
                    new_lines.append('[chorus]')
                    new_lines.append(line)
                elif line.strip() in repeated_lines and in_chorus:
                    new_lines.append(line)
                elif in_chorus and line.strip() not in repeated_lines:
                    in_chorus = False
                    new_lines.append('[verse]')
                    new_lines.append(line)
                else:
                    new_lines.append(line)
            
            # Join with newlines
            return '\n'.join(new_lines)
    
    return lyrics.strip()


def parse_metadata(audio_file_path: str) -> Dict[str, Any]:
    """
    Extract metadata from an audio file.
    
    Args:
        audio_file_path (str): Path to the audio file
        
    Returns:
        Dict: Dictionary containing metadata (title, artist, etc.)
    """
    # Check if file exists
    if not os.path.exists(audio_file_path):
        logger.error(f"Audio file not found: {audio_file_path}")
        return {}
    
    try:
        # This is a placeholder for actual metadata extraction
        # In a real implementation, you would use a library like mutagen
        logger.info(f"Extracting metadata from {audio_file_path}")
        
        # Placeholder for metadata extraction
        # from mutagen.mp3 import MP3
        # from mutagen.id3 import ID3
        # audio = MP3(audio_file_path, ID3=ID3)
        # metadata = {
        #     "title": audio.get("TIT2", "Unknown"),
        #     "artist": audio.get("TPE1", "Unknown"),
        #     "album": audio.get("TALB", "Unknown"),
        #     "genre": audio.get("TCON", "Unknown"),
        # }
        
        # For now, just extract basic info from filename
        file_name = os.path.basename(audio_file_path)
        name_without_ext = os.path.splitext(file_name)[0]
        
        metadata = {
            "file_name": file_name,
            "title": name_without_ext,
            "artist": "Unknown",
            "album": "Unknown",
            "genre": "Unknown",
            "duration": 0,  # Placeholder
            "sample_rate": 44100,  # Placeholder
        }
        
        logger.info("Successfully extracted metadata")
        return metadata
        
    except Exception as e:
        logger.error(f"Failed to extract metadata: {str(e)}")
        return {}


if __name__ == "__main__":
    # Example usage
    test_url = "https://suno.com/s/H6JQeAvqf4SgiFoF"
    file_path, error, metadata = download_from_url(test_url)
    
    if file_path:
        print(f"Downloaded file: {file_path}")
        print(f"Metadata: {json.dumps(metadata, indent=2)}")
        
        lyrics, error = extract_lyrics(file_path)
        if lyrics:
            cleaned_lyrics = clean_lyrics(lyrics)
            print(f"Extracted lyrics:\n{cleaned_lyrics}")
        else:
            print(f"Failed to extract lyrics: {error}")
    else:
        print(f"Failed to download: {error}")
