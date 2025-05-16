# MaiVid Studio Planning

## Project Overview

MaiVid Studio is an AI-driven music video generation system that converts audio tracks and lyrics into complete music videos. The platform enables users to control narrative elements, visual style, characters, and effects while leveraging AI to handle the creative heavy lifting.

## Key Components

### 1. Music & Lyrics Acquisition

#### Primary Method: URL Integration
- **Music URL Import**: Direct links to music platforms (e.g., https://suno.com/s/H6JQeAvqf4SgiFoF)
- **Automatic Download**: System downloads audio directly from supported platforms
- **Lyric Extraction**: Uses OpenAI Whisper for automatic lyrics extraction
- **Metadata Capture**: Collects artist, title, and genre information

#### Alternative Methods
- **Manual Lyric Input**: Text area for direct lyric entry
- **Audio Upload**: Option for local audio file upload
- **AI Lyric Generation**: For instrumental tracks

### 2. Concept Development

- **Interface Design**: Clean card-style layout with AI-driven content generation
- **Input Components**: Simple AI concept generation button
- **Development Process**: 
  - AI analyzes lyrics and automatically suggests concept
  - System generates style, mood, themes, and visual elements
  - Sample image is generated to visualize the concept
  - User can regenerate for alternative concepts
- **Format Selection**: Auto-detected from lyrical content
- **Visual Feedback**: Generated sample image to demonstrate the concept

### 3. Storyline Creation

- **Interface Design**: Multi-column layout
- **Navigation**: Horizontal progression indicator
- **Content Components**:
  - Primary storyline editor
  - Alternative storylines panel
  - Contextual suggestions based on music
- **Interactivity**: Drag-and-drop scene reordering

### 4. Settings & Cast

- **Interface Design**: Split-screen layout
- **Configuration Elements**:
  - Project name field with auto-save
  - Aspect ratio selector with previews
  - Video style selector with examples
- **Character Management**:
  - Character creation panel
  - Attribute editor
  - Relationship mapper

### 5. Scene Breakdown

- **Interface Design**: Scrollable document-style layout
- **Structural Elements**:
  - Project synopsis
  - Sequential scene blocks
  - In-line editing
- **Scene Components**:
  - Scene header with numbering
  - Location description
  - Emotional tone indicators
  - Technical notes

### 6. Storyboard Creation

- **Interface Design**: Filmstrip-style horizontal layout
- **Organizational Elements**:
  - Scene selector with thumbnails
  - Frame sequence with numbering
  - Zoom controls
- **Frame Components**:
  - Shot type selector
  - Composition tools
  - Character placement indicators
  - AI-prompt field

### 7. Timeline Editing

- **Interface Design**: Professional editing interface
- **Library Elements**:
  - Categorized assets panel
  - Search and filter functionality
  - Drag-and-drop asset browser
- **Timeline Components**:
  - Multi-track timeline with audio visualization
  - Frame-accurate playhead
  - Clip trimming tools
  - Transition indicators

### 8. Motion Editing

- **Interface Design**: Detailed editor with frame preview
- **Control Elements**:
  - Current frame display
  - Frame navigation controls
  - Tool palette
- **Editing Components**:
  - Shot customization fields
  - Prompt editor
  - Animation parameter controls
  - Scene sequence navigator

## Technical Architecture

### Frontend
- **Framework**: React.js
- **Styling**: TailwindCSS with Apple Card-inspired components
- **State Management**: Redux
- **Routing**: React Router
- **UI Components**: Custom components with Material UI base
- **Card Design**: Apple Card style with subtle shadows and animations
- **Showcase Feature**: Rotating gallery of AI-generated scene examples on homepage
- **Visual Elements**: Sample image generation for concepts and scenes

### Backend
- **API**: Flask (Python)
- **Authentication**: Firebase Auth
- **Database**: Firebase Firestore
- **Storage**: Firebase Storage
- **Media Processing**: FFmpeg

### UI Components

#### Workflow Progress Bar
- **Visual Style**: Pure Apple-inspired design with subtle shadows and spacing
- **Interactivity**: Highlights current step with Apple blue (#007AFF) and subtle elevation
- **Color Scheme**: 
  - Base: Light gray (#F2F2F7) - Apple Gray 6
  - Active: Apple blue (#007AFF)
  - Inactive: Apple gray (#E5E5EA) - Apple Gray 5
  - Text: Dark (#3A3F47) for inactive, White for active
- **Animation**: Subtle elevation for active step (2px rise)
- **Consistency**: Present across all main pages
- **Accessibility**: High contrast for readability
- **Format**: Numbered steps with centered text "1 · Music", "2 · Concept", etc.
- **Spacing**: 8px gap between steps for visual separation

### AI Integration
- **Image Generation**: ComfyUI with Stable Diffusion
- **Audio Analysis**: OpenAI Whisper
- **Text Generation**: LLM via API
- **Video Generation**: Custom pipeline with Deforum

### MCP Servers
- **Firebase MCP**: Database and authentication
- **ComfyUI MCP**: AI workflow processing
- **Memory MCP**: Context retention and knowledge graph
- **Task MCP**: Workflow coordination
- **GPU MCP**: Accelerated rendering

## Data Flow

1. **Input Processing**
   - Audio input → Lyric extraction → Metadata parsing
   - Story input → Segmentation → Scene planning

2. **Generation Pipeline**
   - Scene descriptions → Image prompts → ComfyUI generation
   - Timeline data → Frame assignment → Motion calculation

3. **Output Generation**
   - Generated frames → Motion application → Video rendering
   - Audio track → Synchronization → Final export

## Development Phases

### Phase 1: Core Functionality
- Music & Lyrics acquisition
- Basic concept development
- Simple scene generation
- Prototype video output

### Phase 2: Enhanced Creation
- Full storyline development
- Character creation system
- Storyboard functionality
- Advanced scene controls

### Phase 3: Production Quality
- Timeline editor
- Motion effects
- Export options
- Performance optimization

### Phase 4: Platform Integration
- User accounts
- Project saving/loading
- Sharing capabilities
- Template library

## Performance Considerations

- GPU-accelerated image generation
- Background processing for heavy tasks
- Caching of expensive operations
- Progressive loading of interface elements
- Optimized video processing

## Development Process

### Task Management Approach
- **Task Documentation**: Separate TASK.md and COMPLETED.md files
- **Task Organization**: 
  - TASK.md contains current, upcoming, and recently completed tasks
  - COMPLETED.md maintains full history of completed tasks by category
- **Task Transition Process**:
  1. Add completed tasks to "Recently Completed" section in TASK.md
  2. Use `tools/manage_tasks.py` script to move tasks to COMPLETED.md
  3. Tasks are automatically categorized and added to appropriate sections
- **Automation**: `update_tasks.bat` script for one-click task management
- **Benefits**: Eliminates need to recreate lengthy completed task lists

### Testing Strategy
- **UI Testing**: Puppeteer for automated UI validation
- **API Testing**: Dedicated test scripts for each API component
- **Integration Testing**: End-to-end tests for complete workflows
- **Visual Testing**: Puppeteer screenshots for visual regression
- **Performance Testing**: Metrics collection during runtime
- **Test Location**: All tests are stored in the `/tests` directory
- **Test Automation**: Master test runner script for comprehensive testing

## Dependencies

- FFmpeg for video processing
- ComfyUI for image generation
- Firebase SDK
- OpenAI Whisper
- Stable Diffusion models

## Future Enhancements

- Mobile application
- Collaborative editing
- Direct social media publishing
- Custom model training
- Audio effects and enhancement
- Text-to-speech narration
