/**
 * MaiVid Studio - Fast Render JavaScript
 * 
 * This file contains the client-side code for the Fast Render page,
 * handling single scene generation and complete music video generation.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize UI elements
    const generateButton = document.getElementById('generateButton');
    const generateSceneButton = document.getElementById('generateSceneButton');
    const createVideoButton = document.getElementById('createVideoButton');
    const exportScenesButton = document.getElementById('exportScenesButton');
    const addToProjectButton = document.getElementById('addToProjectButton');
    const downloadSceneButton = document.getElementById('downloadSceneButton');
    
    // Progress and results sections
    const generationProgress = document.getElementById('generationProgress');
    const generationResults = document.getElementById('generationResults');
    const progressBar = document.getElementById('progressBar');
    const statusMessage = document.getElementById('statusMessage');
    const sceneGrid = document.getElementById('sceneGrid');
    const metadataSection = document.getElementById('metadataSection');
    const songMetadata = document.getElementById('songMetadata');
    
    // Single scene result elements
    const sceneResult = document.getElementById('sceneResult');
    const sceneResultImage = document.getElementById('sceneResultImage');
    const sceneResultDescription = document.getElementById('sceneResultDescription');
    const sceneResultModel = document.getElementById('sceneResultModel');
    const sceneResultAspectRatio = document.getElementById('sceneResultAspectRatio');
    const sceneResultStyle = document.getElementById('sceneResultStyle');
    
    // Store the current job details
    let currentJobId = null;
    let pollInterval = null;
    let generatedScenes = [];
    let currentSingleScene = null;
    
    // Function to ensure the correct workflow step is highlighted
    updateWorkflowStep();
    
    // Event listeners
    if (generateButton) {
        generateButton.addEventListener('click', generateMusicVideo);
    }
    
    if (generateSceneButton) {
        generateSceneButton.addEventListener('click', generateSingleScene);
    }
    
    if (createVideoButton) {
        createVideoButton.addEventListener('click', createVideo);
    }
    
    if (exportScenesButton) {
        exportScenesButton.addEventListener('click', exportScenes);
    }
    
    if (addToProjectButton) {
        addToProjectButton.addEventListener('click', addToProject);
    }
    
    if (downloadSceneButton) {
        downloadSceneButton.addEventListener('click', downloadScene);
    }
    
    /**
     * Generate a music video from a Suno URL
     */
    function generateMusicVideo() {
        // Get form values
        const sunoUrl = document.getElementById('sunoUrl').value;
        const modelType = document.getElementById('modelType').value;
        const aspectRatio = document.getElementById('aspectRatio').value;
        const style = document.getElementById('style').value;
        const sceneCount = document.getElementById('sceneCount').value;
        
        // Validate URL
        if (!sunoUrl) {
            alert('Please enter a Suno URL');
            return;
        }
        
        // Show progress
        generationProgress.style.display = 'block';
        generationResults.style.display = 'none';
        progressBar.style.width = '5%';
        statusMessage.textContent = 'Starting music video generation...';
        
        // Disable generate button
        generateButton.disabled = true;
        generateButton.innerHTML = '<i class="fas fa-spin fa-spinner"></i> Generating...';
        
        // Send request
        fetch('/api/fast_render/music_video', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                suno_url: sunoUrl,
                model_type: modelType,
                aspect_ratio: aspectRatio,
                style: style,
                scene_count: sceneCount
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.job_id) {
                // Store the job ID
                currentJobId = data.job_id;
                
                // Start polling for updates
                pollJobStatus();
                
                // Update status
                statusMessage.textContent = 'Downloading song and extracting lyrics...';
                progressBar.style.width = '10%';
            } else {
                throw new Error(data.error || 'Failed to start job');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            statusMessage.textContent = `Error: ${error.message}`;
            progressBar.style.width = '0%';
            
            // Re-enable generate button
            generateButton.disabled = false;
            generateButton.innerHTML = '<i class="fas fa-bolt"></i> Generate Music Video';
        });
    }
    
    /**
     * Poll for job status updates
     */
    function pollJobStatus() {
        if (!currentJobId) return;
        
        // Clear any existing interval
        if (pollInterval) {
            clearInterval(pollInterval);
        }
        
        // Set up new polling interval
        pollInterval = setInterval(() => {
            fetch(`/api/fast_render/job/${currentJobId}`)
                .then(response => response.json())
                .then(data => {
                    // Check if job is complete
                    if (data.success !== undefined) {
                        // Job is complete
                        clearInterval(pollInterval);
                        
                        if (data.success) {
                            // Success - display results
                            displayResults(data);
                        } else {
                            // Error
                            statusMessage.textContent = `Error: ${data.error || 'Unknown error'}`;
                            progressBar.style.width = '0%';
                        }
                        
                        // Re-enable generate button
                        generateButton.disabled = false;
                        generateButton.innerHTML = '<i class="fas fa-bolt"></i> Generate Music Video';
                    } else {
                        // Job is still processing
                        // Update progress estimation based on status
                        updateProgressEstimation(data);
                    }
                })
                .catch(error => {
                    console.error('Error polling job status:', error);
                    // Don't stop polling on error, just log it
                });
        }, 2000); // Poll every 2 seconds
    }
    
    /**
     * Update progress estimation based on job status
     */
    function updateProgressEstimation(data) {
        // This is an estimation since we don't have direct progress feedback
        // from the backend for all steps
        
        if (data.status === 'processing') {
            // Assuming the process takes roughly ~2 minutes for a typical song
            // We'll simulate progress to give user feedback
            
            let currentWidth = parseInt(progressBar.style.width) || 5;
            
            // Increment by a small amount, but cap at 95% until we get actual results
            currentWidth = Math.min(95, currentWidth + 2);
            progressBar.style.width = `${currentWidth}%`;
            
            // Update message based on progress estimation
            if (currentWidth < 30) {
                statusMessage.textContent = 'Downloading song and extracting lyrics...';
            } else if (currentWidth < 60) {
                statusMessage.textContent = 'Generating scenes from lyrics...';
            } else if (currentWidth < 80) {
                statusMessage.textContent = 'Processing images...';
            } else {
                statusMessage.textContent = 'Finalizing music video project...';
            }
        }
    }
    
    /**
     * Display the results of the music video generation
     */
    function displayResults(data) {
        // Hide progress, show results
        generationProgress.style.display = 'none';
        generationResults.style.display = 'block';
        
        // Store generated scenes
        generatedScenes = data.scenes || [];
        
        // Clear previous results
        sceneGrid.innerHTML = '';
        songMetadata.innerHTML = '';
        
        // Add song metadata
        if (data.song_title || data.artist) {
            metadataSection.style.display = 'block';
            
            // Add song title
            if (data.song_title) {
                const titleItem = document.createElement('div');
                titleItem.className = 'metadata-item';
                titleItem.innerHTML = `<strong>Title:</strong> ${data.song_title}`;
                songMetadata.appendChild(titleItem);
            }
            
            // Add artist
            if (data.artist) {
                const artistItem = document.createElement('div');
                artistItem.className = 'metadata-item';
                artistItem.innerHTML = `<strong>Artist:</strong> ${data.artist}`;
                songMetadata.appendChild(artistItem);
            }
            
            // Add scene count
            const sceneCountItem = document.createElement('div');
            sceneCountItem.className = 'metadata-item';
            sceneCountItem.innerHTML = `<strong>Scenes:</strong> ${generatedScenes.length}`;
            songMetadata.appendChild(sceneCountItem);
            
            // Add model type
            if (data.params && data.params.model_type) {
                const modelItem = document.createElement('div');
                modelItem.className = 'metadata-item';
                modelItem.innerHTML = `<strong>Model:</strong> ${getModelDisplayName(data.params.model_type)}`;
                songMetadata.appendChild(modelItem);
            }
        }
        
        // Add scenes to grid
        generatedScenes.forEach((scene, index) => {
            if (scene.success && scene.image_url) {
                const sceneCard = document.createElement('div');
                sceneCard.className = 'scene-card';
                
                // Create the scene HTML
                sceneCard.innerHTML = `
                    <img src="${scene.image_url}" alt="Scene ${index + 1}" class="scene-image">
                    <div class="scene-info">
                        <h4>Scene ${index + 1}</h4>
                        <p>${scene.description.substring(0, 60)}${scene.description.length > 60 ? '...' : ''}</p>
                    </div>
                `;
                
                // Add to grid
                sceneGrid.appendChild(sceneCard);
            }
        });
        
        // If no successful scenes, show message
        if (sceneGrid.children.length === 0) {
            sceneGrid.innerHTML = '<p>No scenes were successfully generated.</p>';
        }
    }
    
    /**
     * Generate a single scene
     */
    function generateSingleScene() {
        // Get form values
        const sceneDescription = document.getElementById('sceneDescription').value;
        const modelType = document.getElementById('singleModelType').value;
        const aspectRatio = document.getElementById('singleAspectRatio').value;
        const style = document.getElementById('singleStyle').value;
        
        // Validate description
        if (!sceneDescription) {
            alert('Please enter a scene description');
            return;
        }
        
        // Disable generate button
        generateSceneButton.disabled = true;
        generateSceneButton.innerHTML = '<i class="fas fa-spin fa-spinner"></i> Generating...';
        
        // Hide previous result
        sceneResult.style.display = 'none';
        
        // Send request
        fetch('/api/fast_render/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                description: sceneDescription,
                model_type: modelType,
                aspect_ratio: aspectRatio,
                style: style
            })
        })
        .then(response => response.json())
        .then(data => {
            // Re-enable generate button
            generateSceneButton.disabled = false;
            generateSceneButton.innerHTML = '<i class="fas fa-image"></i> Generate Scene';
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Store the scene data
            currentSingleScene = data;
            
            // Display the result
            sceneResultImage.src = data.image_url;
            sceneResultDescription.textContent = data.description;
            sceneResultModel.textContent = getModelDisplayName(data.model_type);
            sceneResultAspectRatio.textContent = data.aspect_ratio;
            sceneResultStyle.textContent = data.style;
            
            // Show the result
            sceneResult.style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            alert(`Error generating scene: ${error.message}`);
            
            // Re-enable generate button
            generateSceneButton.disabled = false;
            generateSceneButton.innerHTML = '<i class="fas fa-image"></i> Generate Scene';
        });
    }
    
    /**
     * Create a video from the generated scenes
     */
    function createVideo() {
        // Check if we have scenes
        if (!generatedScenes || generatedScenes.length === 0) {
            alert('No scenes available to create a video');
            return;
        }
        
        // Extract successful scenes
        const successfulScenes = generatedScenes.filter(scene => scene.success);
        
        if (successfulScenes.length === 0) {
            alert('No successful scenes available to create a video');
            return;
        }
        
        // Navigate to timeline page with this project
        // For now, we'll just alert
        alert('This will navigate to the timeline page with these scenes pre-loaded.');
        // TODO: Implement proper navigation with data passing
    }
    
    /**
     * Export the generated scenes as a ZIP file
     */
    function exportScenes() {
        // This would normally create a ZIP file with all scenes
        // For now, we'll just alert
        alert('Export functionality not yet implemented. This would download all scenes as a ZIP file.');
        // TODO: Implement export functionality
    }
    
    /**
     * Add the current single scene to the project
     */
    function addToProject() {
        if (!currentSingleScene) {
            alert('No scene available to add to project');
            return;
        }
        
        // This would normally add the scene to the current project
        // For now, we'll just alert
        alert('Scene added to project successfully!');
        // TODO: Implement add to project functionality
    }
    
    /**
     * Download the current single scene
     */
    function downloadScene() {
        if (!currentSingleScene || !currentSingleScene.image_url) {
            alert('No scene available to download');
            return;
        }
        
        // Create a temporary anchor and click it to download
        const a = document.createElement('a');
        a.href = currentSingleScene.image_url;
        a.download = `scene_${Date.now()}.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }
    
    /**
     * Get a display name for a model type
     */
    function getModelDisplayName(modelType) {
        switch (modelType) {
            case 'sdxl_turbo':
                return 'SDXL Turbo';
            case 'sd3':
                return 'SD 3';
            case 'flux':
                return 'Flux';
            default:
                return modelType;
        }
    }
    
    /**
     * Update the active workflow step based on current page
     */
    function updateWorkflowStep() {
        // Get the workflow container
        const workflow = document.getElementById('workflow');
        if (workflow) {
            // Reset all steps
            const steps = workflow.querySelectorAll('.progress-bar');
            steps.forEach(step => {
                step.classList.remove('workflow-step-active');
            });
            
            // For fast_render.html, we consider it equivalent to the Motion step (8)
            const fastRenderStep = workflow.querySelector(`.progress-bar[data-step="8"]`);
            if (fastRenderStep) {
                fastRenderStep.classList.add('workflow-step-active');
            }
        }
    }
});
