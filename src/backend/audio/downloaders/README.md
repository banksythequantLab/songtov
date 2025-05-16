# MaiVid Studio Audio Downloaders

This directory contains specialized downloaders for various audio platforms to be used with MaiVid Studio.

## Available Downloaders

### Suno Downloader

The `suno_downloader.py` module provides robust functionality for downloading songs from Suno.com with the following features:

- Support for various Suno URL formats (share URLs, direct song URLs, etc.)
- Automatic metadata extraction
- Multiple methods for MP3 file location and download
- Lyrics extraction using both HTML parsing and Whisper AI transcription
- Automatic scene generation based on lyrics content
- Fallback mechanisms when primary download methods fail

## Integration with MaiVid Studio

The downloaders are integrated with the main audio processor through the `suno_integration.py` module, which provides a simplified interface to use the enhanced downloader functionality.

## Usage

### Within MaiVid Studio

The audio processor automatically uses these downloaders when a URL from a supported platform is provided.

### Command-line Testing

You can test the Suno downloader directly using the provided command-line tool:

```bash
python download_suno_song.py https://suno.com/s/YOUR_SONG_ID
```

Or with a specific output directory:

```bash
python download_suno_song.py https://suno.com/s/YOUR_SONG_ID --output-dir my_songs
```

## Adding New Downloaders

To add support for new audio platforms:

1. Create a new downloader module in this directory
2. Create an integration module that provides a simplified interface
3. Update the main audio processor to recognize and use the new downloader
4. Add the URL pattern to the `SUPPORTED_PLATFORMS` dictionary in `processor.py`
