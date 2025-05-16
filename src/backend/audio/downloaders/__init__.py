"""
MaiVid Studio - Audio Downloaders Package

This package contains specialized downloaders for various audio platforms used by MaiVid Studio.
"""

# Make the download function available at the package level
from .suno_downloader import download_suno_song, generate_scenes_from_lyrics, generate_default_scenes
