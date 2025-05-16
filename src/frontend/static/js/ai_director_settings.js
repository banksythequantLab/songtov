/**
 * MaiVid Studio - AI Director Settings
 * 
 * This script handles the AI Director settings UI,
 * including Ollama integration and test generation.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const aiSettingsBtn = document.getElementById('ai-settings-btn');
    const saveAiSettingsBtn = document.getElementById('saveAiSettingsBtn');
    const useOllamaSwitch = document.getElementById('useOllamaSwitch');
    const ollamaSettings = document.getElementById('ollamaSettings');
    const ollamaModel = document.getElementById('ollamaModel');
    const ollamaUrl = document.getElementById('ollamaUrl');
    const checkOllamaBtn = document.getElementById('checkOllamaBtn');
    const ollamaStatus = document.getElementById('ollamaStatus');
    const testLyrics = document.getElementById('testLyrics');
    const testGenerationBtn = document.getElementById('testGenerationBtn');
    const testResults = document.getElementById('testResults');
    const testSummary = document.getElementById('testSummary');
    const testScenePrompt = document.getElementById('testScenePrompt');
    const testModelType = document.getElementById('testModelType');
    
    // Modal
    const aiSettingsModal = new bootstrap.Modal(document.getElementById('aiSettingsModal'));
    
    // Initial setup
    loadSettings();
    
    // Event listeners
    aiSettingsBtn.addEventListener('click', openSettings);
    saveAiSettingsBtn.addEventListener('click', saveSettings);
    useOllamaSwitch.addEventListener('change', toggleOllamaSettings);
    checkOllamaBtn.addEventListener('click', checkOllamaConnection);
    testGenerationBtn.addEventListener('click', testGeneration);
    
    /**
     * Open settings modal
     */
    function openSettings() {
        loadSettings();
        aiSettingsModal.show();
    }
    
    /**
     * Load current AI Director settings
     */
    function loadSettings() {
        fetch('/api/ai/settings')
            .then(response => response.json())
            .then(data => {
                // Update UI
                useOllamaSwitch.checked = data.use_ollama;
                ollamaModel.value = data.ollama_model || 'phi3:mini';
                ollamaUrl.value = data.ollama_url || 'http://localhost:11434';
                
                // Toggle Ollama settings visibility
                toggleOllamaSettings();
                
                // If Ollama is enabled, check connection
                if (data.use_ollama) {
                    checkOllamaConnection();
                }
                
                // Populate Ollama models
                loadOllamaModels();
            })
            .catch(error => {
                console.error('Error loading settings:', error);
                showAlert('Failed to load AI Director settings', 'danger');
            });
    }
    
    /**
     * Toggle Ollama settings visibility
     */
    function toggleOllamaSettings() {
        if (useOllamaSwitch.checked) {
            ollamaSettings.style.display = 'block';
        } else {
            ollamaSettings.style.display = 'none';
        }
    }
    
    /**
     * Check Ollama connection
     */
    function checkOllamaConnection() {
        // Update status
        ollamaStatus.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="spinner-border spinner-border-sm me-2" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                Checking Ollama connection...
            </div>
        `;
        ollamaStatus.className = 'alert alert-info';
        
        // Make API call
        fetch('/api/ai/ollama/status')
            .then(response => response.json())
            .then(data => {
                if (data.available) {
                    ollamaStatus.innerHTML = `
                        <i class="fas fa-check-circle me-2"></i>
                        Ollama is connected and working!
                        <br><small>Model: ${data.model}</small>
                        ${data.test_response ? `<br><small>Response: "${data.test_response}"</small>` : ''}
                    `;
                    ollamaStatus.className = 'alert alert-success';
                } else {
                    ollamaStatus.innerHTML = `
                        <i class="fas fa-exclamation-circle me-2"></i>
                        Ollama is not available.
                        <br><small>${data.error || 'Check if Ollama is running.'}</small>
                    `;
                    ollamaStatus.className = 'alert alert-danger';
                }
            })
            .catch(error => {
                console.error('Error checking Ollama:', error);
                ollamaStatus.innerHTML = `
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Error checking Ollama connection.
                    <br><small>${error.message || 'Unknown error'}</small>
                `;
                ollamaStatus.className = 'alert alert-danger';
            });
    }
    
    /**
     * Load available Ollama models
     */
    function loadOllamaModels() {
        fetch('/api/ai/models/list')
            .then(response => response.json())
            .then(data => {
                // Clear options (except default)
                ollamaModel.innerHTML = '';
                
                // Add options
                data.models.forEach(model => {
                    if (model.type === 'ollama') {
                        const option = document.createElement('option');
                        option.value = model.id;
                        option.textContent = model.name;
                        ollamaModel.appendChild(option);
                    }
                });
                
                // If no models found, add default
                if (ollamaModel.options.length === 0) {
                    const option = document.createElement('option');
                    option.value = 'phi3:mini';
                    option.textContent = 'phi3:mini';
                    ollamaModel.appendChild(option);
                }
            })
            .catch(error => {
                console.error('Error loading models:', error);
                
                // Add default option
                ollamaModel.innerHTML = '';
                const option = document.createElement('option');
                option.value = 'phi3:mini';
                option.textContent = 'phi3:mini';
                ollamaModel.appendChild(option);
            });
    }
    
    /**
     * Save AI Director settings
     */
    function saveSettings() {
        // Collect settings
        const settings = {
            use_ollama: useOllamaSwitch.checked,
            ollama_model: ollamaModel.value,
            ollama_url: ollamaUrl.value
        };
        
        // Make API call
        fetch('/api/ai/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showAlert(`Failed to save settings: ${data.error}`, 'danger');
                } else {
                    showAlert('AI Director settings saved successfully!', 'success');
                    aiSettingsModal.hide();
                }
            })
            .catch(error => {
                console.error('Error saving settings:', error);
                showAlert('Failed to save settings', 'danger');
            });
    }
    
    /**
     * Test generation with current settings
     */
    function testGeneration() {
        // Get lyrics
        const lyrics = testLyrics.value;
        
        if (!lyrics.trim()) {
            showAlert('Please enter some lyrics for testing', 'warning');
            return;
        }
        
        // Show loading
        testResults.style.display = 'block';
        testSummary.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
        testScenePrompt.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
        testModelType.textContent = 'Loading...';
        
        // Make API call
        fetch('/api/ai/test/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ lyrics })
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    testSummary.innerHTML = `<div class="text-danger">${data.error}</div>`;
                    testScenePrompt.innerHTML = `<div class="text-danger">${data.error}</div>`;
                    testModelType.textContent = 'Error';
                    return;
                }
                
                // Update UI
                testSummary.innerHTML = (data.summary || 'No summary generated').replace(/\n/g, '<br>');
                testScenePrompt.innerHTML = (data.scene?.scene_prompt || 'No scene generated').replace(/\n/g, '<br>');
                testModelType.textContent = data.model_type === 'ollama' ? 'Ollama Phi-3 Mini' : 'Built-in AI Director';
                
                // Add scene metadata
                const sceneType = data.scene?.section_type || 'unknown';
                const narrativeBeat = data.scene?.narrative_beat || 'unknown';
                
                // Add metadata to prompt display
                testScenePrompt.innerHTML += `<hr><small class="text-muted">Section type: ${sceneType}, Narrative beat: ${narrativeBeat}</small>`;
            })
            .catch(error => {
                console.error('Error testing generation:', error);
                testSummary.innerHTML = `<div class="text-danger">Error: ${error.message || 'Unknown error'}</div>`;
                testScenePrompt.innerHTML = `<div class="text-danger">Error: ${error.message || 'Unknown error'}</div>`;
                testModelType.textContent = 'Error';
            });
    }
    
    /**
     * Show alert message
     */
    function showAlert(message, type = 'info') {
        // Create alert element
        const alertEl = document.createElement('div');
        alertEl.className = `alert alert-${type} alert-dismissible fade show`;
        alertEl.setAttribute('role', 'alert');
        
        // Alert content
        alertEl.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Find container
        const container = document.querySelector('main .container');
        
        // Insert at top
        container.insertBefore(alertEl, container.firstChild);
        
        // Auto-close after 5 seconds
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alertEl);
            bsAlert.close();
        }, 5000);
    }
});
