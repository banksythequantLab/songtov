/**
 * MaiVid Studio - Timeline JavaScript
 * Handles timeline-specific functionality including:
 * - Loading storyboard data into the timeline
 * - Drag and drop scene ordering
 * - Clip duration and effect management
 * - Transition control
 * - Audio synchronization
 * - Video generation
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const timelineTrack = document.getElementById('timeline-track');
    const sceneThumbnails = document.getElementById('scene-thumbnails');
    const clipPropertiesForm = document.getElementById('clip-properties-form');
    const clipDuration = document.getElementById('clip-duration');
    const clipMotion = document.getElementById('clip-motion');
    const transitionType = document.getElementById('transition-type');
    const videoTitleInput = document.getElementById('video-title');
    const videoResolution = document.getElementById('video-resolution');
    const videoFormat = document.getElementById('video-format');
    const videoPreviewContainer = document.getElementById('video-preview-container');
    const videoPreview = document.getElementById('video-preview');
    const audioPlayer = document.getElementById('timeline-audio-player');
    
    // Buttons
    const addTransitionBtn = document.getElementById('add-transition-btn');
    const previewSegmentBtn = document.getElementById('preview-segment-btn');
    const updateClipBtn = document.getElementById('update-clip-btn');
    const generateVideoBtn = document.getElementById('generate-video-btn');
    const downloadVideoBtn = document.getElementById('download-video-btn');
    
    // Project data from localStorage
    let projectData = {
        audioPath: null,
        lyrics: null,
        metadata: null,
        concept: null,
        storyline: null,
        scenes: [],
        storyboard: [],
        timeline: []
    };
    
    // Currently selected clip
    let selectedClipId = null;
    
    // Load project data from localStorage
    const savedProject = localStorage.getItem('maivid_project');
    if (savedProject) {
        try {
            projectData = JSON.parse(savedProject);
            console.log('Loaded project data:', projectData);
            
            // Initialize timeline array if it doesn't exist
            if (!projectData.timeline) {
                projectData.timeline = [];
            }
            
            // Initialize with storyboard if timeline is empty
            if (projectData.timeline.length === 0 && projectData.storyboard && projectData.storyboard.length > 0) {
                initializeTimeline();
            } else {
                // Load existing timeline
                renderTimeline();
            }
            
            // Populate scene library
            renderSceneLibrary();
            
            // Load video title from metadata if available
            if (projectData.metadata && projectData.metadata.title) {
                videoTitleInput.value = projectData.metadata.title + " - Music Video";
            }
        } catch (e) {
            console.error('Error parsing saved project data:', e);
            showAlert('Error loading project data. Please start over.', 'danger');
        }
    } else {
        showAlert('No project data found. Please start from the beginning.', 'warning');
        setTimeout(() => {
            window.location.href = '/';
        }, 3000);
    }
    
    /**
     * Initialize the timeline with storyboard data
     */
    function initializeTimeline() {
        // Sort storyboard frames by order
        const sortedFrames = [...projectData.storyboard].sort((a, b) => a.order - b.order);
        
        // Create timeline clips from storyboard frames
        projectData.timeline = sortedFrames.map((frame, index) => {
            // Find scene for this frame
            const scene = projectData.scenes.find(s => s.id === frame.sceneId);
            
            return {
                id: `clip_${Date.now()}_${index}`,
                frameId: frame.id,
                sceneId: frame.sceneId,
                duration: frame.duration || 3,
                motion: frame.shotType === 'close_up' ? 'zoom' : (frame.shotType === 'wide_shot' ? 'pan' : 'ken_burns'),
                transition: frame.transition || 'fade',
                imageUrl: scene ? scene.image_url : '/static/img/placeholder-image.png',
                order: index,
                description: frame.description || '',
                lyrics: frame.lyrics || ''
            };
        });
        
        // Save to localStorage
        saveProjectData();
        
        // Render the timeline
        renderTimeline();
    }
    
    /**
     * Render the timeline based on project data
     */
    function renderTimeline() {
        if (!projectData.timeline || projectData.timeline.length === 0) {
            // Show empty state
            timelineTrack.innerHTML = `
                <div class="alert alert-info my-4 mx-3">
                    <i class="fas fa-info-circle me-2"></i>
                    Your timeline is empty. Drag scenes from the library to add them to the timeline.
                </div>
            `;
            return;
        }
        
        // Sort clips by order
        const sortedClips = [...projectData.timeline].sort((a, b) => a.order - b.order);
        
        // Clear existing clips
        timelineTrack.innerHTML = '';
        
        // Add each clip to the timeline
        sortedClips.forEach((clip, index) => {
            // Create clip element
            const clipElement = document.createElement('div');
            clipElement.className = 'timeline-clip';
            clipElement.dataset.id = clip.id;
            clipElement.draggable = true;
            
            // Set clip width based on duration
            const baseWidth = 80;
            const durationFactor = clip.duration / 3; // Base of 3 seconds
            clipElement.style.width = `${baseWidth * durationFactor}px`;
            
            // Set clip content
            clipElement.innerHTML = `
                <div class="label">${clip.description || `Clip ${index + 1}`}</div>
                <img src="${clip.imageUrl}" alt="Clip ${index + 1}">
                <div class="duration">${clip.duration}s</div>
            `;
            
            // Append clip to timeline
            timelineTrack.appendChild(clipElement);
            
            // Add transition marker if not the last clip
            if (index < sortedClips.length - 1) {
                const transitionElement = document.createElement('div');
                transitionElement.className = 'transition-marker';
                transitionElement.title = getTransitionName(clip.transition);
                transitionElement.innerHTML = getTransitionIcon(clip.transition);
                transitionElement.dataset.clipId = clip.id;
                
                // Add transition click event
                transitionElement.addEventListener('click', function() {
                    editTransition(clip.id);
                });
                
                // Append transition to timeline
                timelineTrack.appendChild(transitionElement);
            }
        });
        
        // Add clip click events
        document.querySelectorAll('.timeline-clip').forEach(clip => {
            clip.addEventListener('click', function() {
                selectClip(this.dataset.id);
            });
            
            // Add drag events
            clip.addEventListener('dragstart', handleDragStart);
        });
        
        // Initialize drag-and-drop
        initDragDrop();
    }
    
    /**
     * Render the scene library
     */
    function renderSceneLibrary() {
        if (!projectData.scenes || projectData.scenes.length === 0) {
            sceneThumbnails.innerHTML = `
                <div class="alert alert-warning">
                    <small>No scenes available. Please create scenes first.</small>
                </div>
            `;
            return;
        }
        
        // Clear existing thumbnails
        sceneThumbnails.innerHTML = '';
        
        // Add each scene to the library
        projectData.scenes.forEach(scene => {
            const thumbnailElement = document.createElement('div');
            thumbnailElement.className = 'p-1';
            thumbnailElement.draggable = true;
            thumbnailElement.dataset.id = scene.id;
            thumbnailElement.dataset.type = 'scene';
            
            thumbnailElement.innerHTML = `
                <img src="${scene.image_url || '/static/img/placeholder-image.png'}" 
                     class="img-thumbnail" 
                     style="width: 80px; height: 60px;" 
                     alt="${scene.description || 'Scene'}">
            `;
            
            // Add drag events
            thumbnailElement.addEventListener('dragstart', handleDragStart);
            
            // Append to scene library
            sceneThumbnails.appendChild(thumbnailElement);
        });
    }
    
    /**
     * Select a clip for editing
     */
    function selectClip(clipId) {
        // Update selection state
        selectedClipId = clipId;
        
        // Clear all selected clips
        document.querySelectorAll('.timeline-clip').forEach(clip => {
            clip.classList.remove('selected');
        });
        
        // Highlight selected clip
        const clipElement = document.querySelector(`.timeline-clip[data-id="${clipId}"]`);
        if (clipElement) {
            clipElement.classList.add('selected');
        }
        
        // Get clip data
        const clip = projectData.timeline.find(c => c.id === clipId);
        if (!clip) {
            console.error('Clip not found:', clipId);
            return;
        }
        
        // Set form values
        clipDuration.value = clip.duration || 3;
        clipMotion.value = clip.motion || 'zoom';
        
        // Find the scene for this clip
        const scene = projectData.scenes.find(s => s.id === clip.sceneId);
        if (scene) {
            // Show description in the alert
            showAlert(`Selected: ${scene.description || 'Unnamed scene'}`, 'info');
        }
    }
    
    /**
     * Edit the transition for a clip
     */
    function editTransition(clipId) {
        // Get clip data
        const clip = projectData.timeline.find(c => c.id === clipId);
        if (!clip) {
            console.error('Clip not found:', clipId);
            return;
        }
        
        // Set transition selector value
        transitionType.value = clip.transition || 'fade';
        
        // Show transition alert
        showAlert('Select a transition type and click "Add Transition"', 'info');
        
        // Set selected clip for transition
        selectedClipId = clipId;
    }
    
    /**
     * Update transition for selected clip
     */
    function updateTransition() {
        if (!selectedClipId) {
            showAlert('No clip selected for transition', 'warning');
            return;
        }
        
        // Get clip data
        const clip = projectData.timeline.find(c => c.id === selectedClipId);
        if (!clip) {
            console.error('Clip not found:', selectedClipId);
            return;
        }
        
        // Update transition
        clip.transition = transitionType.value;
        
        // Save to localStorage
        saveProjectData();
        
        // Render the timeline
        renderTimeline();
        
        // Show success message
        showAlert('Transition updated', 'success');
    }
    
    /**
     * Update clip properties
     */
    function updateClipProperties() {
        if (!selectedClipId) {
            showAlert('No clip selected', 'warning');
            return;
        }
        
        // Get clip data
        const clip = projectData.timeline.find(c => c.id === selectedClipId);
        if (!clip) {
            console.error('Clip not found:', selectedClipId);
            return;
        }
        
        // Update clip properties
        clip.duration = parseFloat(clipDuration.value) || 3;
        clip.motion = clipMotion.value;
        
        // Save to localStorage
        saveProjectData();
        
        // Render the timeline
        renderTimeline();
        
        // Re-select the clip
        selectClip(selectedClipId);
        
        // Show success message
        showAlert('Clip properties updated', 'success');
    }
    
    /**
     * Add a new clip from a scene
     */
    function addClipFromScene(sceneId, position = null) {
        // Find scene data
        const scene = projectData.scenes.find(s => s.id === sceneId);
        if (!scene) {
            console.error('Scene not found:', sceneId);
            return;
        }
        
        // Get maximum order or use position if specified
        let order;
        if (position !== null) {
            // Shift all clips at or after the position
            projectData.timeline.forEach(clip => {
                if (clip.order >= position) {
                    clip.order += 1;
                }
            });
            order = position;
        } else {
            order = Math.max(...projectData.timeline.map(c => c.order), -1) + 1;
        }
        
        // Create new clip
        const newClip = {
            id: `clip_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
            sceneId: sceneId,
            duration: parseFloat(clipDuration.value) || 3,
            motion: clipMotion.value || 'zoom',
            transition: transitionType.value || 'fade',
            imageUrl: scene.image_url || '/static/img/placeholder-image.png',
            order: order,
            description: scene.description || '',
            lyrics: scene.lyrics || ''
        };
        
        // Add to timeline
        projectData.timeline.push(newClip);
        
        // Save to localStorage
        saveProjectData();
        
        // Render the timeline
        renderTimeline();
        
        // Select the new clip
        selectClip(newClip.id);
        
        // Show success message
        showAlert('Scene added to timeline', 'success');
    }
    
    /**
     * Delete the selected clip
     */
    function deleteClip() {
        if (!selectedClipId) {
            showAlert('No clip selected', 'warning');
            return;
        }
        
        // Confirm deletion
        if (!confirm('Are you sure you want to delete this clip?')) {
            return;
        }
        
        // Get clip data to find its order
        const clip = projectData.timeline.find(c => c.id === selectedClipId);
        if (!clip) {
            console.error('Clip not found:', selectedClipId);
            return;
        }
        
        const deletedOrder = clip.order;
        
        // Remove from timeline
        projectData.timeline = projectData.timeline.filter(c => c.id !== selectedClipId);
        
        // Reorder remaining clips
        projectData.timeline.forEach(c => {
            if (c.order > deletedOrder) {
                c.order -= 1;
            }
        });
        
        // Save to localStorage
        saveProjectData();
        
        // Render the timeline
        renderTimeline();
        
        // Clear selection
        selectedClipId = null;
        
        // Show success message
        showAlert('Clip deleted', 'success');
    }
    
    /**
     * Preview a segment of the timeline
     */
    function previewSegment() {
        if (!selectedClipId) {
            showAlert('Select a clip to preview', 'warning');
            return;
        }
        
        // Get the selected clip
        const clip = projectData.timeline.find(c => c.id === selectedClipId);
        if (!clip) {
            return;
        }
        
        // Calculate approximate start time based on clip order
        let startTime = 0;
        const sortedClips = [...projectData.timeline].sort((a, b) => a.order - b.order);
        
        for (let i = 0; i < sortedClips.length; i++) {
            if (sortedClips[i].id === selectedClipId) {
                break;
            }
            startTime += sortedClips[i].duration;
        }
        
        // Set audio player time and play
        if (audioPlayer) {
            audioPlayer.currentTime = startTime;
            audioPlayer.play();
            
            // Highlight the clip with pulsing effect
            const clipElement = document.querySelector(`.timeline-clip[data-id="${selectedClipId}"]`);
            if (clipElement) {
                clipElement.style.animation = 'pulse 1s infinite';
                
                // Remove animation after clip duration
                setTimeout(() => {
                    clipElement.style.animation = '';
                    audioPlayer.pause();
                }, clip.duration * 1000);
            }
        }
        
        // Show preview message
        showAlert(`Previewing clip for ${clip.duration} seconds`, 'info');
    }
    
    /**
     * Generate the final video
     */
    function generateVideo() {
        if (!projectData.timeline || projectData.timeline.length === 0) {
            showAlert('Timeline is empty. Add clips first.', 'warning');
            return;
        }
        
        // Get video settings
        const videoTitle = videoTitleInput.value || 'Music Video';
        const resolution = videoResolution.value || '720p';
        const format = videoFormat.value || 'mp4';
        
        // Show loading
        showAlert('Preparing video job...', 'info');
        showLoading('Starting video generation...');
        
        // Sort clips by order
        const sortedClips = [...projectData.timeline].sort((a, b) => a.order - b.order);
        
        // Store all scenes for reference
        const allScenes = projectData.scenes || [];
        
        // Call API to create video
        fetch('/api/video/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                scenes: sortedClips.map(clip => {
                    // Find the scene for this clip
                    const scene = projectData.scenes.find(s => s.id === clip.sceneId);
                    
                    return {
                        id: clip.id,
                        scene_id: clip.sceneId,
                        image_path: scene ? scene.image_path : null,
                        image_url: scene ? scene.image_url : null,
                        duration: clip.duration,
                        motion: clip.motion,
                        zoom_factor: clip.zoom_factor || 1.2,
                        pan_x: clip.pan_x || 0,
                        pan_y: clip.pan_y || 0,
                        transition: clip.transition
                    };
                }),
                all_scenes: allScenes,
                audio_path: projectData.audioPath,
                video_title: videoTitle,
                resolution: resolution,
                format: format,
                transition_type: sortedClips.length > 0 ? (sortedClips[0].transition || 'fade') : 'fade',
                transition_duration: 1.0
            })
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.error) {
                showAlert(`Error: ${data.error}`, 'danger');
                return;
            }
            
            // Store job data
            projectData.videoJobId = data.job_id;
            projectData.expectedVideoUrl = data.expected_output;
            saveProjectData();
            
            // Show progress UI
            showVideoProgress(data.job_id);
            
            // Show info message
            showAlert('Video generation started! You can track the progress below.', 'info');
        })
        .catch(error => {
            hideLoading();
            showAlert(`Error: ${error.message}`, 'danger');
        });
    }
    
    /**
     * Show video generation progress
     */
    function showVideoProgress(jobId) {
        // Create progress container if it doesn't exist
        let progressContainer = document.getElementById('video-progress-container');
        if (!progressContainer) {
            progressContainer = document.createElement('div');
            progressContainer.id = 'video-progress-container';
            progressContainer.className = 'row mb-4';
            document.getElementById('video-preview-container').insertAdjacentElement('beforebegin', progressContainer);
        }
        
        // Create progress UI
        progressContainer.innerHTML = `
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h3 class="h5 mb-0">Video Rendering Progress</h3>
                    </div>
                    <div class="card-body">
                        <div class="progress mb-3" style="height: 25px;">
                            <div id="video-progress-bar" class="progress-bar progress-bar-striped progress-bar-animated" 
                                role="progressbar" style="width: 0%" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">
                                0%
                            </div>
                        </div>
                        <div id="video-progress-stage" class="text-center mb-3">Initializing...</div>
                        <div id="video-progress-details" class="small text-muted">Started just now</div>
                    </div>
                </div>
            </div>
        `;
        
        // Make progress container visible
        progressContainer.style.display = 'block';
        
        // Start progress polling
        pollVideoProgress(jobId);
    }
    
    /**
     * Poll video generation progress
     */
    let progressPoller = null;
    function pollVideoProgress(jobId) {
        // Clear any existing poller
        if (progressPoller) {
            clearInterval(progressPoller);
        }
        
        // Function to update progress UI
        const updateProgressUI = (progress) => {
            const progressBar = document.getElementById('video-progress-bar');
            const progressStage = document.getElementById('video-progress-stage');
            const progressDetails = document.getElementById('video-progress-details');
            
            if (progressBar && progressStage && progressDetails) {
                // Update progress bar
                const percent = Math.round(progress.overall_progress);
                progressBar.style.width = `${percent}%`;
                progressBar.setAttribute('aria-valuenow', percent);
                progressBar.textContent = `${percent}%`;
                
                // Update status class
                progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
                if (progress.status === 'completed') {
                    progressBar.className = 'progress-bar bg-success';
                } else if (progress.status === 'failed') {
                    progressBar.className = 'progress-bar bg-danger';
                }
                
                // Update stage text
                progressStage.textContent = progress.current_stage;
                
                // Calculate elapsed time
                const startTime = new Date(progress.started_at * 1000);
                const now = new Date();
                const elapsedSeconds = Math.floor((now - startTime) / 1000);
                const elapsedMinutes = Math.floor(elapsedSeconds / 60);
                const remainingSeconds = elapsedSeconds % 60;
                
                // Update details
                progressDetails.textContent = `Elapsed time: ${elapsedMinutes}m ${remainingSeconds}s`;
                
                // If completed or failed, stop polling and show result
                if (progress.status === 'completed') {
                    clearInterval(progressPoller);
                    progressPoller = null;
                    
                    // Update video preview
                    if (progress.video_path) {
                        // Store video data
                        projectData.videoPath = progress.video_path;
                        projectData.videoUrl = projectData.expectedVideoUrl;
                        saveProjectData();
                        
                        // Show video preview
                        if (videoPreview) {
                            videoPreview.src = projectData.videoUrl;
                            videoPreviewContainer.style.display = 'block';
                            videoPreview.scrollIntoView({ behavior: 'smooth' });
                        }
                        
                        // Show success message
                        showAlert('Video generated successfully!', 'success');
                    }
                } else if (progress.status === 'failed') {
                    clearInterval(progressPoller);
                    progressPoller = null;
                    
                    // Show error message
                    showAlert(`Video generation failed: ${progress.error}`, 'danger');
                }
            }
        };
        
        // Function to fetch progress
        const fetchProgress = () => {
            fetch(`/api/video/progress/${jobId}`)
                .then(response => response.json())
                .then(progress => {
                    if (progress.error) {
                        showAlert(`Error: ${progress.error}`, 'danger');
                        clearInterval(progressPoller);
                        progressPoller = null;
                        return;
                    }
                    
                    // Update UI with progress data
                    updateProgressUI(progress);
                })
                .catch(error => {
                    showAlert(`Error checking progress: ${error.message}`, 'danger');
                });
        };
        
        // Start polling
        fetchProgress(); // Initial fetch
        progressPoller = setInterval(fetchProgress, 3000); // Then every 3 seconds
    }
    
    /**
     * Download the generated video
     */
    function downloadVideo() {
        if (!projectData.videoUrl) {
            showAlert('No video to download. Generate a video first.', 'warning');
            return;
        }
        
        // Create a temporary link to trigger download
        const link = document.createElement('a');
        link.href = projectData.videoUrl;
        link.download = `${videoTitleInput.value || 'music_video'}.${videoFormat.value || 'mp4'}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    /**
     * Initialize drag and drop functionality
     */
    function initDragDrop() {
        // Make timeline track a drop target
        timelineTrack.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        });
        
        timelineTrack.addEventListener('drop', function(e) {
            e.preventDefault();
            
            // Get the dragged element ID and type
            const draggedId = e.dataTransfer.getData('text/plain');
            const draggedType = e.dataTransfer.getData('dragType');
            
            if (draggedType === 'scene') {
                // Adding a new scene from the library
                addClipFromScene(draggedId);
            } else if (draggedType === 'clip') {
                // Reordering clips
                reorderClips(draggedId, e.clientX);
            }
        });
    }
    
    /**
     * Handle drag start event
     */
    function handleDragStart(e) {
        // Store the element ID and type
        const id = this.dataset.id;
        const type = this.dataset.type || 'clip';
        
        e.dataTransfer.setData('text/plain', id);
        e.dataTransfer.setData('dragType', type);
        e.dataTransfer.effectAllowed = 'move';
    }
    
    /**
     * Reorder clips based on drop position
     */
    function reorderClips(draggedId, dropX) {
        // Get the dragged clip
        const draggedClip = projectData.timeline.find(c => c.id === draggedId);
        if (!draggedClip) return;
        
        // Find the position where the clip was dropped
        const clipElements = document.querySelectorAll('.timeline-clip');
        let targetOrder = projectData.timeline.length - 1;
        
        for (let i = 0; i < clipElements.length; i++) {
            const rect = clipElements[i].getBoundingClientRect();
            const clipMiddle = rect.left + rect.width / 2;
            
            if (dropX < clipMiddle) {
                const clipId = clipElements[i].dataset.id;
                const clip = projectData.timeline.find(c => c.id === clipId);
                if (clip) {
                    targetOrder = clip.order;
                    break;
                }
            }
        }
        
        // Update orders
        const oldOrder = draggedClip.order;
        
        if (oldOrder < targetOrder) {
            // Moving forward
            for (let clip of projectData.timeline) {
                if (clip.order > oldOrder && clip.order <= targetOrder) {
                    clip.order--;
                }
            }
        } else if (oldOrder > targetOrder) {
            // Moving backward
            for (let clip of projectData.timeline) {
                if (clip.order >= targetOrder && clip.order < oldOrder) {
                    clip.order++;
                }
            }
        } else {
            // Same position, no change needed
            return;
        }
        
        // Set new order for dragged clip
        draggedClip.order = targetOrder;
        
        // Save to localStorage
        saveProjectData();
        
        // Render the timeline
        renderTimeline();
    }
    
    /**
     * Save project data to localStorage
     */
    function saveProjectData() {
        localStorage.setItem('maivid_project', JSON.stringify(projectData));
    }
    
    /**
     * Get transition name
     */
    function getTransitionName(transition) {
        switch (transition) {
            case 'fade': return 'Fade';
            case 'wipe': return 'Wipe';
            case 'dissolve': return 'Dissolve';
            case 'none': return 'Cut (No Transition)';
            default: return 'Fade';
        }
    }
    
    /**
     * Get transition icon
     */
    function getTransitionIcon(transition) {
        switch (transition) {
            case 'fade': return '↔';
            case 'wipe': return '→';
            case 'dissolve': return '⊗';
            case 'none': return '∥';
            default: return '↔';
        }
    }
    
    /**
     * Show a loading indicator
     */
    function showLoading(message = 'Loading...') {
        // Create loading element
        const loadingEl = document.createElement('div');
        loadingEl.id = 'loading-indicator';
        loadingEl.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center';
        loadingEl.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
        loadingEl.style.zIndex = '9999';
        loadingEl.innerHTML = `
            <div class="bg-white p-4 rounded shadow-sm text-center">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="text-dark">${message}</div>
            </div>
        `;
        
        // Add to the page
        document.body.appendChild(loadingEl);
    }
    
    /**
     * Hide loading indicator
     */
    function hideLoading() {
        const loadingEl = document.getElementById('loading-indicator');
        if (loadingEl) {
            loadingEl.remove();
        }
    }
    
    /**
     * Show an alert message
     */
    function showAlert(message, type = 'info') {
        // Create alert element
        const alertEl = document.createElement('div');
        alertEl.className = `alert alert-${type} alert-dismissible fade show position-fixed bottom-0 end-0 m-3`;
        alertEl.style.zIndex = '9999';
        alertEl.role = 'alert';
        alertEl.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Add to the page
        document.body.appendChild(alertEl);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            alertEl.remove();
        }, 5000);
    }
    
    // Add event listeners
    if (addTransitionBtn) {
        addTransitionBtn.addEventListener('click', updateTransition);
    }
    
    if (previewSegmentBtn) {
        previewSegmentBtn.addEventListener('click', previewSegment);
    }
    
    if (updateClipBtn) {
        updateClipBtn.addEventListener('click', updateClipProperties);
    }
    
    if (generateVideoBtn) {
        generateVideoBtn.addEventListener('click', generateVideo);
    }
    
    if (downloadVideoBtn) {
        downloadVideoBtn.addEventListener('click', downloadVideo);
    }
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Delete key - delete selected clip
        if (e.key === 'Delete' && selectedClipId) {
            deleteClip();
        }
        
        // Space key - toggle audio playback
        if (e.code === 'Space' && audioPlayer) {
            if (audioPlayer.paused) {
                audioPlayer.play();
            } else {
                audioPlayer.pause();
            }
            e.preventDefault(); // Prevent page scroll
        }
    });
    
    // Set audio source if available
    if (audioPlayer && projectData.audioPath) {
        audioPlayer.src = `/uploads/${projectData.audioPath.split('/').pop()}`;
    }
    
    // Add a custom context menu for timeline clips
    document.addEventListener('contextmenu', function(e) {
        const clipElement = e.target.closest('.timeline-clip');
        if (clipElement) {
            e.preventDefault();
            
            // Select the clip
            selectClip(clipElement.dataset.id);
            
            // Create context menu
            const contextMenu = document.createElement('div');
            contextMenu.className = 'card position-absolute shadow-sm';
            contextMenu.style.left = `${e.pageX}px`;
            contextMenu.style.top = `${e.pageY}px`;
            contextMenu.style.zIndex = '9999';
            contextMenu.innerHTML = `
                <div class="list-group list-group-flush">
                    <button class="list-group-item list-group-item-action" id="ctx-edit">
                        <i class="fas fa-edit me-2"></i>Edit Properties
                    </button>
                    <button class="list-group-item list-group-item-action" id="ctx-duplicate">
                        <i class="fas fa-clone me-2"></i>Duplicate Clip
                    </button>
                    <button class="list-group-item list-group-item-action text-danger" id="ctx-delete">
                        <i class="fas fa-trash me-2"></i>Delete Clip
                    </button>
                </div>
            `;
            
            // Add to page
            document.body.appendChild(contextMenu);
            
            // Add event listeners
            document.getElementById('ctx-edit').addEventListener('click', function() {
                updateClipProperties();
                contextMenu.remove();
            });
            
            document.getElementById('ctx-duplicate').addEventListener('click', function() {
                // Get clip data
                const clip = projectData.timeline.find(c => c.id === selectedClipId);
                if (clip) {
                    addClipFromScene(clip.sceneId, clip.order + 1);
                }
                contextMenu.remove();
            });
            
            document.getElementById('ctx-delete').addEventListener('click', function() {
                deleteClip();
                contextMenu.remove();
            });
            
            // Remove on click outside
            document.addEventListener('click', function removeMenu() {
                contextMenu.remove();
                document.removeEventListener('click', removeMenu);
            });
        }
    });
    
    // Add keyframe animation to CSS
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
    `;
    document.head.appendChild(style);
});
