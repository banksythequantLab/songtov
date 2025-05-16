/**
 * MaiVid Studio - Projects JS
 * Handles project management and display
 */

// Wait for DOM content to load
document.addEventListener('DOMContentLoaded', function() {
    // Get Firebase instances
    const auth = firebase.auth();
    const firestore = firebase.firestore();
    
    // References to DOM elements
    const projectsGrid = document.getElementById('projects-grid');
    const loadingProjects = document.getElementById('loading-projects');
    const emptyProjects = document.getElementById('empty-projects');
    const searchProjects = document.getElementById('search-projects');
    const clearSearch = document.getElementById('clear-search');
    const filterProjects = document.getElementById('filter-projects');
    const newProjectBtn = document.getElementById('new-project-btn');
    const createProjectCard = document.getElementById('create-project-card');
    const emptyCreateBtn = document.getElementById('empty-create-btn');
    
    // Modals
    const newProjectModal = new bootstrap.Modal(document.getElementById('new-project-modal'));
    const projectOptionsModal = new bootstrap.Modal(document.getElementById('project-options-modal'));
    const shareProjectModal = new bootstrap.Modal(document.getElementById('share-project-modal'));
    
    // Create project form elements
    const createProjectBtn = document.getElementById('create-project-btn');
    
    // Current projects data
    let projects = [];
    let selectedProjectId = null;
    
    /**
     * Initialize projects page
     */
    function initProjectsPage() {
        // Load user's projects
        loadProjects();
        
        // Set up event listeners
        setupEventListeners();
    }
    
    /**
     * Set up event listeners
     */
    function setupEventListeners() {
        // New project button
        if (newProjectBtn) {
            newProjectBtn.addEventListener('click', () => {
                newProjectModal.show();
            });
        }
        
        // Create project card
        if (createProjectCard) {
            createProjectCard.addEventListener('click', () => {
                newProjectModal.show();
            });
        }
        
        // Empty state create button
        if (emptyCreateBtn) {
            emptyCreateBtn.addEventListener('click', () => {
                newProjectModal.show();
            });
        }
        
        // Create project button in modal
        if (createProjectBtn) {
            createProjectBtn.addEventListener('click', handleCreateProject);
        }
        
        // Search input
        if (searchProjects) {
            searchProjects.addEventListener('input', handleSearch);
        }
        
        // Clear search button
        if (clearSearch) {
            clearSearch.addEventListener('click', () => {
                searchProjects.value = '';
                handleSearch();
            });
        }
        
        // Filter select
        if (filterProjects) {
            filterProjects.addEventListener('change', handleFilter);
        }
        
        // Project action buttons (set up later when projects are loaded)
    }
    
    /**
     * Load user's projects from Firestore
     */
    function loadProjects() {
        const user = auth.currentUser;
        if (!user) return;
        
        // Show loading state
        if (loadingProjects) loadingProjects.style.display = 'flex';
        if (projectsGrid) projectsGrid.style.display = 'none';
        if (emptyProjects) emptyProjects.style.display = 'none';
        
        // Get projects from Firestore
        firestore.collection('projects')
            .where('userId', '==', user.uid)
            .orderBy('updatedAt', 'desc')
            .get()
            .then(snapshot => {
                // Convert snapshot to array of projects
                projects = snapshot.docs.map(doc => {
                    const data = doc.data();
                    return {
                        id: doc.id,
                        ...data
                    };
                });
                
                // Hide loading state
                if (loadingProjects) loadingProjects.style.display = 'none';
                
                // Handle empty state
                if (projects.length === 0) {
                    if (emptyProjects) emptyProjects.style.display = 'block';
                    if (projectsGrid) projectsGrid.style.display = 'none';
                } else {
                    // Render projects
                    renderProjects(projects);
                    if (projectsGrid) projectsGrid.style.display = 'flex';
                    if (emptyProjects) emptyProjects.style.display = 'none';
                }
                
                // Update user document with project count
                firestore.collection('users').doc(user.uid).update({
                    projectCount: projects.length
                }).catch(error => {
                    console.error('Failed to update project count:', error);
                });
            })
            .catch(error => {
                console.error('Error loading projects:', error);
                showAlert('Failed to load projects. Please try again.', 'danger');
                
                // Hide loading state
                if (loadingProjects) loadingProjects.style.display = 'none';
            });
    }
    
    /**
     * Render projects in the grid
     */
    function renderProjects(projectsToRender) {
        if (!projectsGrid) return;
        
        // Clear existing project items (but keep the create card)
        const existingItems = projectsGrid.querySelectorAll('.project-item');
        existingItems.forEach(item => item.remove());
        
        // Add project cards
        projectsToRender.forEach(project => {
            const projectCard = createProjectCard(project);
            projectsGrid.appendChild(projectCard);
        });
        
        // Set up event listeners for project actions
        setupProjectActionListeners();
    }
    
    /**
     * Create a project card element
     */
    function createProjectCard(project) {
        // Calculate progress
        const progressSteps = 8; // 8 steps in MaiVid workflow
        const progress = Math.min(100, (project.currentStep / progressSteps) * 100);
        
        // Determine status badge
        let statusBadge = '';
        if (progress === 100) {
            statusBadge = '<span class="badge bg-success badge-category">Completed</span>';
        } else if (progress > 0) {
            statusBadge = '<span class="badge bg-warning badge-category">In Progress</span>';
        } else {
            statusBadge = '<span class="badge bg-secondary badge-category">Not Started</span>';
        }
        
        // Format date
        const updatedAt = project.updatedAt ? new Date(project.updatedAt.toDate()) : new Date();
        const formattedDate = updatedAt.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
        
        // Create column element
        const colElement = document.createElement('div');
        colElement.className = 'col-md-4 mb-4 project-item';
        colElement.dataset.id = project.id;
        
        // Create card HTML
        colElement.innerHTML = `
            <div class="card project-card">
                <div class="position-relative">
                    <img src="${project.thumbnailUrl || '/static/img/placeholder-image.png'}" class="project-thumbnail" alt="${project.name}">
                    <div class="project-actions">
                        <div class="action-btn share-project-btn" title="Share Project" data-id="${project.id}">
                            <i class="fas fa-share-alt"></i>
                        </div>
                        <div class="action-btn project-options-btn" title="More Options" data-id="${project.id}">
                            <i class="fas fa-ellipsis-v"></i>
                        </div>
                    </div>
                    <div class="project-info">
                        <h5 class="card-title mb-1">${project.name}</h5>
                        <div class="project-date">Last edited: ${formattedDate}</div>
                    </div>
                </div>
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        ${statusBadge}
                        <small class="text-muted">${project.sceneCount || 0} scenes</small>
                    </div>
                    <div class="progress project-progress">
                        <div class="progress-bar ${progress === 100 ? 'bg-success' : 'bg-primary'}" role="progressbar" style="width: ${progress}%;" aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </div>
            </div>
        `;
        
        // Add click handler to the card
        const card = colElement.querySelector('.project-card');
        card.addEventListener('click', (e) => {
            // Don't open project if clicking on action buttons
            if (e.target.closest('.project-actions')) {
                return;
            }
            
            // Navigate to project
            window.location.href = `/?project=${project.id}`;
        });
        
        return colElement;
    }
    
    /**
     * Set up event listeners for project action buttons
     */
    function setupProjectActionListeners() {
        // Share buttons
        document.querySelectorAll('.share-project-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const projectId = btn.dataset.id;
                showShareProjectModal(projectId);
            });
        });
        
        // Options buttons
        document.querySelectorAll('.project-options-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const projectId = btn.dataset.id;
                showProjectOptionsModal(projectId);
            });
        });
        
        // Project options modal buttons
        document.querySelectorAll('#project-options-modal button').forEach(btn => {
            btn.addEventListener('click', handleProjectOption);
        });
        
        // Copy link button
        const copyLinkBtn = document.getElementById('copy-link-btn');
        if (copyLinkBtn) {
            copyLinkBtn.addEventListener('click', () => {
                const linkInput = document.getElementById('share-link');
                if (linkInput) {
                    linkInput.select();
                    document.execCommand('copy');
                    showAlert('Link copied to clipboard', 'success');
                }
            });
        }
        
        // Share via email button
        const shareEmailBtn = document.getElementById('share-email-btn');
        if (shareEmailBtn) {
            shareEmailBtn.addEventListener('click', () => {
                const shareLink = document.getElementById('share-link').value;
                const mailtoLink = `mailto:?subject=Check out my MaiVid Studio project&body=I've created a music video project with MaiVid Studio that I'd like to share with you. You can view it here: ${shareLink}`;
                window.open(mailtoLink);
            });
        }
        
        // Share via social media buttons
        const shareFacebookBtn = document.getElementById('share-facebook-btn');
        if (shareFacebookBtn) {
            shareFacebookBtn.addEventListener('click', () => {
                const shareLink = document.getElementById('share-link').value;
                const facebookLink = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareLink)}`;
                window.open(facebookLink, '_blank', 'width=600,height=400');
            });
        }
        
        const shareTwitterBtn = document.getElementById('share-twitter-btn');
        if (shareTwitterBtn) {
            shareTwitterBtn.addEventListener('click', () => {
                const shareLink = document.getElementById('share-link').value;
                const twitterLink = `https://twitter.com/intent/tweet?url=${encodeURIComponent(shareLink)}&text=Check out my AI-generated music video:`;
                window.open(twitterLink, '_blank', 'width=600,height=400');
            });
        }
    }
    
    /**
     * Handle creating a new project
     */
    function handleCreateProject() {
        const user = auth.currentUser;
        if (!user) {
            showAlert('You must be logged in to create a project', 'danger');
            return;
        }
        
        // Get form values
        const projectName = document.getElementById('project-name').value;
        const projectDescription = document.getElementById('project-description').value;
        const projectType = document.querySelector('input[name="project-type"]:checked').value;
        
        // Validate form
        if (!projectName) {
            showAlert('Please enter a project name', 'warning');
            return;
        }
        
        // Show loading
        showLoading('Creating project...');
        
        // Create project in Firestore
        firestore.collection('projects').add({
            name: projectName,
            description: projectDescription,
            type: projectType,
            userId: user.uid,
            createdAt: firebase.firestore.FieldValue.serverTimestamp(),
            updatedAt: firebase.firestore.FieldValue.serverTimestamp(),
            currentStep: 0,
            sceneCount: 0,
            isPublic: false,
            projectData: {
                audioPath: null,
                lyrics: null,
                metadata: null,
                concept: null,
                storyline: null,
                scenes: [],
                storyboard: [],
                timeline: []
            }
        })
        .then(docRef => {
            hideLoading();
            newProjectModal.hide();
            
            // Reset form
            document.getElementById('project-name').value = '';
            document.getElementById('project-description').value = '';
            
            // Update user's project count
            firestore.collection('users').doc(user.uid).update({
                projectCount: firebase.firestore.FieldValue.increment(1)
            }).catch(error => {
                console.error('Failed to update project count:', error);
            });
            
            // Navigate to the new project
            window.location.href = `/?project=${docRef.id}`;
        })
        .catch(error => {
            hideLoading();
            console.error('Error creating project:', error);
            showAlert('Failed to create project. Please try again.', 'danger');
        });
    }
    
    /**
     * Show project options modal
     */
    function showProjectOptionsModal(projectId) {
        selectedProjectId = projectId;
        projectOptionsModal.show();
    }
    
    /**
     * Show share project modal
     */
    function showShareProjectModal(projectId) {
        selectedProjectId = projectId;
        
        // Generate share link
        const shareLink = document.getElementById('share-link');
        if (shareLink) {
            shareLink.value = `https://maivid.studio/p/${projectId}`;
        }
        
        // Show modal
        shareProjectModal.show();
        
        // Select the link for easy copying
        if (shareLink) {
            setTimeout(() => {
                shareLink.select();
            }, 300);
        }
    }
    
    /**
     * Handle project option button clicks
     */
    function handleProjectOption(e) {
        if (!selectedProjectId) return;
        
        const optionId = e.target.id;
        
        // Hide modal
        projectOptionsModal.hide();
        
        // Handle different options
        switch (optionId) {
            case 'rename-project-btn':
                handleRenameProject();
                break;
            case 'duplicate-project-btn':
                handleDuplicateProject();
                break;
            case 'export-project-btn':
                handleExportProject();
                break;
            case 'archive-project-btn':
                handleArchiveProject();
                break;
            case 'delete-project-btn':
                handleDeleteProject();
                break;
        }
    }
    
    /**
     * Handle renaming a project
     */
    function handleRenameProject() {
        // Find the project
        const project = projects.find(p => p.id === selectedProjectId);
        if (!project) return;
        
        // Prompt for new name
        const newName = prompt('Enter a new name for the project:', project.name);
        if (!newName) return;
        
        // Show loading
        showLoading('Renaming project...');
        
        // Update project in Firestore
        firestore.collection('projects').doc(selectedProjectId).update({
            name: newName,
            updatedAt: firebase.firestore.FieldValue.serverTimestamp()
        })
        .then(() => {
            hideLoading();
            showAlert('Project renamed successfully', 'success');
            
            // Reload projects
            loadProjects();
        })
        .catch(error => {
            hideLoading();
            console.error('Error renaming project:', error);
            showAlert('Failed to rename project. Please try again.', 'danger');
        });
    }
    
    /**
     * Handle duplicating a project
     */
    function handleDuplicateProject() {
        // Find the project
        const project = projects.find(p => p.id === selectedProjectId);
        if (!project) return;
        
        // Show loading
        showLoading('Duplicating project...');
        
        // Create a new project with the same data
        const newProject = {
            name: `${project.name} (Copy)`,
            description: project.description,
            type: project.type,
            userId: auth.currentUser.uid,
            createdAt: firebase.firestore.FieldValue.serverTimestamp(),
            updatedAt: firebase.firestore.FieldValue.serverTimestamp(),
            currentStep: project.currentStep,
            sceneCount: project.sceneCount,
            isPublic: false,
            thumbnailUrl: project.thumbnailUrl,
            projectData: project.projectData
        };
        
        // Add to Firestore
        firestore.collection('projects').add(newProject)
            .then(() => {
                hideLoading();
                showAlert('Project duplicated successfully', 'success');
                
                // Update user's project count
                firestore.collection('users').doc(auth.currentUser.uid).update({
                    projectCount: firebase.firestore.FieldValue.increment(1)
                }).catch(error => {
                    console.error('Failed to update project count:', error);
                });
                
                // Reload projects
                loadProjects();
            })
            .catch(error => {
                hideLoading();
                console.error('Error duplicating project:', error);
                showAlert('Failed to duplicate project. Please try again.', 'danger');
            });
    }
    
    /**
     * Handle exporting a project
     */
    function handleExportProject() {
        // Find the project
        const project = projects.find(p => p.id === selectedProjectId);
        if (!project) return;
        
        // Show loading
        showLoading('Preparing project export...');
        
        // Create export data
        const exportData = {
            name: project.name,
            description: project.description,
            type: project.type,
            createdAt: project.createdAt ? project.createdAt.toDate().toISOString() : new Date().toISOString(),
            updatedAt: project.updatedAt ? project.updatedAt.toDate().toISOString() : new Date().toISOString(),
            projectData: project.projectData
        };
        
        // Convert to JSON
        const jsonData = JSON.stringify(exportData, null, 2);
        
        // Create download link
        const blob = new Blob([jsonData], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${project.name.replace(/\s+/g, '_')}.maivid.json`;
        
        // Hide loading
        hideLoading();
        
        // Trigger download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showAlert('Project exported successfully', 'success');
    }
    
    /**
     * Handle archiving a project
     */
    function handleArchiveProject() {
        if (!confirm('Are you sure you want to archive this project?')) return;
        
        // Show loading
        showLoading('Archiving project...');
        
        // Update project in Firestore
        firestore.collection('projects').doc(selectedProjectId).update({
            archived: true,
            updatedAt: firebase.firestore.FieldValue.serverTimestamp()
        })
        .then(() => {
            hideLoading();
            showAlert('Project archived successfully', 'success');
            
            // Reload projects
            loadProjects();
        })
        .catch(error => {
            hideLoading();
            console.error('Error archiving project:', error);
            showAlert('Failed to archive project. Please try again.', 'danger');
        });
    }
    
    /**
     * Handle deleting a project
     */
    function handleDeleteProject() {
        if (!confirm('Are you sure you want to delete this project? This action cannot be undone.')) return;
        
        // Show loading
        showLoading('Deleting project...');
        
        // Delete project from Firestore
        firestore.collection('projects').doc(selectedProjectId).delete()
            .then(() => {
                hideLoading();
                showAlert('Project deleted successfully', 'success');
                
                // Update user's project count
                firestore.collection('users').doc(auth.currentUser.uid).update({
                    projectCount: firebase.firestore.FieldValue.increment(-1)
                }).catch(error => {
                    console.error('Failed to update project count:', error);
                });
                
                // Reload projects
                loadProjects();
            })
            .catch(error => {
                hideLoading();
                console.error('Error deleting project:', error);
                showAlert('Failed to delete project. Please try again.', 'danger');
            });
    }
    
    /**
     * Handle search input
     */
    function handleSearch() {
        const searchTerm = searchProjects.value.toLowerCase();
        
        // Filter projects by search term
        const filteredProjects = projects.filter(project => {
            // Search in name, description, and type
            return (
                project.name?.toLowerCase().includes(searchTerm) ||
                project.description?.toLowerCase().includes(searchTerm) ||
                project.type?.toLowerCase().includes(searchTerm)
            );
        });
        
        // Update the filter as well
        const currentFilter = filterProjects.value;
        applyFilter(filteredProjects, currentFilter);
    }
    
    /**
     * Handle filter select change
     */
    function handleFilter() {
        const filterValue = filterProjects.value;
        applyFilter(projects, filterValue);
    }
    
    /**
     * Apply filter to projects
     */
    function applyFilter(projectsToFilter, filterValue) {
        let filteredProjects = [...projectsToFilter];
        
        // Apply filter
        switch (filterValue) {
            case 'recent':
                // Already sorted by updatedAt
                break;
            case 'complete':
                filteredProjects = filteredProjects.filter(project => {
                    const progress = Math.min(100, ((project.currentStep || 0) / 8) * 100);
                    return progress === 100;
                });
                break;
            case 'in-progress':
                filteredProjects = filteredProjects.filter(project => {
                    const progress = Math.min(100, ((project.currentStep || 0) / 8) * 100);
                    return progress > 0 && progress < 100;
                });
                break;
            case 'all':
            default:
                // Show all projects
                break;
        }
        
        // Render filtered projects
        renderProjects(filteredProjects);
        
        // Show/hide empty state
        if (filteredProjects.length === 0) {
            if (emptyProjects) emptyProjects.style.display = 'block';
            if (projectsGrid) projectsGrid.style.display = 'none';
        } else {
            if (emptyProjects) emptyProjects.style.display = 'none';
            if (projectsGrid) projectsGrid.style.display = 'flex';
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
    
    // Initialize the projects page
    initProjectsPage();
});
