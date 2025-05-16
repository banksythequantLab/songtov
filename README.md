# MaiVid Studio

## Overview
MaiVid Studio is an AI-driven music video generation platform that allows for seamless creation of visually compelling music videos with strong narrative elements based on song input.

## Features
- Direct integration with music platforms (including Suno)
- Automatic lyric extraction using OpenAI Whisper
- AI-driven concept development and storyline creation
- Scene breakdown and storyboard generation
- Timeline and motion editing
- Multiple export options

## Installation

### Prerequisites
- Python 3.8+
- ComfyUI installation
- Firebase account for database functionality
- GPU for accelerated video processing

### Setup
1. Clone this repository
2. Install dependencies:
```
pip install -r requirements.txt
```
3. Configure environment variables (see Configuration section)
4. Run the application:
```
python start.py
```

## Configuration
Create a `.env` file with the following variables:
```
FIREBASE_API_KEY=your_api_key
FIREBASE_AUTH_DOMAIN=your_domain
FIREBASE_DATABASE_URL=your_db_url
FIREBASE_STORAGE_BUCKET=your_bucket
OPENAI_API_KEY=your_openai_key
```

## Usage
1. Start the MaiVid Studio server using start.bat
2. Access the web interface at http://localhost:420
3. Import a song using a URL or file upload
4. Follow the guided workflow to create your music video

## Current Status
The integration is functional with the following capabilities:
- Song downloading from Suno URLs
- Metadata extraction
- Lyrics extraction using HTML parsing and Whisper
- Scene generation based on lyrics
- Web interface integration

## Credits
This project builds upon several open-source libraries and technologies, including ComfyUI.

## License
[MIT License](LICENSE)
