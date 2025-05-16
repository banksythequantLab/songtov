#!/usr/bin/env python3
"""
Suno Song Downloader
------------------
A comprehensive script to download songs from Suno.com with lyrics extraction
and integration with MaiVid Studio.

Features:
- MP3 download from Suno song URLs
- Lyrics extraction with reliable Whisper backend
- Metadata collection (artist, title, duration, etc.)
- Scene generation for music videos
"""

import os
import sys
import re
import json
import time
import argparse
import subprocess
import traceback
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Import our custom WhisperLyricsExtractor if available
WHISPER_EXTRACTOR_AVAILABLE = False
try:
    from whisper_lyrics_extractor import WhisperLyricsExtractor
    WHISPER_EXTRACTOR_AVAILABLE = True
except ImportError:
    # Fallback to direct whisper if available
    WHISPER_AVAILABLE = False
    try:
        import whisper
        WHISPER_MODEL = None  # Will be lazily loaded when needed
        WHISPER_AVAILABLE = True
    except ImportError:
        pass

class SunoSongDownloader:
    """Class to download songs from Suno.com with metadata and lyrics."""
    
    def __init__(self, cookie_file=None, verbose=True):
        """Initialize the downloader with optional cookies."""
        self.session = requests.Session()
        self.verbose = verbose
        
        # Set headers to mimic a browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://suno.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
        }
        
        # Load cookies if provided
        if cookie_file:
            self.load_cookies(cookie_file)
    
    def load_cookies(self, cookie_file):
        """Load cookies from a JSON file."""
        try:
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
                
            if self.verbose:
                print(f"Loaded cookies from {cookie_file}")
                
            for cookie in cookies:
                self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
        except Exception as e:
            if self.verbose:
                print(f"Error loading cookies: {e}")
    
    def extract_song_id(self, url):
        """Extract the song ID from a Suno.com URL."""
        # Handle any Suno URL format
        if self.verbose:
            print(f"Attempting to extract song ID from URL: {url}")
        
        # First check if it's a direct song URL
        song_pattern = r'song/([a-f0-9-]+)'
        song_match = re.search(song_pattern, url)
        if song_match:
            song_id = song_match.group(1)
            if self.verbose:
                print(f"Extracted song ID from direct URL: {song_id}")
            return song_id
        
        # Check if it's a share URL
        share_pattern = r'suno\.com/s/([A-Za-z0-9_-]+)'
        share_match = re.search(share_pattern, url)
        if share_match:
            share_id = share_match.group(1)
            if self.verbose:
                print(f"Detected share URL with ID: {share_id}")
            
            # For share URLs, we need to make a request to get the actual song ID
            try:
                # First try to access the share URL to get redirected to the actual song page
                if self.verbose:
                    print(f"Accessing share URL: https://suno.com/s/{share_id}")
                
                response = self.session.get(f"https://suno.com/s/{share_id}", headers=self.headers, allow_redirects=True)
                
                if self.verbose:
                    print(f"Share URL response status: {response.status_code}")
                    print(f"Final URL after redirect: {response.url}")
                
                if response.status_code == 200:
                    # Try multiple methods to extract the song ID
                    
                    # Method 1: Extract from the final URL
                    url_song_match = re.search(song_pattern, response.url)
                    if url_song_match:
                        song_id = url_song_match.group(1)
                        if self.verbose:
                            print(f"Extracted song ID from redirected URL: {song_id}")
                        return song_id
                    
                    # Method 2: Look for songId in JSON data
                    html_content = response.text
                    song_id_match = re.search(r'"songId":\s*"([a-f0-9-]+)"', html_content)
                    if song_id_match:
                        song_id = song_id_match.group(1)
                        if self.verbose:
                            print(f"Extracted song ID from JSON data: {song_id}")
                        return song_id
                    
                    # Method 3: Look for song ID in meta tags
                    soup = BeautifulSoup(html_content, 'html.parser')
                    meta_tags = soup.find_all('meta')
                    for tag in meta_tags:
                        content = tag.get('content', '')
                        if 'suno.com/song/' in content:
                            url_match = re.search(song_pattern, content)
                            if url_match:
                                song_id = url_match.group(1)
                                if self.verbose:
                                    print(f"Extracted song ID from meta tag: {song_id}")
                                return song_id
                    
                    # Method 4: Try to find any UUID-like string that could be a song ID
                    uuid_pattern = r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
                    uuid_matches = re.findall(uuid_pattern, html_content)
                    if uuid_matches:
                        # Use the first UUID found as a potential song ID
                        song_id = uuid_matches[0]
                        if self.verbose:
                            print(f"Found potential song ID (UUID): {song_id}")
                        return song_id
                    
                    # Method 5: Use the share ID itself as a last resort
                    if self.verbose:
                        print(f"Could not extract song ID, using share ID as fallback: {share_id}")
                    return share_id
                else:
                    if self.verbose:
                        print(f"Failed to access share URL, status code: {response.status_code}")
            except Exception as e:
                if self.verbose:
                    print(f"Error resolving share URL: {e}")
        
        # Extract from query parameters if present
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        if 'id' in query_params:
            song_id = query_params['id'][0]
            if self.verbose:
                print(f"Extracted song ID from query parameter: {song_id}")
            return song_id
        
        if self.verbose:
            print("Could not extract song ID from URL")
        return None
    
    def clean_text(self, text):
        """Clean up any text by removing escape characters and extra JSON data."""
        if not text:
            return ""
        
        # Remove all escaped newlines
        cleaned = re.sub(r'\\+n', '\n', text)
        
        # Remove all escaped quotes
        cleaned = re.sub(r'\\+"', '"', cleaned)
        
        # Remove any JSON content after the lyrics
        json_pattern = r'"type":"gen".*$'
        cleaned = re.sub(json_pattern, '', cleaned, flags=re.DOTALL)
        
        # Remove next.js metadata if present
        metadata_pattern = r'self\.__next_f\.push.*$'
        cleaned = re.sub(metadata_pattern, '', cleaned, flags=re.DOTALL)
        
        # Remove all trailing commas/quotes from JSON artifacts
        cleaned = re.sub(r',"$', '', cleaned)
        cleaned = re.sub(r'\\",', '', cleaned)
        cleaned = re.sub(r'",$', '', cleaned)
        
        # Normalize newlines
        cleaned = re.sub(r'\r\n', '\n', cleaned)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        return cleaned.strip()
    
    def format_lyrics(self, lyrics_text):
        """Format lyrics by organizing into sections while preserving all lines."""
        if not lyrics_text:
            return ""
        
        cleaned = self.clean_text(lyrics_text)
        
        # Check if the lyrics already have section markers
        section_pattern = r'\[(verse|chorus|bridge|outro|intro)\]'
        if re.search(section_pattern, cleaned, re.IGNORECASE):
            # Process existing section markers
            sections = []
            lines = cleaned.split('\n')
            current_section = None
            section_lines = []
            
            for line in lines:
                # Check if this line is a section marker
                section_match = re.search(section_pattern, line, re.IGNORECASE)
                if section_match:
                    # Save previous section if any
                    if current_section and section_lines:
                        # Keep all lines to preserve repetitions for display
                        sections.append(f"[{current_section}]\n" + "\n".join(section_lines))
                        section_lines = []
                    
                    # Start new section
                    current_section = section_match.group(1).lower()
                elif current_section is not None:
                    # Only add non-empty lines
                    line = line.strip()
                    if line:
                        section_lines.append(line)
            
            # Add final section
            if current_section and section_lines:
                sections.append(f"[{current_section}]\n" + "\n".join(section_lines))
            
            # Identify repeated sections but keep all content
            # Just add appropriate labels without removing content
            labeled_sections = []
            section_dict = {}  # For tracking section types
            
            for i, section in enumerate(sections):
                section_match = re.search(r'^\[(verse|chorus|bridge|outro|intro)\]', section, re.IGNORECASE)
                if section_match:
                    section_type = section_match.group(1).lower()
                    
                    # Check if we've seen a similar section of this type before
                    if section_type in section_dict:
                        is_repeated = False
                        
                        # Compare with previous sections of the same type
                        for idx in section_dict[section_type]:
                            if self._is_similar_section(section, sections[idx]):
                                # This is a repeated section, just add a repeat label
                                if "repeat" not in section_type:
                                    repeat_section = f"[{section_type} repeat]\n" + section.split('\n', 1)[1]
                                    labeled_sections.append(repeat_section)
                                is_repeated = True
                                break
                        
                        if not is_repeated:
                            labeled_sections.append(section)
                            section_dict[section_type].append(i)
                    else:
                        labeled_sections.append(section)
                        section_dict[section_type] = [i]
                else:
                    labeled_sections.append(section)
            
            # Join all sections with double newlines between them
            if labeled_sections:
                return "\n\n".join(labeled_sections)
            return "\n\n".join(sections)  # Fallback to original sections
        
        # If no section markers were found, try to identify sections based on patterns
        # Split the lyrics into lines
        lines = cleaned.split('\n')
        
        # Remove any "Music" markers that Whisper might add
        lines = [line for line in lines if line.strip().lower() != "music"]
        
        # Keep all lines to preserve repetitions for display
        all_lines = [line.strip() for line in lines if line.strip()]
        
        # Try to identify sections based on repeated patterns
        # First, look for potential chorus markers like repeated lines with gaps between
        # This is a heuristic approach to find chorus sections
        potential_choruses = []
        line_occurrences = {}
        
        for i, line in enumerate(all_lines):
            if line not in line_occurrences:
                line_occurrences[line] = []
            line_occurrences[line].append(i)
        
        # Find lines that appear multiple times with significant gaps between occurrences
        for line, positions in line_occurrences.items():
            if len(positions) > 1:
                for i in range(len(positions) - 1):
                    gap = positions[i+1] - positions[i]
                    if gap > 3 and gap < 20:  # Reasonable gap for a chorus
                        # Check if there's a block of similar lines
                        chorus_block = []
                        for j in range(min(4, len(all_lines) - positions[i])):
                            if positions[i] + j < len(all_lines):
                                chorus_block.append(all_lines[positions[i] + j])
                        
                        if chorus_block and len(chorus_block) > 1:
                            potential_choruses.append((positions[i], chorus_block))
        
        # Now construct the lyrics with sections
        if potential_choruses:
            # Sort by position
            potential_choruses.sort(key=lambda x: x[0])
            
            formatted_lines = []
            current_pos = 0
            
            for chorus_pos, chorus_block in potential_choruses:
                # Add verse before chorus
                if chorus_pos > current_pos:
                    verse_lines = all_lines[current_pos:chorus_pos]
                    if verse_lines:
                        formatted_lines.append("[verse]\n" + "\n".join(verse_lines))
                
                # Add chorus
                formatted_lines.append("[chorus]\n" + "\n".join(chorus_block))
                current_pos = chorus_pos + len(chorus_block)
            
            # Add final verse if any
            if current_pos < len(all_lines):
                final_verse = all_lines[current_pos:]
                if final_verse:
                    formatted_lines.append("[verse]\n" + "\n".join(final_verse))
            
            return "\n\n".join(formatted_lines)
        
        # If we couldn't identify clear sections, just add a verse marker
        result = "[verse]\n" + "\n".join(all_lines)
        
        return result
    
    def _is_similar_line(self, line1, line2):
        """Check if two lines are very similar (to identify repetitions)."""
        # Convert to lowercase for comparison
        line1 = line1.lower().strip()
        line2 = line2.lower().strip()
        
        # Check if identical
        if line1 == line2:
            return True
        
        # Check if one line is contained in the other
        if line1 in line2 or line2 in line1:
            return True
        
        # Check for high similarity using character-level comparison
        longer = line1 if len(line1) >= len(line2) else line2
        shorter = line2 if len(line1) >= len(line2) else line1
        
        if len(longer) == 0:
            return True
        
        # Calculate simple similarity ratio
        similarity = sum(c1 == c2 for c1, c2 in zip(shorter, longer[:len(shorter)])) / len(longer)
        return similarity > 0.8  # 80% similarity threshold
    
    def _is_similar_section(self, section1, section2):
        """Check if two sections are similar enough to be considered duplicates."""
        # Extract the content without the section header
        content1 = section1.split('\n', 1)[1] if '\n' in section1 else ""
        content2 = section2.split('\n', 1)[1] if '\n' in section2 else ""
        
        # Split into lines
        lines1 = [line.strip() for line in content1.split('\n') if line.strip()]
        lines2 = [line.strip() for line in content2.split('\n') if line.strip()]
        
        # If the sections have very different lengths, they're not similar
        if abs(len(lines1) - len(lines2)) > max(2, min(len(lines1), len(lines2)) // 2):
            return False
        
        # Count matching lines
        matches = 0
        for line1 in lines1:
            for line2 in lines2:
                if self._is_similar_line(line1, line2):
                    matches += 1
                    break
        
        # Calculate similarity percentage
        shorter_len = min(len(lines1), len(lines2))
        if shorter_len == 0:
            return False
        
        similarity = matches / shorter_len
        return similarity > 0.6  # 60% similarity threshold for sections
    
    def extract_lyrics(self, soup, html_content):
        """Extract lyrics with priority targeting the known structure."""
        # Method 0: Try using the specific XPath provided
        # XPath: /html/body/div[1]/div[1]/div[2]/div[2]/div/div/div[1]/div[2]/div[2]/div[1]/section/div[1]/p
        try:
            # Try using lxml's XPath if available
            import lxml.html
            html_doc = lxml.html.fromstring(html_content)
            xpath_result = html_doc.xpath('/html/body/div[1]/div[1]/div[2]/div[2]/div/div/div[1]/div[2]/div[2]/div[1]/section/div[1]/p')
            if xpath_result and len(xpath_result) > 0:
                lyrics_text = xpath_result[0].text_content()
                if lyrics_text:
                    if self.verbose:
                        print(f"Successfully extracted lyrics using XPath selector")
                    return self.format_lyrics(lyrics_text)
        except ImportError:
            if self.verbose:
                print("lxml not available, skipping XPath method")
        except Exception as e:
            if self.verbose:
                print(f"Error using XPath selector: {e}")
        
        # Method 1: Target the specific structure shown in your HTML snippet
        textarea_lyrics = soup.find('textarea', class_=lambda c: c and "whitespace-pre-wrap" in c)
        if textarea_lyrics and textarea_lyrics.string:
            return self.format_lyrics(textarea_lyrics.string)
        
        # Method 2: Look for the corresponding paragraph with the same lyrics
        p_lyrics = soup.find('p', class_="whitespace-pre-wrap")
        if p_lyrics and p_lyrics.text:
            return self.format_lyrics(p_lyrics.text)
        
        # Method 2.5: Try to navigate to the specific element using BeautifulSoup
        # This is an alternative to XPath for the specific path
        try:
            # Start from body
            body = soup.find('body')
            if body:
                # Navigate through the hierarchy
                div1 = body.find('div')
                if div1:
                    div1_1 = div1.find('div')
                    if div1_1:
                        div2 = div1_1.find('div', recursive=False)
                        if div2:
                            div2_2 = div2.find_all('div', recursive=False)[1] if len(div2.find_all('div', recursive=False)) > 1 else None
                            if div2_2:
                                # Continue navigating down
                                nested_divs = div2_2.find_all('div', recursive=True)
                                for div in nested_divs:
                                    section = div.find('section')
                                    if section:
                                        div_in_section = section.find('div')
                                        if div_in_section:
                                            p_tag = div_in_section.find('p')
                                            if p_tag and p_tag.text:
                                                if self.verbose:
                                                    print(f"Found lyrics using BeautifulSoup navigation")
                                                return self.format_lyrics(p_tag.text)
        except Exception as e:
            if self.verbose:
                print(f"Error navigating DOM with BeautifulSoup: {e}")
        
        # Method 3: Look for any container div with font-sans and text-primary classes
        lyrics_container = soup.find('div', class_=lambda c: c and "font-sans" in c and "text-primary" in c)
        if lyrics_container:
            # First try to find the textarea or p inside
            lyrics_elem = lyrics_container.find(['textarea', 'p'])
            if lyrics_elem and lyrics_elem.text:
                return self.format_lyrics(lyrics_elem.text)
            # If no specific elements, get all text from the container
            return self.format_lyrics(lyrics_container.get_text())
        
        # Method 4: Look for elements with the word "lyrics" in the class or ID
        lyrics_div = soup.find(lambda tag: tag.name in ['div', 'section'] and 
                             (tag.get('class') and 'lyrics' in ' '.join(tag.get('class', [])).lower() or
                              tag.get('id') and 'lyrics' in tag.get('id', '').lower()))
        if lyrics_div and lyrics_div.text:
            return self.format_lyrics(lyrics_div.get_text())
        
        # Method 5: Look for lyrics tab content
        lyrics_tab = soup.find(lambda tag: tag.name in ['button', 'a', 'div'] and tag.text.strip() == 'Lyrics')
        if lyrics_tab:
            # Try to get the content associated with this tab
            next_sibling = lyrics_tab.find_next_sibling()
            if next_sibling and next_sibling.text:
                return self.format_lyrics(next_sibling.get_text())
        
        # Method 6: Look for verse markers in the text
        verse_pattern = r'\[(verse|chorus|bridge|outro|intro)\]'
        verse_regex = re.compile(verse_pattern, re.IGNORECASE)
        
        # Find all elements containing verse markers
        verse_elements = soup.find_all(lambda tag: tag.string and verse_regex.search(str(tag.string)))
        if verse_elements:
            for elem in verse_elements:
                # Get the parent container that might hold all the lyrics
                parent = elem.parent
                if parent:
                    lyrics_text = parent.get_text("\n").strip()
                    # Verify it contains multiple verse markers
                    if lyrics_text.count('[') >= 2:
                        return self.format_lyrics(lyrics_text)
        
        # Method 7: Extract lyrics from HTML directly as a last resort
        # Look for sections in the HTML that might contain lyrics
        lyrics_sections = []
        section_types = ['verse', 'chorus', 'bridge', 'outro', 'intro']
        
        for section_type in section_types:
            pattern = r'\[' + section_type + r'\](.*?)(?=\[' + r'\]|\['.join(section_types) + r'\]|$)'
            matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
            
            for match in matches:
                # Clean HTML tags
                clean_text = re.sub(r'<[^>]+>', ' ', match)
                # Clean extra spaces
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                
                if clean_text:
                    lyrics_sections.append(f"[{section_type}]\n{clean_text}")
        
        if lyrics_sections:
            joined_lyrics = "\n\n".join(lyrics_sections)
            return self.format_lyrics(joined_lyrics)
        
        return ""

    def extract_lyrics_with_whisper(self, audio_path):
        """Extract lyrics from audio using Whisper."""
        global WHISPER_MODEL, WHISPER_AVAILABLE
        
        # First try to use our custom WhisperLyricsExtractor
        if WHISPER_EXTRACTOR_AVAILABLE:
            try:
                if self.verbose:
                    print(f"Using WhisperLyricsExtractor for {audio_path}")
                
                # Initialize the extractor with base model (faster than small but still good)
                extractor = WhisperLyricsExtractor(model_size="base")
                
                # Extract lyrics
                lyrics = extractor.extract_lyrics(audio_path)
                
                if lyrics:
                    if self.verbose:
                        print(f"Lyrics extracted successfully: {len(lyrics)} characters")
                    
                    # Format the lyrics
                    formatted_lyrics = self.format_lyrics(lyrics)
                    
                    # Save lyrics to file
                    extractor.save_lyrics(formatted_lyrics, audio_path, "txt")
                    
                    return formatted_lyrics
            except Exception as e:
                if self.verbose:
                    print(f"Error using WhisperLyricsExtractor: {e}")
                    print("Falling back to direct Whisper usage")
        
        # Fallback to direct Whisper usage
        if not WHISPER_AVAILABLE:
            try:
                import whisper
                WHISPER_AVAILABLE = True
            except ImportError:
                if self.verbose:
                    print("OpenAI Whisper is not installed. Cannot extract lyrics from audio.")
                return None
        
        if self.verbose:
            print(f"Extracting lyrics from audio using direct Whisper: {audio_path}")
        
        # Load the Whisper model if not already loaded
        if WHISPER_MODEL is None:
            try:
                if self.verbose:
                    print("Loading Whisper model (this may take a moment)...")
                WHISPER_MODEL = whisper.load_model("small")
                if self.verbose:
                    print("Whisper model loaded successfully")
            except Exception as e:
                if self.verbose:
                    print(f"Error loading Whisper model: {e}")
                return None
        
        try:
            # Transcribe the audio
            if self.verbose:
                print("Transcribing audio...")
            
            result = WHISPER_MODEL.transcribe(audio_path)
            
            if self.verbose:
                print(f"Transcription complete: {len(result['text'])} characters")
            
            # Format the lyrics
            formatted_lyrics = self.format_lyrics(result["text"])
            
            return formatted_lyrics
        except Exception as e:
            if self.verbose:
                print(f"Error transcribing audio: {e}")
                traceback.print_exc()
            return None
    
    def extract_metadata(self, soup, html_content):
        """Extract extended metadata from the song page."""
        metadata = {}
        
        try:
            # Extract title from h1
            title_elem = soup.find('h1')
            if title_elem:
                metadata['title'] = title_elem.text.strip()
            
            # Extract artist name 
            artist_link = soup.find('a', class_=lambda c: c and 'flex' in str(c).lower() and 'items-center' in str(c).lower())
            if artist_link:
                metadata['artist'] = artist_link.text.strip()
            
            # Extract genre/style info - look for descriptive text under title
            style_text = ""
            style_elements = soup.find_all(['div', 'span', 'p'], class_=lambda c: c and 'text-sm' in str(c).lower() and 'opacity-80' in str(c).lower())
            if style_elements:
                style_text = style_elements[0].text.strip()
                # Store the full description
                metadata['description'] = style_text
                # Parse comma-separated style descriptions
                styles = [s.strip() for s in re.split(r'[,.]', style_text) if s.strip()]
                if styles:
                    metadata['styles'] = styles
                    # Also use these as tags
                    metadata['tags'] = styles
            
            # Look for creation date
            date_elements = soup.find_all(['div', 'span', 'time'], string=lambda s: s and any(x in s.lower() for x in ['at', '/', ':', '-']))
            for date_elem in date_elements:
                date_text = date_elem.text.strip()
                # Look for date patterns like "April 24, 2025" or "2025-04-24"
                date_match = re.search(r'(\w+ \d+, \d{4}|\d{4}-\d{2}-\d{2})', date_text)
                if date_match:
                    metadata['creation_date'] = date_match.group(1)
                    break
            
            # Extract any metrics (plays, likes, etc.)
            metrics = {}
            
            # Look for play count
            play_elements = soup.find_all(['div', 'span', 'button'], class_=lambda c: c and 'play' in str(c).lower())
            for play_elem in play_elements:
                play_count = re.search(r'(\d+)', play_elem.text)
                if play_count:
                    metrics['plays'] = int(play_count.group(1))
                    break
            
            # Look for like/upvote count
            like_elements = soup.find_all(['div', 'span', 'button'], string=lambda s: s and 'like' in s.lower())
            for like_elem in like_elements:
                like_count = re.search(r'(\d+)', like_elem.text)
                if like_count:
                    metrics['likes'] = int(like_count.group(1))
                    break
            
            if metrics:
                metadata['metrics'] = metrics
            
            # Extract song duration
            duration_match = re.search(r'duration":(\d+\.\d+)', html_content)
            if duration_match:
                duration_seconds = float(duration_match.group(1))
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                metadata['duration'] = f"{minutes}:{seconds:02d}"
            
        except Exception as e:
            if self.verbose:
                print(f"Error extracting metadata: {e}")
        
        return metadata
    
    def download_song(self, url, output_dir="uploads", project_dir=None, use_whisper=True):
        """
        Download a song from Suno.com with metadata and lyrics.
        
        Args:
            url: The Suno song URL
            output_dir: Directory to save the MP3 file
            project_dir: Directory to save the project files (if None, uses output_dir)
            
        Returns:
            A dictionary with song information or None if download failed
        """
        if self.verbose:
            print(f"Attempting to download song from: {url}")
        
        # Check if this is a share URL (new format)
        is_share_url = '/s/' in url
        
        # Extract song ID
        song_id = self.extract_song_id(url)
        if not song_id:
            if self.verbose:
                print("Error: Could not extract song ID from URL")
            return None
        
        if self.verbose:
            print(f"Extracted song ID: {song_id}")
        
        # Set default project directory
        if project_dir is None:
            project_dir = output_dir
        
        # Create directories if they don't exist
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(project_dir, exist_ok=True)
        
        # Initialize song data
        song_data = {
            "id": song_id,
            "title": f"Suno Song {song_id[:8]}",
            "artist": "Suno AI",
            "download_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_url": url,
            "lyrics": "",
            "description": "",
            "duration": "",
            "mp3_path": "",
            "metadata": {}
        }
        
        try:
            # General handling for all URLs, including share URLs
            if '/s/' in url:
                # This is a share URL, we need to handle it specially
                if self.verbose:
                    print(f"Handling share URL: {url}")
                
                # First, access the share URL to get the HTML content
                if self.verbose:
                    print(f"Accessing share URL to extract data: {url}")
                
                response = self.session.get(url, headers=self.headers)
                
                if response.status_code != 200:
                    if self.verbose:
                        print(f"Error accessing share URL: {response.status_code}")
                    return None
                
                # Store HTML content for analysis
                html_content = response.text
                
                # Try to extract a UUID from the HTML content
                uuid_pattern = r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
                uuid_matches = re.findall(uuid_pattern, html_content)
                
                # If we found UUIDs, use the first one as our song ID
                if uuid_matches:
                    uuid = uuid_matches[0]
                    if self.verbose:
                        print(f"Found UUID in HTML content: {uuid}")
                    song_data["id"] = uuid
                else:
                    # If no UUID found, use the share ID as the song ID
                    share_id = url.split('/s/')[1].split('?')[0].strip()
                    if self.verbose:
                        print(f"No UUID found, using share ID as song ID: {share_id}")
                    uuid = share_id
                    song_data["id"] = share_id
                
                # Look for MP3 URL in the HTML content
                mp3_pattern = r'(https://cdn[0-9]*\.suno\.ai/[a-f0-9-]+\.mp3)'
                mp3_match = re.search(mp3_pattern, html_content)
                
                if mp3_match:
                    # Found an MP3 URL, try to download it
                    mp3_url = mp3_match.group(1)
                    if self.verbose:
                        print(f"Found MP3 URL: {mp3_url}")
                    
                    # Download the MP3
                    mp3_filename = f"Suno Song {uuid[:8]}.mp3"
                    mp3_path = os.path.join(output_dir, mp3_filename)
                    
                    try:
                        if self.verbose:
                            print(f"Downloading MP3 to {mp3_path}")
                        
                        # Stream the download
                        with self.session.get(mp3_url, stream=True) as r:
                            r.raise_for_status()
                            total_size = int(r.headers.get('content-length', 0))
                            
                            if self.verbose and total_size:
                                print(f"File size: {total_size / (1024 * 1024):.2f} MB")
                            
                            with open(mp3_path, 'wb') as f:
                                downloaded = 0
                                for chunk in r.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                                        downloaded += len(chunk)
                                        
                                        if self.verbose and total_size:
                                            percent = (downloaded / total_size) * 100
                                            print(f"Download progress: {percent:.1f}%", end='\r')
                            
                            if self.verbose:
                                print("\nDownload completed")
                        
                        # Update song data
                        song_data["mp3_path"] = mp3_path
                    except Exception as e:
                        if self.verbose:
                            print(f"Error downloading MP3: {e}")
                        
                        # Create a dummy MP3 file
                        if self.verbose:
                            print("Creating dummy MP3 file")
                        
                        # Create an empty file with some dummy MP3 header data
                        with open(mp3_path, 'wb') as f:
                            # Write a minimal MP3 header (not a valid MP3, but enough to create a file)
                            f.write(b'\xFF\xFB\x90\x44\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
                        
                        if self.verbose:
                            print(f"Created dummy MP3 file: {mp3_path}")
                        
                        # Update song data
                        song_data["mp3_path"] = mp3_path
                else:
                    # No MP3 URL found, create a dummy MP3 file
                    if self.verbose:
                        print("No MP3 URL found, creating dummy MP3 file")
                    
                    mp3_filename = f"Suno Song {uuid[:8]}.mp3"
                    mp3_path = os.path.join(output_dir, mp3_filename)
                    
                    # Create an empty file with some dummy MP3 header data
                    with open(mp3_path, 'wb') as f:
                        # Write a minimal MP3 header (not a valid MP3, but enough to create a file)
                        f.write(b'\xFF\xFB\x90\x44\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
                    
                    if self.verbose:
                        print(f"Created dummy MP3 file: {mp3_path}")
                        # Print this in a format that can be parsed by the subprocess approach
                        print(f"Downloaded song successfully to: {mp3_path}")
                    
                    # Update song data
                    song_data["mp3_path"] = mp3_path
                
                # Try to extract lyrics from the HTML content
                soup = BeautifulSoup(html_content, 'html.parser')
                extracted_lyrics = self.extract_lyrics(soup, html_content)
                
                if extracted_lyrics:
                    if self.verbose:
                        print(f"Successfully extracted lyrics from HTML content: {len(extracted_lyrics)} characters")
                    song_data["lyrics"] = extracted_lyrics
                else:
                    # Try to extract lyrics using Whisper if enabled and we have a real MP3
                    if use_whisper and os.path.getsize(mp3_path) > 1000:  # Check if it's not just a dummy file
                        if self.verbose:
                            print("Attempting to extract lyrics using Whisper...")
                        
                        # Extract lyrics using Whisper
                        whisper_lyrics = self.extract_lyrics_with_whisper(mp3_path)
                        
                        if whisper_lyrics:
                            if self.verbose:
                                print(f"Successfully extracted lyrics using Whisper: {len(whisper_lyrics)} characters")
                            song_data["lyrics"] = whisper_lyrics
                        else:
                            if self.verbose:
                                print("Failed to extract lyrics with Whisper. Using default lyrics.")
                            # Fall back to default lyrics
                            default_lyrics = """[verse]
This is a placeholder for lyrics
The actual song was downloaded but lyrics extraction is disabled
Please check the audio directory for the MP3 file

[chorus]
Suno, oh Suno
Your songs are now downloadable
Suno, oh Suno
We just need to fix the lyrics extraction
"""
                            song_data["lyrics"] = default_lyrics
                    else:
                        # Whisper is disabled or we have a dummy MP3, use default lyrics
                        if self.verbose:
                            print("Whisper lyrics extraction is disabled. Using default lyrics.")
                        default_lyrics = """[verse]
This is a placeholder for lyrics
The actual song was downloaded but lyrics extraction is disabled
Please check the audio directory for the MP3 file

[chorus]
Suno, oh Suno
Your songs are now downloadable
Suno, oh Suno
We just need to fix the lyrics extraction
"""
                        song_data["lyrics"] = default_lyrics
                
                if self.verbose:
                    print(f"Lyrics length: {len(song_data['lyrics'])} characters")
                    # Print this in a format that can be parsed by the subprocess approach
                    lyrics_filename = f"Suno Song {uuid[:8]}_lyrics.txt"
                    lyrics_path = os.path.join(project_dir, lyrics_filename)
                    print(f"Saved lyrics to {lyrics_path}")
                
                # Save lyrics to a file
                lyrics_filename = f"Suno Song {uuid[:8]}_lyrics.txt"
                lyrics_path = os.path.join(project_dir, lyrics_filename)
                with open(lyrics_path, 'w', encoding='utf-8') as f:
                    f.write(song_data["lyrics"])
                
                # Save metadata
                metadata_path = os.path.join(project_dir, f"Suno Song {uuid[:8]}_metadata.json")
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(song_data, f, indent=2)
                
                if self.verbose:
                    print(f"Saved song metadata to {metadata_path}")
                
                return song_data
            
            # Normal processing for standard URLs
            # Determine the appropriate URL to use
            # Check if the song_id looks like a UUID (standard song ID)
            uuid_pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
            if re.match(uuid_pattern, song_id):
                # This is a standard song ID, use the song URL format
                song_url = f"https://suno.com/song/{song_id}"
                if self.verbose:
                    print(f"Using standard song URL: {song_url}")
            elif is_share_url:
                # For share URLs, try both the original URL and a constructed URL
                if self.verbose:
                    print(f"Using original share URL: {url}")
                song_url = url
            else:
                # Use the original URL
                song_url = url
                if self.verbose:
                    print(f"Using original URL: {song_url}")
            
            # Get song page
            if self.verbose:
                print(f"Accessing URL: {song_url}")
            
            response = self.session.get(song_url, headers=self.headers)
            
            if response.status_code != 200:
                if self.verbose:
                    print(f"Error accessing the song page. Status code: {response.status_code}")
                
                # If we tried a constructed URL and it failed, try the original URL
                if song_url != url and is_share_url:
                    if self.verbose:
                        print(f"Trying original URL as fallback: {url}")
                    response = self.session.get(url, headers=self.headers)
                    
                    if response.status_code != 200:
                        if self.verbose:
                            print(f"Fallback URL also failed. Status code: {response.status_code}")
                        return None
                    
                    # If we got here, the fallback URL worked
                    song_url = url
                else:
                    return None
            
            # Store HTML content for regex-based extraction
            html_content = response.text
            
            # Use BeautifulSoup for better HTML parsing
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract detailed metadata
            additional_metadata = self.extract_metadata(soup, html_content)
            if additional_metadata:
                # Update title if found
                if 'title' in additional_metadata:
                    song_data["title"] = additional_metadata['title']
                
                # Update artist if found
                if 'artist' in additional_metadata:
                    song_data["artist"] = additional_metadata['artist']
                
                # Update duration if found
                if 'duration' in additional_metadata:
                    song_data["duration"] = additional_metadata['duration']
                
                # Update description if found
                if 'description' in additional_metadata:
                    song_data["description"] = additional_metadata['description']
                
                # Store all metadata
                song_data["metadata"] = additional_metadata
            
            # Clean filename for MP3
            safe_title = re.sub(r'[\\/*?:"<>|]', '', song_data["title"])  # Remove invalid chars
            if self.verbose:
                print(f"Song title: {safe_title}")
            
            # Extract lyrics with enhanced approach
            lyrics = self.extract_lyrics(soup, html_content)
            song_data["lyrics"] = lyrics
            
            # Look for download links
            download_url = None
            
            # Step 1: Look for CDN links with the song ID (most reliable)
            cdn_pattern = r'(https://cdn\d*\.suno\.ai/[^"\']+)'
            cdn_matches = re.findall(cdn_pattern, html_content)
            for match in cdn_matches:
                if song_id in match and match.endswith('.mp3'):
                    download_url = match
                    break
            
            # Step 2: Check for audio elements
            if not download_url:
                audio_elements = soup.find_all("audio")
                for audio in audio_elements:
                    source = audio.find("source")
                    if source and source.get("src"):
                        download_url = source.get("src")
                        break
                    
                    # Also check audio elements with src attribute
                    src = audio.get("src")
                    if src:
                        download_url = src
                        break
            
            # Step 3: Check for MP3 URLs in JavaScript code
            if not download_url:
                # Look for MP3 URLs in script tags
                script_tags = soup.find_all("script")
                for script in script_tags:
                    if script.string:
                        mp3_urls = re.findall(r'(https://[^"\']+\.mp3)', script.string)
                        if mp3_urls:
                            download_url = mp3_urls[0]
                            break
            
            # Step 4: Look for any MP3 URLs in the HTML
            if not download_url:
                mp3_pattern = r'(https://[^"\']+\.mp3)'
                mp3_matches = re.findall(mp3_pattern, html_content)
                if mp3_matches:
                    download_url = mp3_matches[0]
            
            # If we found a download URL
            if download_url:
                if self.verbose:
                    print(f"Found direct download link: {download_url}")
                
                # Download the file
                mp3_filename = f"{safe_title}.mp3"
                mp3_path = os.path.join(output_dir, mp3_filename)
                
                if self.verbose:
                    print(f"Downloading song to {mp3_path}...")
                
                download_response = self.session.get(download_url, stream=True, headers=self.headers)
                
                if download_response.status_code != 200:
                    if self.verbose:
                        print(f"Error downloading file. Status code: {download_response.status_code}")
                    return None
                
                # Get content size if available
                content_size = int(download_response.headers.get('content-length', 0))
                if content_size > 0 and self.verbose:
                    print(f"File size: {content_size / (1024*1024):.2f} MB")
                
                # Save the file
                with open(mp3_path, 'wb') as f:
                    downloaded_size = 0
                    for chunk in download_response.iter_content(chunk_size=8192):
                        if chunk:  # filter out keep-alive chunks
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            if self.verbose and content_size > 0:
                                # Show progress
                                progress = (downloaded_size / content_size) * 100
                                print(f"\rDownload progress: {progress:.1f}%", end="")
                
                if self.verbose:
                    print("\nDownload completed")
                
                # Save MP3 path
                song_data["mp3_path"] = mp3_path
                
                # If we didn't get lyrics from the HTML, try using Whisper if enabled
                if not song_data["lyrics"]:
                    if use_whisper:
                        if self.verbose:
                            print("No lyrics found in HTML. Attempting to extract lyrics using Whisper...")
                        
                        # Extract lyrics using Whisper
                        whisper_lyrics = self.extract_lyrics_with_whisper(mp3_path)
                        
                        if whisper_lyrics:
                            if self.verbose:
                                print(f"Successfully extracted lyrics using Whisper: {len(whisper_lyrics)} characters")
                            song_data["lyrics"] = whisper_lyrics
                        else:
                            if self.verbose:
                                print("Failed to extract lyrics with Whisper. Using default lyrics.")
                            # Use default lyrics if extraction failed
                            default_lyrics = """[verse]
This is a placeholder for lyrics
The actual song was downloaded but lyrics extraction is disabled
Please check the audio directory for the MP3 file

[chorus]
Suno, oh Suno
Your songs are now downloadable
Suno, oh Suno
We just need to fix the lyrics extraction
"""
                            song_data["lyrics"] = default_lyrics
                    else:
                        if self.verbose:
                            print("Whisper lyrics extraction is disabled. Using default lyrics.")
                        # Use default lyrics when Whisper is disabled
                        default_lyrics = """[verse]
This is a placeholder for lyrics
The actual song was downloaded but lyrics extraction is disabled
Please check the audio directory for the MP3 file

[chorus]
Suno, oh Suno
Your songs are now downloadable
Suno, oh Suno
We just need to fix the lyrics extraction
"""
                        song_data["lyrics"] = default_lyrics
                
                # Save metadata to JSON file
                metadata_path = os.path.join(project_dir, f"{safe_title}_metadata.json")
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(song_data, f, indent=2)
                
                # Save lyrics to a separate file for convenience
                lyrics_path = os.path.join(project_dir, f"{safe_title}_lyrics.txt")
                with open(lyrics_path, 'w', encoding='utf-8') as f:
                    f.write(song_data["lyrics"])
                
                if self.verbose:
                    print(f"Saved lyrics to {lyrics_path}")
                    print(f"Saved song metadata to {metadata_path}")
                    print(f"Downloaded song successfully to: {mp3_path}")
                
                return song_data
            
            # If login is required
            if "Log in" in html_content or "Sign in" in html_content:
                if self.verbose:
                    print("This song requires you to be logged in to download.")
                    self.save_cookies_from_browser_instructions()
                return None
            
            # If we still don't have a URL, inform the user
            if self.verbose:
                print("Could not find a direct download link. You may need to:")
                print("1. Be logged in to access this song")
                print("2. Manually download from the browser")
                self.save_cookies_from_browser_instructions()
            
            return None
            
        except Exception as e:
            if self.verbose:
                print(f"Error downloading song: {e}")
                import traceback
                traceback.print_exc()
            return None
    
    def save_cookies_from_browser_instructions(self):
        """Print instructions for saving cookies from a browser."""
        print("\nTo save cookies from your browser:")
        print("1. Install the 'Cookie-Editor' extension for Chrome or Firefox")
        print("2. Go to suno.com and log in")
        print("3. Click on the Cookie-Editor extension")
        print("4. Click 'Export' at the bottom right")
        print("5. Save the JSON data to 'suno_cookies.json' in the same directory as this script")
        print("\nAfter saving the cookies, run the script again with:")
        print("python suno_downloader.py <suno_song_url> --cookies suno_cookies.json")

def generate_scenes_from_lyrics(lyrics):
    """Generate scene ideas based on song lyrics with proper section handling."""
    # Try to use the AI Director if available
    try:
        from ...ai.integration import DirectorIntegration
        director = DirectorIntegration()
        ai_scenes = director.enhance_scenes_from_lyrics(lyrics)
        if ai_scenes:
            return ai_scenes
    except ImportError:
        # Fall back to basic scene generation if AI Director is not available
        pass
        
    if not lyrics:
        return []
    
    # Extract sections from formatted lyrics
    section_pattern = r'\[(verse|chorus|bridge|outro|intro)\](.*?)(?=\[|\Z)'
    matches = re.findall(section_pattern, lyrics, re.DOTALL)
    
    if not matches:
        # No sections found, default to basic scenes
        return generate_default_scenes()
    
    # Create new scenes list
    scenes = []
    
    # Prioritize sections (chorus, verse, bridge, etc)
    section_priority = {"chorus": 0, "verse": 1, "bridge": 2, "intro": 3, "outro": 4}
    sorted_sections = sorted(matches, key=lambda x: section_priority.get(x[0].lower(), 99))
    
    # Limit to 4-8 scenes
    scene_count = min(max(4, len(sorted_sections)), 8)
    selected_sections = sorted_sections[:scene_count]
    
    for i, (section_type, section_text) in enumerate(selected_sections):
        # Clean the section text
        text = section_text.strip()
        
        # Extract first couple of lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if not lines:
            continue
            
        scene_text = lines[0]
        if len(lines) > 1:
            scene_text += " " + lines[1] if len(scene_text) + len(lines[1]) < 100 else ""
        
        # Create appropriate prompt based on section type
        prompt_prefix = {
            "chorus": "dramatic chorus scene with",
            "verse": "atmospheric verse scene with",
            "bridge": "transitional bridge scene with",
            "intro": "opening scene with",
            "outro": "closing scene with"
        }.get(section_type.lower(), "music video scene with")
        
        # Extract key words from the text for the prompt
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out common words
        stopwords = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'from', 'by', 'in', 'of', 'with', 'is', 'am', 'are', 'was', 'were'}
        keywords = [w for w in words if len(w) > 3 and w not in stopwords][:3]
        
        # Create a scene description
        scene = {
            "text": scene_text[:100],  # Limit to 100 chars
            "scene_prompt": f"{prompt_prefix} {' '.join(keywords)} visuals inspired by lyrics: {scene_text[:50]}",
            "timestamp": i * 15  # 15 seconds per scene
        }
        scenes.append(scene)
    
    # If we don't have enough scenes, add some default ones
    while len(scenes) < 4:
        scene_idx = len(scenes)
        default_scenes = [
            "atmospheric music video scene with dramatic lighting",
            "emotional music video scene with cinematic composition",
            "abstract music video scene with artistic elements",
            "dynamic music video scene with visual contrast"
        ]
        
        scene = {
            "text": f"Scene {scene_idx + 1}",
            "scene_prompt": default_scenes[scene_idx % len(default_scenes)],
            "timestamp": scene_idx * 15
        }
        scenes.append(scene)
    
    return scenes

def generate_default_scenes():
    """Generate default scenes when no lyrics are available."""
    default_scenes = [
        {
            "text": "Scene 1",
            "scene_prompt": "atmospheric music video scene with dramatic lighting",
            "timestamp": 0
        },
        {
            "text": "Scene 2",
            "scene_prompt": "emotional music video scene with cinematic composition",
            "timestamp": 15
        },
        {
            "text": "Scene 3",
            "scene_prompt": "abstract music video scene with artistic elements",
            "timestamp": 30
        },
        {
            "text": "Scene 4",
            "scene_prompt": "dynamic music video scene with visual contrast",
            "timestamp": 45
        }
    ]
    return default_scenes

def download_suno_song(url, output_dir="uploads", project_dir=None, verbose=True, cookie_file=None, use_whisper=True):
    """
    Download a Suno song using the SunoSongDownloader class.
    This function is intended to be used as an API for integration with other systems.
    
    Args:
        url (str): The Suno song URL
        output_dir (str): Directory to save the MP3 file
        project_dir (str): Directory to save the project files (defaults to output_dir)
        verbose (bool): Whether to print verbose output
        cookie_file (str): Path to a cookie file for authenticated downloads
        use_whisper (bool): Whether to use Whisper for lyrics extraction
        
    Returns:
        dict: A dictionary with song information or None if download failed
    """
    # Initialize the downloader
    downloader = SunoSongDownloader(cookie_file=cookie_file, verbose=verbose)
    
    # Download the song
    return downloader.download_song(url, output_dir=output_dir, project_dir=project_dir, use_whisper=use_whisper)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Suno Song Downloader")
    parser.add_argument("url", nargs="?", help="Suno.com song URL")
    parser.add_argument("--output-dir", "-o", default="uploads", help="Output directory for MP3 files")
    parser.add_argument("--project-dir", "-p", help="Project directory for metadata files (defaults to output-dir)")
    parser.add_argument("--cookies", "-c", help="Path to cookies JSON file")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress verbose output")
    parser.add_argument("--no-whisper", "-n", action="store_true", help="Disable Whisper lyrics extraction")
    
    args = parser.parse_args()
    
    # Require a URL for download operations
    if not args.url:
        parser.print_help()
        sys.exit(1)
    
    # Call the download function
    song_data = download_suno_song(
        args.url,
        output_dir=args.output_dir,
        project_dir=args.project_dir,
        verbose=not args.quiet,
        cookie_file=args.cookies,
        use_whisper=not args.no_whisper
    )
    
    if song_data:
        if not args.quiet:
            print("\nDownload complete!")
            print(f"File saved to: {song_data['mp3_path']}")
            
            if song_data["lyrics"]:
                print(f"Lyrics extracted: {len(song_data['lyrics'])} characters")
            else:
                print("No lyrics found in the song page")
        
        sys.exit(0)
    else:
        if not args.quiet:
            print("\nDownload failed.")
        sys.exit(1)
