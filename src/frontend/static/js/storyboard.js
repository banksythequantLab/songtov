/**
 * MaiVid Studio - Storyboard JavaScript
 * Handles storyboard-specific functionality including:
 * - Loading scenes into the storyboard
 * - Arranging frames in sequence
 * - Editing frame properties
 * - Managing transitions
 * - Preview functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const storyboardContainer = document.getElementById('storyboard-container');
    const storyboardFrames = document.getElementById('storyboard-frames');
    const emptyStoryboard = document.getElementById('empty-storyboard');
    const frameEditor = document.getElementById('frame-editor');
    const noFrameSelected = document.getElementById('no-frame-selected');
    const audioPlayer = document.getElementById('storyboard-audio-player');
    const audioInfo = document.getElementById('audio-info');
    const audioTimeline = document.getElementById('audio-timeline');
    
    // Form elements
    const frameShotType = document.getElementById('frame-shot-type');
    const frameDuration = document.getElementById('frame-duration');
    const frameTransition = document.getElementById('frame-transition');
    const frameDescription = document.getElementById('frame-description');
    const frameLyrics = document.getElementById('frame-lyrics');
    const defaultDuration = document.getElementById('default-duration');
    const defaultTransition = document.getElementById('default-transition');
    
    // Buttons
    const addFrameBtn = document.getElementById('add-frame-btn');
    const saveFrameBtn = document.getElementById('save-frame-btn');
    const deleteFrameBtn = document.getElementById('delete-frame-btn');
    const autoArrangeBtn = document.getElementById('auto-arrange-btn');
    const playStoryboardBtn = document.getElementById('play-storyboard-btn');
    const resetStoryboardBtn = document.getElementById('reset-storyboard-btn');
    const continueToTimelineBtn = document.getElementById('continue-to-timeline-btn');
    
    // Shot type selector
    const shotTypeOptions = document.querySelectorAll('.shot-type-option');
    
    // Project data from localStorage
    let projectData = {
        audioPath: null,
        lyrics: null,
        metadata: null,
        concept: null,
        storyline: null,
        scenes: [],
        storyboard: []
    };
    
    // Currently selected frame
    let selectedFrameId = null;
    let selectedShotType = null;
    
    // Load project data from localStorage
    const savedProject = localStorage.getItem('maivid_project');
    if (savedProject) {
        try {
            projectData = JSON.parse(savedProject);
            console.log('Loaded project data:', projectData);
            
            // Create storyboard array if it doesn't exist
            if (!projectData.storyboard) {
                projectData.storyboard = [];
            }
            
            // Initialize with scenes if storyboard is empty
            if (projectData.storyboard.length === 0 && projectData.scenes && projectData.scenes.length > 0) {
                initializeStoryboard();
            } else {
                // Load existing storyboard
                renderStoryboard();
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
     * Initialize the storyboard with scenes from project data
     */
    function initializeStoryboard() {
        projectData.storyboard = projectData.scenes.map((scene, index) => {
            return {
                id: `frame_${Date.now()}_${index}`,
                sceneId: scene.id,
                shotType: 'medium_shot',
                description: scene.description || '',
                duration: parseFloat(scene.duration) || 3,
                transition: 'fade',
                lyrics: scene.lyrics || '',
                imageUrl: scene.image_url || '',
                order: index
            };
        });
        
        // Save to localStorage
        saveProjectData();
        
        // Render the storyboard
        renderStoryboard();
    }
    
    /**
     * Render the storyboard based on project data
     */
    function renderStoryboard() {
        if (!projectData.storyboard || projectData.storyboard.length === 0) {
            // Show empty state
            storyboardFrames.classList.add('d-none');
            emptyStoryboard.classList.remove('d-none');
            return;
        }
        
        // Show storyboard frames
        storyboardFrames.classList.remove('d-none');
        emptyStoryboard.classList.add('d-none');
        
        // Sort frames by order
        const sortedFrames = [...projectData.storyboard].sort((a, b) => a.order - b.order);
        
        // Clear existing frames
        storyboardFrames.innerHTML = '';
        
        // Add each frame to the storyboard
        sortedFrames.forEach((frame, index) => {
            const frameElement = document.createElement('div');
            frameElement.className = 'storyboard-frame card shadow-sm';
            frameElement.dataset.id = frame.id;
            frameElement.dataset.order = frame.order;
            
            // Find matching scene
            const scene = projectData.scenes.find(s => s.id === frame.sceneId);
            const imageSrc = scene ? scene.image_url : '/static/img/placeholder-image.png';
            
            // Create frame HTML
            frameElement.innerHTML = `
                <div class="position-relative">
                    <img src="${imageSrc}" class="frame-preview" alt="Frame ${index + 1}">
                    <div class="frame-number">${index + 1}</div>
                    <div class="frame-duration">${frame.duration}s</div>
                    <div class="frame-options">
                        <div class="frame-option-btn edit-frame-btn" title="Edit Frame">
                            <i class="fas fa-edit"></i>
                        </div>
                        <div class="frame-option-btn clone-frame-btn" title="Clone Frame">
                            <i class="fas fa-clone"></i>
                        </div>
                    </div>
                    ${index < sortedFrames.length - 1 ? `
                        <div class="transition-overlay" title="${getTransitionName(frame.transition)}">
                            <i class="${getTransitionIcon(frame.transition)}"></i>
                        </div>
                    ` : ''}
                </div>
                <div class="card-body p-2">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <small class="text-muted">Shot: ${getShotTypeName(frame.shotType)}</small>
                        <span class="badge bg-${getShotTypeColor(frame.shotType)}">
                            <i class="${getShotTypeIcon(frame.shotType)}"></i>
                        </span>
                    </div>
                    <div class="frame-lyrics text-muted">
                        ${frame.lyrics || 'No lyrics associated'}
                    </div>
                </div>
            `;
            
            // Add click event to select the frame
            frameElement.addEventListener('click', function(e) {
                // Don't select if clicking on options
                if (e.target.closest('.frame-option-btn')) {
                    return;
                }
                
                selectFrame(frame.id);
            });
            
            // Add to storyboard
            storyboardFrames.appendChild(frameElement);
        });
        
        // Add edit button events
        document.querySelectorAll('.edit-frame-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const frameId = this.closest('.storyboard-frame').dataset.id;
                selectFrame(frameId);
            });
        });
        
        // Add clone button events
        document.querySelectorAll('.clone-frame-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const frameId = this.closest('.storyboard-frame').dataset.id;
                cloneFrame(frameId);
            });
        });
        
        // Initialize sortable
        initSortable();
        
        // Update audio timeline
        updateAudioTimeline();
    }
    
    /**
     * Initialize Sortable.js for drag and drop reordering
     */
    function initSortable() {
        if (storyboardFrames) {
            new Sortable(storyboardFrames, {
                animation: 150,
                ghostClass: 'sortable-ghost',
                onEnd: function(evt) {
                    // Update order of frames
                    const frames = storyboardFrames.querySelectorAll('.storyboard-frame');
                    frames.forEach((frame, index) => {
                        const frameId = frame.dataset.id;
                        const frameData = projectData.storyboard.find(f => f.id === frameId);
                        if (frameData) {
                            frameData.order = index;
                        }
                    });
                    
                    // Save changes
                    saveProjectData();
                    
                    // Re-render to update frame numbers
                    renderStoryboard();
                }
            });
        }
    }
    
    /**
     * Select a frame for editing
     */
    function selectFrame(frameId) {
        // Update selection state
        selectedFrameId = frameId;
        
        // Clear all selected frames
        document.querySelectorAll('.storyboard-frame').forEach(frame => {
            frame.classList.remove('selected');
        });
        
        // Highlight selected frame
        const frameElement = document.querySelector(`.storyboard-frame[data-id="${frameId}"]`);
        if (frameElement) {
            frameElement.classList.add('selected');
        }
        
        // Get frame data
        const frame = projectData.storyboard.find(f => f.id === frameId);
        if (!frame) {
            console.error('Frame not found:', frameId);
            return;
        }
        
        // Show frame editor
        noFrameSelected.classList.add('d-none');
        frameEditor.classList.remove('d-none');
        
        // Set form values
        frameShotType.value = frame.shotType || 'medium_shot';
        frameDuration.value = frame.duration || 3;
        frameTransition.value = frame.transition || 'fade';
        frameDescription.value = frame.description || '';
        frameLyrics.value = frame.lyrics || '';
    }
    
    /**
     * Clone a frame
     */
    function cloneFrame(frameId) {
        // Get original frame data
        const originalFrame = projectData.storyboard.find(f => f.id === frameId);
        if (!originalFrame) {
            console.error('Frame not found:', frameId);
            return;
        }
        
        // Get maximum order
        const maxOrder = Math.max(...projectData.storyboard.map(f => f.order), 0);
        
        // Create new frame
        const newFrame = {
            ...originalFrame,
            id: `frame_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
            order: maxOrder + 1
        };
        
        // Add to storyboard
        projectData.storyboard.push(newFrame);
        
        // Save changes
        saveProjectData();
        
        // Re-render storyboard
        renderStoryboard();
        
        // Show success message
        showAlert('Frame cloned successfully', 'success');
    }
    
    /**
     * Save frame changes
     */
    function saveFrameChanges() {
        if (!selectedFrameId) {
            showAlert('No frame selected', 'warning');
            return;
        }
        
        // Get frame data
        const frame = projectData.storyboard.find(f => f.id === selectedFrameId);
        if (!frame) {
            console.error('Frame not found:', selectedFrameId);
            return;
        }
        
        // Update frame data
        frame.shotType = frameShotType.value;
        frame.duration = parseFloat(frameDuration.value);
        frame.transition = frameTransition.value;
        frame.description = frameDescription.value;
        frame.lyrics = frameLyrics.value;
        
        // Save changes
        saveProjectData();
        
        // Re-render storyboard
        renderStoryboard();
        
        // Re-select frame
        selectFrame(selectedFrameId);
        
        // Show success message
        showAlert('Frame updated successfully', 'success');
    }
    
    /**
     * Delete a frame
     */
    function deleteFrame() {
        if (!selectedFrameId) {
            showAlert('No frame selected', 'warning');
            return;
        }
        
        // Confirm deletion
        if (!confirm('Are you sure you want to delete this frame?')) {
            return;
        }
        
        // Remove frame from storyboard
        projectData.storyboard = projectData.storyboard.filter(f => f.id !== selectedFrameId);
        
        // Reorder remaining frames
        projectData.storyboard.forEach((frame, index) => {
            frame.order = index;
        });
        
        // Save changes
        saveProjectData();
        
        // Re-render storyboard
        renderStoryboard();
        
        // Show editor closed state
        selectedFrameId = null;
        noFrameSelected.classList.remove('d-none');
        frameEditor.classList.add('d-none');
        
        // Show success message
        showAlert('Frame deleted successfully', 'success');
    }
    
    /**
     * Add a new empty frame
     */
    function addEmptyFrame() {
        // Find all available scenes
        if (!projectData.scenes || projectData.scenes.length === 0) {
            showAlert('No scenes available. Please create scenes first.', 'warning');
            return;
        }
        
        // Get maximum order
        const maxOrder = Math.max(...projectData.storyboard.map(f => f.order), -1);
        
        // Create new frame
        const newFrame = {
            id: `frame_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
            sceneId: projectData.scenes[0].id,
            shotType: 'medium_shot',
            description: '',
            duration: parseFloat(defaultDuration.value) || 3,
            transition: defaultTransition.value || 'fade',
            lyrics: '',
            order: maxOrder + 1
        };
        
        // Add to storyboard
        projectData.storyboard.push(newFrame);
        
        // Save changes
        saveProjectData();
        
        // Re-render storyboard
        renderStoryboard();
        
        // Select the new frame
        selectFrame(newFrame.id);
        
        // Show success message
        showAlert('New frame added', 'success');
    }
    
    /**
     * Auto-arrange frames based on audio timing
     */
    function autoArrangeFrames() {
        if (!projectData.storyboard || projectData.storyboard.length === 0) {
            showAlert('No frames to arrange', 'warning');
            return;
        }
        
        // Get audio duration
        const audioDuration = audioPlayer.duration || 180; // Default to 3 minutes if not loaded
        
        // Calculate frame duration
        const frameDuration = audioDuration / projectData.storyboard.length;
        
        // Update all frames
        projectData.storyboard.forEach((frame, index) => {
            frame.duration = Math.max(2, Math.min(10, Math.round(frameDuration)));
        });
        
        // Save changes
        saveProjectData();
        
        // Re-render storyboard
        renderStoryboard();
        
        // Update timeline
        updateAudioTimeline();
        
        // Show success message
        showAlert('Frames auto-arranged based on audio duration', 'success');
    }
    
    /**
     * Preview the storyboard (simulated)
     */
    function playStoryboardPreview() {
        if (!projectData.storyboard || projectData.storyboard.length === 0) {
            showAlert('No frames to preview', 'warning');
            return;
        }
        
        // Show preview message
        showAlert('Preview mode started. Frames will highlight in sequence.', 'info');
        
        // Start the preview
        let currentIndex = 0;
        const frames = document.querySelectorAll('.storyboard-frame');
        
        // Remove all highlights
        frames.forEach(frame => frame.classList.remove('selected'));
        
        // Highlight first frame
        if (frames[0]) {
            frames[0].classList.add('selected');
            frames[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' });
        }
        
        // Start audio
        audioPlayer.currentTime = 0;
        audioPlayer.play();
        
        // Preview interval
        const previewInterval = setInterval(() => {
            // Move to next frame
            currentIndex++;
            
            // End preview if done
            if (currentIndex >= frames.length) {
                clearInterval(previewInterval);
                showAlert('Preview completed', 'success');
                return;
            }
            
            // Remove previous highlight
            frames.forEach(frame => frame.classList.remove('selected'));
            
            // Highlight current frame
            if (frames[currentIndex]) {
                frames[currentIndex].classList.add('selected');
                frames[currentIndex].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' });
            }
        }, 2000); // Preview each frame for 2 seconds
    }
    
    /**
     * Reset the storyboard
     */
    function resetStoryboard() {
        // Confirm reset
        if (!confirm('Are you sure you want to reset the storyboard? This will remove all frames and arrangements.')) {
            return;
        }
        
        // Clear storyboard
        projectData.storyboard = [];
        
        // Save changes
        saveProjectData();
        
        // Re-render storyboard
        renderStoryboard();
        
        // Show editor closed state
        selectedFrameId = null;
        noFrameSelected.classList.remove('d-none');
        frameEditor.classList.add('d-none');
        
        // Show success message
        showAlert('Storyboard reset successfully', 'success');
    }
    
    /**
     * Update the audio timeline
     */
    function updateAudioTimeline() {
        if (!audioTimeline) return;
        
        // Clear existing markers
        audioTimeline.innerHTML = '<div class="progress-bar bg-primary" role="progressbar" style="width: 0%;" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>';
        
        // Get audio duration
        const audioDuration = audioPlayer.duration || 180; // Default to 3 minutes if not loaded
        
        // Create frame markers
        let currentTime = 0;
        
        // Sort frames by order
        const sortedFrames = [...projectData.storyboard].sort((a, b) => a.order - b.order);
        
        // Add markers for each frame
        sortedFrames.forEach((frame, index) => {
            const frameDuration = frame.duration || 3;
            const frameWidth = (frameDuration / audioDuration) * 100;
            const marker = document.createElement('div');
            
            marker.className = `position-absolute bg-info bg-opacity-50`;
            marker.style.left = `${(currentTime / audioDuration) * 100}%`;
            marker.style.width = `${frameWidth}%`;
            marker.style.height = '100%';
            marker.style.top = '0';
            marker.style.zIndex = '1';
            marker.style.borderRight = '1px solid #0dcaf0';
            marker.innerHTML = `<span class="position-absolute top-50 start-50 translate-middle badge rounded-pill bg-info">${index + 1}</span>`;
            
            audioTimeline.appendChild(marker);
            
            // Update current time
            currentTime += frameDuration;
        });
        
        // Add time markers
        for (let i = 0; i <= audioDuration; i += 30) {
            const timeMarker = document.createElement('div');
            const minutes = Math.floor(i / 60);
            const seconds = i % 60;
            
            timeMarker.className = 'position-absolute text-dark';
            timeMarker.style.left = `${(i / audioDuration) * 100}%`;
            timeMarker.style.bottom = '-20px';
            timeMarker.style.fontSize = '0.8rem';
            timeMarker.style.transform = 'translateX(-50%)';
            timeMarker.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            audioTimeline.appendChild(timeMarker);
        }
    }
    
    /**
     * Save project data to localStorage
     */
    function saveProjectData() {
        localStorage.setItem('maivid_project', JSON.stringify(projectData));
    }
    
    /**
     * Set shot type from selector
     */
    function setSelectedShotType(shotType) {
        selectedShotType = shotType;
        
        // Update UI
        document.querySelectorAll('.shot-type-option').forEach(option => {
            option.classList.remove('selected');
        });
        
        const selectedOption = document.querySelector(`.shot-type-option[data-shot-type="${shotType}"]`);
        if (selectedOption) {
            selectedOption.classList.add('selected');
        }
    }
    
    /**
     * Apply shot type to selected frame
     */
    function applyShotTypeToFrame() {
        if (!selectedFrameId || !selectedShotType) return;
        
        // Get frame data
        const frame = projectData.storyboard.find(f => f.id === selectedFrameId);
        if (!frame) return;
        
        // Update shot type
        frame.shotType = selectedShotType;
        
        // Update form if open
        if (frameShotType) {
            frameShotType.value = selectedShotType;
        }
        
        // Save changes
        saveProjectData();
        
        // Re-render storyboard
        renderStoryboard();
        
        // Re-select frame
        selectFrame(selectedFrameId);
    }
    
    /**
     * Get human-readable shot type name
     */
    function getShotTypeName(shotType) {
        switch (shotType) {
            case 'close_up': return 'Close-Up';
            case 'medium_shot': return 'Medium Shot';
            case 'wide_shot': return 'Wide Shot';
            case 'extreme_close_up': return 'Extreme Close-Up';
            default: return 'Medium Shot';
        }
    }
    
    /**
     * Get shot type icon
     */
    function getShotTypeIcon(shotType) {
        switch (shotType) {
            case 'close_up': return 'fas fa-user';
            case 'medium_shot': return 'fas fa-user-friends';
            case 'wide_shot': return 'fas fa-image';
            case 'extreme_close_up': return 'fas fa-eye';
            default: return 'fas fa-user-friends';
        }
    }
    
    /**
     * Get shot type color
     */
    function getShotTypeColor(shotType) {
        switch (shotType) {
            case 'close_up': return 'info';
            case 'medium_shot': return 'primary';
            case 'wide_shot': return 'success';
            case 'extreme_close_up': return 'warning';
            default: return 'primary';
        }
    }
    
    /**
     * Get transition name
     */
    function getTransitionName(transition) {
        switch (transition) {
            case 'fade': return 'Fade';
            case 'wipe_left': return 'Wipe Left';
            case 'wipe_right': return 'Wipe Right';
            case 'zoom': return 'Zoom';
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
            case 'fade': return 'fas fa-adjust';
            case 'wipe_left': return 'fas fa-arrow-left';
            case 'wipe_right': return 'fas fa-arrow-right';
            case 'zoom': return 'fas fa-search-plus';
            case 'dissolve': return 'fas fa-water';
            case 'none': return 'fas fa-cut';
            default: return 'fas fa-adjust';
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
    
    // Event Listeners
    if (addFrameBtn) {
        addFrameBtn.addEventListener('click', addEmptyFrame);
    }
    
    if (saveFrameBtn) {
        saveFrameBtn.addEventListener('click', saveFrameChanges);
    }
    
    if (deleteFrameBtn) {
        deleteFrameBtn.addEventListener('click', deleteFrame);
    }
    
    if (autoArrangeBtn) {
        autoArrangeBtn.addEventListener('click', autoArrangeFrames);
    }
    
    if (playStoryboardBtn) {
        playStoryboardBtn.addEventListener('click', playStoryboardPreview);
    }
    
    if (resetStoryboardBtn) {
        resetStoryboardBtn.addEventListener('click', resetStoryboard);
    }
    
    if (continueToTimelineBtn) {
        continueToTimelineBtn.addEventListener('click', function() {
            window.location.href = '/timeline';
        });
    }
    
    // Shot type selector events
    shotTypeOptions.forEach(option => {
        option.addEventListener('click', function() {
            const shotType = this.dataset.shotType;
            setSelectedShotType(shotType);
            
            // If a frame is selected, apply the shot type
            if (selectedFrameId) {
                applyShotTypeToFrame();
            }
        });
    });
    
    // Audio events
    if (audioPlayer) {
        audioPlayer.addEventListener('loadedmetadata', updateAudioTimeline);
        
        // Set audio source if available
        if (projectData.audioPath) {
            audioPlayer.src = `/uploads/${projectData.audioPath.split('/').pop()}`;
            
            // Set audio info
            if (audioInfo && projectData.metadata) {
                audioInfo.innerHTML = `
                    <p class="song-title mb-1">${projectData.metadata.title || 'Unknown Title'}</p>
                    <p class="song-artist text-muted mb-3">${projectData.metadata.artist || 'Unknown Artist'}</p>
                `;
            }
        }
    }
});
