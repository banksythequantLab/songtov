/**
 * MaiVid Studio - Main JavaScript
 * Handles UI interactions, API calls, and dynamic content loading
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded - initializing MaiVid Studio");
    
    // Get form elements
    const urlForm = document.getElementById('url-form');
    const uploadForm = document.getElementById('upload-form');
    const musicUrl = document.getElementById('music-url');
    const audioFile = document.getElementById('audio-file');
    const resultsSection = document.getElementById('results');
    const audioPlayer = document.getElementById('audio-player');
    const lyricsText = document.getElementById('lyrics-text');
    const continueBtn = document.getElementById('continue-btn');
    
    // Result display elements
    const resultTitle = document.getElementById('result-title');
    const resultArtist = document.getElementById('result-artist');
    const resultDuration = document.getElementById('result-duration');
    
    // Initialize showcase if it exists
    if (window.location.pathname === '/') {
        console.log("Initializing showcase on homepage");
        initShowcase();
    }
    
    // Function to ensure the correct workflow step is highlighted
    updateWorkflowStep();
    
    // Store project data
    let projectData = {
        audioPath: null,
        lyrics: null,
        metadata: null,
        concept: null,
        storyline: null,
        scenes: []
    };
    
    // Load project data from localStorage if it exists
    const savedProject = localStorage.getItem('maivid_project');
    if (savedProject) {
        try {
            projectData = JSON.parse(savedProject);
            console.log('Loaded project data:', projectData);
        } catch (e) {
            console.error('Error parsing saved project data:', e);
        }
    }
    
    /**
     * Handle URL form submission
     */
    if (urlForm) {
        urlForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const url = musicUrl.value.trim();
            
            if (!url) {
                showAlert('Please enter a valid URL', 'danger');
                return;
            }
            
            // Show loading indicator
            showLoading('Downloading music...');
            
            // Always use direct fetch instead of form submission
            console.log("Submitting URL:", url);
            
            fetch('/api/music/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: url })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                hideLoading();
                console.log("Download response:", data);
                
                if (data.error) {
                    showAlert(`Error: ${data.error}`, 'danger');
                    return;
                }
                
                // Store the result
                projectData.audioPath = data.file_path;
                projectData.metadata = data.metadata;
                projectData.lyrics = data.lyrics;
                
                // Display the results
                displayResults(data);
            })
            .catch(error => {
                hideLoading();
                console.error("Download error:", error);
                showAlert(`Error: ${error.message}. Please try again or contact support.`, 'danger');
            });
        });
    }
    
    /**
     * Handle audio file upload
     */
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (!audioFile.files[0]) {
                showAlert('Please select an audio file', 'danger');
                return;
            }
            
            // Show loading indicator
            showLoading('Uploading audio...');
            
            const formData = new FormData();
            formData.append('audio', audioFile.files[0]);
            
            // Call API to upload audio
            fetch('/api/music/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                hideLoading();
                
                if (data.error) {
                    showAlert(`Error: ${data.error}`, 'danger');
                    return;
                }
                
                // Store the result
                projectData.audioPath = data.file_path;
                projectData.metadata = data.metadata;
                projectData.lyrics = data.lyrics;
                
                // Display the results
                displayResults(data);
            })
            .catch(error => {
                hideLoading();
                showAlert(`Error: ${error.message}`, 'danger');
            });
        });
    }
    
    /**
     * Handle continue button click
     */
    if (continueBtn) {
        continueBtn.addEventListener('click', function() {
            // Update the lyrics with any edits
            if (lyricsText) {
                projectData.lyrics = lyricsText.value;
            }
            
            // Save project data to localStorage
            localStorage.setItem('maivid_project', JSON.stringify(projectData));
            
            // Navigate to concept page
            window.location.href = '/concept';
        });
    }
    
    /**
     * Display processing results
     */
    function displayResults(data) {
        if (resultsSection) {
            // Set result values
            if (resultTitle) resultTitle.textContent = data.metadata.title || 'Unknown Title';
            if (resultArtist) resultArtist.textContent = data.metadata.artist || 'Unknown Artist';
            if (resultDuration) {
                const duration = data.metadata.duration || 0;
                const minutes = Math.floor(duration / 60);
                const seconds = Math.floor(duration % 60);
                resultDuration.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            }
            
            // Set audio player source
            if (audioPlayer && data.file_path) {
                audioPlayer.src = `/uploads/${data.file_path.split('/').pop()}`;
            }
            
            // Set lyrics text
            if (lyricsText) {
                lyricsText.value = data.lyrics || '';
            }
            
            // Show results section
            resultsSection.style.display = 'block';
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    /**
     * Show an alert message
     */
    function showAlert(message, type = 'info') {
        // Create alert element
        const alertEl = document.createElement('div');
        alertEl.className = `alert alert-${type} alert-dismissible fade show`;
        alertEl.role = 'alert';
        alertEl.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Add to the page
        const container = document.querySelector('.container');
        if (container) {
            container.insertAdjacentElement('afterbegin', alertEl);
            
            // Auto remove after 5 seconds
            setTimeout(() => {
                alertEl.remove();
            }, 5000);
        }
    }
    
    /**
     * Show loading indicator
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
     * Format time in seconds to MM:SS format
     */
    function formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
    
    /**
     * Generate a unique ID
     */
    function generateId() {
        return 'id_' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * Initialize page based on current route
     */
    function initPage() {
        const path = window.location.pathname;
        
        // Update workflow step based on current page
        updateWorkflowStep(path);
        
        // Home page
        if (path === '/') {
            // Nothing specific needed for homepage initialization
        }
        // Concept page
        else if (path === '/concept') {
            initConceptPage();
        }
        // Storyline page
        else if (path === '/storyline') {
            initStorylinePage();
        }
        // Settings page
        else if (path === '/settings') {
            initSettingsPage();
        }
        // Scenes page
        else if (path === '/scenes') {
            initScenesPage();
        }
        // Storyboard page
        else if (path === '/storyboard') {
            initStoryboardPage();
        }
        // Timeline page
        else if (path === '/timeline') {
            initTimelinePage();
        }
        // Motion page
        else if (path === '/motion') {
            initMotionPage();
        }
    }
    
    /**
     * Update the active workflow step based on current page
     */
    function updateWorkflowStep(path) {
        // Set the default path if not provided
        path = path || window.location.pathname;
        
        // Map pages to step numbers
        let stepNumber = 1; // Default to first step
        
        if (path === '/') {
            stepNumber = 1; // Music
        } else if (path === '/concept') {
            stepNumber = 2; // Concept
        } else if (path === '/storyline') {
            stepNumber = 3; // Storyline
        } else if (path === '/settings') {
            stepNumber = 4; // Settings
        } else if (path === '/scenes') {
            stepNumber = 5; // Scenes
        } else if (path === '/storyboard') {
            stepNumber = 6; // Storyboard
        } else if (path === '/timeline') {
            stepNumber = 7; // Timeline
        } else if (path === '/motion' || path === '/fast_render') {
            stepNumber = 8; // Motion or Fast Render
        }
        
        // Get the workflow container
        const workflow = document.getElementById('workflow');
        if (workflow) {
            // Reset all steps
            const steps = workflow.querySelectorAll('.progress-bar');
            steps.forEach((step, index) => {
                step.classList.remove('workflow-step-active');
                step.classList.remove('workflow-step-completed');
                
                // Mark previous steps as completed
                if (index + 1 < stepNumber) {
                    step.classList.add('workflow-step-completed');
                }
            });
            
            // Highlight the active step
            const activeStep = workflow.querySelector(`.progress-bar[data-step="${stepNumber}"]`);
            if (activeStep) {
                activeStep.classList.add('workflow-step-active');
                activeStep.setAttribute('aria-current', 'step');
            }
        }
    }
    
    /**
     * Initialize the concept development page
     */
    function initConceptPage() {
        // Check if we have lyrics
        if (!projectData.lyrics) {
            showAlert('Please upload music and extract lyrics first', 'warning');
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
            return;
        }
        
        // Initialize concept development interface if available
        const generateConceptBtn = document.getElementById('generate-concept-btn');
        const conceptForm = document.getElementById('concept-form');
        
        if (generateConceptBtn) {
            generateConceptBtn.addEventListener('click', function() {
                // Get selected style
                const styleSelect = document.getElementById('concept-style');
                const style = styleSelect ? styleSelect.value : 'cinematic';
                
                // Show loading
                showLoading('Generating concept...');
                
                // Call API to generate concept
                fetch('/api/concept/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        lyrics: projectData.lyrics,
                        style: style
                    })
                })
                .then(response => response.json())
                .then(data => {
                    hideLoading();
                    
                    if (data.error) {
                        showAlert(`Error: ${data.error}`, 'danger');
                        return;
                    }
                    
                    // Store concept data
                    projectData.concept = data;
                    localStorage.setItem('maivid_project', JSON.stringify(projectData));
                    
                    // Display concept
                    displayConcept(data);
                })
                .catch(error => {
                    hideLoading();
                    showAlert(`Error: ${error.message}`, 'danger');
                });
            });
        }
        
        // Load existing concept if available
        if (projectData.concept) {
            displayConcept(projectData.concept);
        }
    }
    
    /**
     * Display concept data
     */
    function displayConcept(concept) {
        const conceptResult = document.getElementById('concept-result');
        
        if (conceptResult) {
            // Add a placeholder sample image (in a real app, this would be generated)
            const sampleImageUrl = `/static/img/concept_${concept.style.toLowerCase().replace(/[^a-z0-9]/g, '_')}.jpg`;
            const fallbackImageUrl = '/static/img/concept_placeholder.jpg';
            
            // Create concept display with Apple Card style
            conceptResult.innerHTML = `
                <div class="card">
                    <div class="card-header">
                        <h3>${concept.title}</h3>
                    </div>
                    <div class="card-body p-0">
                        <div class="row g-0">
                            <div class="col-md-5">
                                <div class="concept-image" style="height: 100%; min-height: 300px; background-image: url('${sampleImageUrl}'); background-size: cover; background-position: center;">
                                </div>
                            </div>
                            <div class="col-md-7 p-4">
                                <p class="lead">${concept.description}</p>
                                
                                <div class="row mt-4">
                                    <div class="col-md-6">
                                        <h5 class="mb-3">Style & Mood</h5>
                                        <div class="d-flex mb-2">
                                            <div class="me-3 text-muted">Style:</div>
                                            <div class="fw-bold">${concept.style}</div>
                                        </div>
                                        <div class="d-flex mb-3">
                                            <div class="me-3 text-muted">Mood:</div>
                                            <div class="fw-bold">${concept.mood}</div>
                                        </div>
                                        
                                        <h5 class="mb-3">Themes</h5>
                                        <div class="themes-list">
                                            ${concept.themes.map(theme => `<span class="badge bg-light text-dark me-2 mb-2 p-2">${theme}</span>`).join('')}
                                        </div>
                                    </div>
                                    
                                    <div class="col-md-6">
                                        <h5 class="mb-3">Color Palette</h5>
                                        <div class="d-flex mb-3">
                                            ${concept.color_palette.map(color => 
                                                `<div class="me-2" style="width: 36px; height: 36px; background-color: ${color}; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);"></div>`
                                            ).join('')}
                                        </div>
                                        
                                        <h5 class="mb-3">Visual Elements</h5>
                                        <div class="visual-elements-list">
                                            ${concept.visual_elements.map(element => `<span class="badge bg-light text-dark me-2 mb-2 p-2">${element}</span>`).join('')}
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="d-flex justify-content-end mt-4">
                                    <button id="regenerate-concept-btn" class="btn btn-outline-primary me-2">
                                        <i class="fas fa-sync-alt me-2"></i>Regenerate
                                    </button>
                                    <button id="continue-to-storyline-btn" class="btn btn-primary">
                                        Continue to Storyline
                                        <i class="fas fa-arrow-right ms-2"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Show the result
            conceptResult.style.display = 'block';
            
            // Add event listeners
            document.getElementById('regenerate-concept-btn').addEventListener('click', function() {
                document.getElementById('generate-concept-btn').click();
            });
            
            document.getElementById('continue-to-storyline-btn').addEventListener('click', function() {
                window.location.href = '/storyline';
            });
            
            // Check if the sample image exists, otherwise use fallback
            const img = new Image();
            img.onload = function() {
                // Image exists, do nothing
            };
            img.onerror = function() {
                // Image doesn't exist, use fallback
                document.querySelector('.concept-image').style.backgroundImage = `url('${fallbackImageUrl}')`;
            };
            img.src = sampleImageUrl;
        }
    }
    
    // Scene generation functionality
    const generateSceneBtn = document.getElementById('generate-scene-btn');
    if (generateSceneBtn) {
        generateSceneBtn.addEventListener('click', function() {
            const sceneDescription = document.getElementById('scene-description').value;
            const sceneStyle = document.getElementById('scene-style').value;
            
            if (!sceneDescription) {
                showAlert('Please enter a scene description', 'warning');
                return;
            }
            
            // Show loading indicator
            showLoading('Generating scene image...');
            
            // Call API to generate scene
            fetch('/api/scene/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    description: sceneDescription,
                    style: sceneStyle
                })
            })
            .then(response => response.json())
            .then(data => {
                hideLoading();
                
                if (data.error) {
                    showAlert(`Error: ${data.error}`, 'danger');
                    return;
                }
                
                // Update the scene preview
                const scenePreview = document.getElementById('scene-preview');
                if (scenePreview) {
                    scenePreview.src = data.image_url;
                }
                
                // Save the scene data
                const sceneId = document.getElementById('scene-id').value || data.id;
                
                // Add or update the scene in projectData
                const sceneIndex = projectData.scenes.findIndex(scene => scene.id === sceneId);
                
                const sceneData = {
                    id: sceneId,
                    description: sceneDescription,
                    style: sceneStyle,
                    image_path: data.image_path,
                    image_url: data.image_url,
                    motion_type: document.getElementById('scene-motion').value,
                    duration: parseFloat(document.getElementById('scene-duration').value),
                    lyrics: document.getElementById('scene-lyrics').value
                };
                
                if (sceneIndex >= 0) {
                    projectData.scenes[sceneIndex] = sceneData;
                } else {
                    projectData.scenes.push(sceneData);
                }
                
                // Save project data
                localStorage.setItem('maivid_project', JSON.stringify(projectData));
                
                // Show success message
                showAlert('Scene image generated successfully!', 'success');
                
                // Update the scene list if it exists
                updateSceneList();
            })
            .catch(error => {
                hideLoading();
                showAlert(`Error: ${error.message}`, 'danger');
            });
        });
    }
    
    // Function to update the scene list display
    function updateSceneList() {
        const sceneList = document.getElementById('scene-list');
        if (!sceneList) return;
        
        // Clear current content
        sceneList.innerHTML = '';
        
        // Add each scene to the list
        projectData.scenes.forEach(scene => {
            const sceneCard = document.createElement('div');
            sceneCard.className = 'col-md-3 mb-3';
            sceneCard.innerHTML = `
                <div class="card scene-card" data-id="${scene.id}">
                    <img src="${scene.image_url || '/static/img/placeholder-image.png'}" class="card-img-top" alt="Scene Preview">
                    <div class="card-body">
                        <h5 class="card-title">${scene.description.substring(0, 20)}...</h5>
                        <p class="card-text"><small>${scene.style} style, ${scene.duration}s</small></p>
                        <div class="d-grid gap-2">
                            <button class="btn btn-sm btn-outline-primary edit-scene-btn">Edit</button>
                        </div>
                    </div>
                </div>
            `;
            
            sceneList.appendChild(sceneCard);
        });
        
        // Add event listeners to the edit buttons
        document.querySelectorAll('.edit-scene-btn').forEach(button => {
            button.addEventListener('click', function() {
                const sceneId = this.closest('.scene-card').dataset.id;
                editScene(sceneId);
            });
        });
    }
    
    // Function to edit a scene
    function editScene(sceneId) {
        const scene = projectData.scenes.find(s => s.id === sceneId);
        if (!scene) return;
        
        // Fill the form with scene data
        document.getElementById('scene-id').value = scene.id;
        document.getElementById('scene-description').value = scene.description;
        document.getElementById('scene-style').value = scene.style;
        document.getElementById('scene-duration').value = scene.duration;
        document.getElementById('scene-motion').value = scene.motion_type || 'zoom';
        document.getElementById('scene-lyrics').value = scene.lyrics || '';
        
        // Update the preview
        const scenePreview = document.getElementById('scene-preview');
        if (scenePreview) {
            scenePreview.src = scene.image_url || '/static/img/placeholder-image.png';
        }
        
        // Scroll to the form
        document.getElementById('scene-form').scrollIntoView({ behavior: 'smooth' });
    }
    
    // Save scene button
    const saveSceneBtn = document.getElementById('save-scene-btn');
    if (saveSceneBtn) {
        saveSceneBtn.addEventListener('click', function() {
            const sceneId = document.getElementById('scene-id').value;
            if (!sceneId) {
                showAlert('Please generate a scene image first', 'warning');
                return;
            }
            
            const sceneIndex = projectData.scenes.findIndex(scene => scene.id === sceneId);
            if (sceneIndex < 0) {
                showAlert('Scene not found', 'danger');
                return;
            }
            
            // Update the scene data
            projectData.scenes[sceneIndex] = {
                ...projectData.scenes[sceneIndex],
                description: document.getElementById('scene-description').value,
                style: document.getElementById('scene-style').value,
                duration: parseFloat(document.getElementById('scene-duration').value),
                motion_type: document.getElementById('scene-motion').value,
                lyrics: document.getElementById('scene-lyrics').value
            };
            
            // Save project data
            localStorage.setItem('maivid_project', JSON.stringify(projectData));
            
            // Update the scene list
            updateSceneList();
            
            // Show success message
            showAlert('Scene saved successfully!', 'success');
        });
    }
    
    // Add scene button
    const addSceneBtn = document.getElementById('add-scene-btn');
    if (addSceneBtn) {
        addSceneBtn.addEventListener('click', function() {
            // Clear the form
            document.getElementById('scene-id').value = '';
            document.getElementById('scene-description').value = '';
            document.getElementById('scene-style').value = 'cinematic';
            document.getElementById('scene-duration').value = 3;
            document.getElementById('scene-motion').value = 'zoom';
            document.getElementById('scene-lyrics').value = '';
            
            // Reset the preview
            const scenePreview = document.getElementById('scene-preview');
            if (scenePreview) {
                scenePreview.src = '/static/img/placeholder-image.png';
            }
            
            // Scroll to the form
            document.getElementById('scene-form').scrollIntoView({ behavior: 'smooth' });
        });
    }
    
    // Generate video button (on Timeline page)
    const generateVideoBtn = document.getElementById('generate-video-btn');
    if (generateVideoBtn) {
        generateVideoBtn.addEventListener('click', function() {
            if (projectData.scenes.length === 0) {
                showAlert('Please create at least one scene first', 'warning');
                return;
            }
            
            if (!projectData.audioPath) {
                showAlert('No audio file found. Please go back to the home page and upload an audio file.', 'warning');
                return;
            }
            
            // Show loading indicator
            showLoading('Generating video... This may take a few minutes.');
            
            // Call API to create video
            fetch('/api/video/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    scenes: projectData.scenes,
                    audio_path: projectData.audioPath,
                    transition_type: document.getElementById('transition-type')?.value || 'fade'
                })
            })
            .then(response => response.json())
            .then(data => {
                hideLoading();
                
                if (data.error) {
                    showAlert(`Error: ${data.error}`, 'danger');
                    return;
                }
                
                // Store the video path and URL
                projectData.videoPath = data.video_path;
                projectData.videoUrl = data.video_url;
                
                // Save project data
                localStorage.setItem('maivid_project', JSON.stringify(projectData));
                
                // Show the video preview
                const videoPreview = document.getElementById('video-preview');
                if (videoPreview) {
                    videoPreview.src = data.video_url;
                    document.getElementById('video-preview-container').style.display = 'block';
                    videoPreview.scrollIntoView({ behavior: 'smooth' });
                }
                
                // Show success message
                showAlert('Video generated successfully!', 'success');
            })
            .catch(error => {
                hideLoading();
                showAlert(`Error: ${error.message}`, 'danger');
            });
        });
    }
    
    // Download video button
    const downloadVideoBtn = document.getElementById('download-video-btn');
    if (downloadVideoBtn) {
        downloadVideoBtn.addEventListener('click', function() {
            if (!projectData.videoUrl) {
                showAlert('No video to download', 'warning');
                return;
            }
            
            // Create a temporary link and click it to download
            const link = document.createElement('a');
            link.href = projectData.videoUrl;
            link.download = 'music_video.mp4';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
    }
    
    // Load existing scenes if on scenes page
    if (window.location.pathname === '/scenes') {
        updateSceneList();
    }
    
    // Load audio player on relevant pages
    if (['/', '/concept', '/storyline', '/scenes', '/timeline'].includes(window.location.pathname)) {
        // Get the audio player element
        const pageAudioPlayer = audioPlayer ||
                             document.getElementById('timeline-audio-player') ||
                             document.getElementById('audio-player');
                             
        if (pageAudioPlayer && projectData.audioPath) {
            // Set the audio source
            pageAudioPlayer.src = `/uploads/${projectData.audioPath.split('/').pop()}`;
            
            // Set audio info if elements exist
            const audioInfo = document.getElementById('audio-info');
            if (audioInfo && projectData.metadata) {
                audioInfo.innerHTML = `
                    <p class="song-title mb-1">${projectData.metadata.title || 'Unknown Title'}</p>
                    <p class="song-artist text-muted mb-3">${projectData.metadata.artist || 'Unknown Artist'}</p>
                `;
            }
        }
        
        // Set lyrics if element exists
        const pageLyricsText = lyricsText || document.getElementById('lyrics-text');
        if (pageLyricsText && projectData.lyrics) {
            pageLyricsText.value = projectData.lyrics;
        }
    }
    
    // Concept page initialization
    if (window.location.pathname === '/concept') {
        // Load concept if it exists
        if (projectData.concept) {
            displayConcept(projectData.concept);
        }
    }
    
    // Storyline page initialization
    if (window.location.pathname === '/storyline') {
        // Load concept summary
        const conceptSummary = document.getElementById('concept-summary');
        if (conceptSummary && projectData.concept) {
            conceptSummary.innerHTML = `
                <h4>${projectData.concept.title}</h4>
                <p>${projectData.concept.description}</p>
                <div class="d-flex mb-2">
                    <div class="me-3"><strong>Style:</strong> ${projectData.concept.style}</div>
                    <div><strong>Mood:</strong> ${projectData.concept.mood}</div>
                </div>
            `;
        }
        
        // Load storyline if it exists
        if (projectData.storyline) {
            displayStoryline(projectData.storyline);
        }
    }
    
    // Initialize the current page
    initPage();
    
    /**
     * Initialize image showcase on homepage
     */
    function initShowcase() {
        // Only run on homepage
        if (window.location.pathname !== '/') return;
        
        const showcase = document.getElementById('showcase');
        if (!showcase) {
            console.error("Showcase element not found");
            return;
        }
        
        // Clear any interval that might be running
        if (window.showcaseInterval) {
            clearInterval(window.showcaseInterval);
            window.showcaseInterval = null;
        }
        
        // Sample showcase data with gradients and descriptions
        const showcaseData = [
            {
                style: 'linear-gradient(45deg, #FF453A, #FF9F0A)',
                image: '/static/img/showcase/showcase1.png',
                prompt: 'Neon-lit cyberpunk city at night with flying vehicles',
                song: 'Digital Dreams'
            },
            {
                style: 'linear-gradient(45deg, #32D74B, #64D2FF)',
                image: '/static/img/showcase/showcase2.png',
                prompt: 'Mystical forest with glowing plants and ethereal spirits',
                song: 'Enchanted Whispers'
            },
            {
                style: 'linear-gradient(45deg, #5E5CE6, #BF5AF2)',
                image: '/static/img/showcase/showcase3.png',
                prompt: 'Spacecraft journeying through a colorful nebula with distant planets',
                song: 'Cosmic Voyage'
            },
            {
                style: 'linear-gradient(45deg, #FF375F, #FF9F0A)',
                image: '/static/img/showcase/showcase4.png',
                prompt: 'Abstract swirls of color representing emotional journey and transformation',
                song: 'Emotional Waves'
            },
            {
                style: 'linear-gradient(45deg, #30B0C7, #0A84FF)',
                image: '/static/img/showcase/showcase5.png',
                prompt: 'Person silhouetted against dramatic desert sunset',
                song: 'Horizon's Call'
            }
        ];
        
        // Clear any existing content
        showcase.innerHTML = '';
        console.log("Cleared showcase content");
        
        // Create showcase images
        showcaseData.forEach((item, index) => {
            const imageContainer = document.createElement('div');
            imageContainer.className = `showcase-image ${index === 0 ? 'active' : ''}`;
            
            // Always use the gradient background as a fallback
            imageContainer.style.background = item.style;
            
            // Try to load the image
            const img = new Image();
            img.onload = function() {
                // If image loads, set it as background
                imageContainer.style.backgroundImage = `url('${item.image}')`;
                console.log(`Image loaded: ${item.image}`);
            };
            img.onerror = function() {
                console.warn(`Failed to load image: ${item.image}, using gradient fallback`);
            };
            img.src = item.image;
            
            // Add caption
            const caption = document.createElement('div');
            caption.className = 'showcase-caption';
            caption.innerHTML = `
                <strong>"${item.prompt}"</strong>
                <p>Song: ${item.song}</p>
            `;
            
            imageContainer.appendChild(caption);
            showcase.appendChild(imageContainer);
        });
        
        console.log(`Added ${showcaseData.length} images to showcase`);
        
        // Enhanced rotation with animation
        let currentImage = 0;
        function rotateImages() {
            const images = document.querySelectorAll('.showcase-image');
            if (images.length === 0) {
                console.error("No showcase images found");
                return;
            }
            
            // Hide current image with fade-out
            images[currentImage].classList.remove('active');
            
            // Show next image with fade-in
            currentImage = (currentImage + 1) % images.length;
            images[currentImage].classList.add('active');
            
            // Force repaint to ensure animation triggers
            void images[currentImage].offsetWidth;
            
            // Log rotation for debugging
            console.log(`Showcase rotated to image ${currentImage + 1} of ${images.length}`);
        }
        
        // Give images time to load before starting rotation
        console.log("Starting showcase rotation with delay");
        window.showcaseReady = setTimeout(() => {
            // Set up rotation interval - ensure we're using a reasonable interval
            window.showcaseInterval = setInterval(rotateImages, 4000);
            console.log("Showcase rotation interval started");
            
            // Force first rotation after a short delay to ensure everything is loaded
            setTimeout(rotateImages, 500);
        }, 1000);
    }
});
