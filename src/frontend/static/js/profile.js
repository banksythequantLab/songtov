/**
 * MaiVid Studio - Profile JS
 * Handles user profile management and settings
 */

// Wait for DOM content to load
document.addEventListener('DOMContentLoaded', function() {
    // Get Firebase instances
    const auth = firebase.auth();
    const firestore = firebase.firestore();
    const storage = firebase.storage();
    
    // References to DOM elements
    const profileForm = document.getElementById('profile-form');
    const accountForm = document.getElementById('account-form');
    const editProfilePhotoBtn = document.getElementById('edit-profile-photo-btn');
    const profilePhotoUpload = document.getElementById('profile-photo-upload');
    const deleteAccountBtn = document.getElementById('delete-account-btn');
    const confirmDeleteAccountBtn = document.getElementById('confirm-delete-account-btn');
    const deleteAccountModal = new bootstrap.Modal(document.getElementById('delete-account-modal'));
    
    /**
     * Initialize profile page
     */
    function initProfilePage() {
        // Set up form submit events
        if (profileForm) {
            profileForm.addEventListener('submit', handleProfileUpdate);
        }
        
        if (accountForm) {
            accountForm.addEventListener('submit', handlePasswordUpdate);
        }
        
        // Set up profile photo upload
        if (editProfilePhotoBtn && profilePhotoUpload) {
            editProfilePhotoBtn.addEventListener('click', () => {
                profilePhotoUpload.click();
            });
            
            profilePhotoUpload.addEventListener('change', handleProfilePhotoUpload);
        }
        
        // Set up delete account button
        if (deleteAccountBtn) {
            deleteAccountBtn.addEventListener('click', () => {
                deleteAccountModal.show();
            });
        }
        
        // Set up confirm delete account button
        if (confirmDeleteAccountBtn) {
            confirmDeleteAccountBtn.addEventListener('click', handleDeleteAccount);
        }
    }
    
    /**
     * Handle profile form submission
     */
    function handleProfileUpdate(e) {
        e.preventDefault();
        
        const user = auth.currentUser;
        if (!user) {
            showAlert('You must be logged in to update your profile', 'danger');
            return;
        }
        
        // Get form values
        const displayName = document.getElementById('display-name').value;
        const bio = document.getElementById('bio').value;
        const website = document.getElementById('website').value;
        
        // Show loading
        showLoading('Updating profile...');
        
        // Update Firebase Auth display name
        user.updateProfile({
            displayName: displayName
        })
        .then(() => {
            // Update Firestore user document
            return firestore.collection('users').doc(user.uid).update({
                displayName: displayName,
                bio: bio,
                website: website,
                updatedAt: firebase.firestore.FieldValue.serverTimestamp()
            });
        })
        .then(() => {
            hideLoading();
            showAlert('Profile updated successfully', 'success');
            
            // Update UI
            const profileName = document.getElementById('profile-name');
            if (profileName) {
                profileName.textContent = displayName || 'Unnamed User';
            }
        })
        .catch(error => {
            hideLoading();
            console.error('Profile update error:', error);
            showAlert('Failed to update profile. Please try again.', 'danger');
        });
    }
    
    /**
     * Handle password update form submission
     */
    function handlePasswordUpdate(e) {
        e.preventDefault();
        
        const user = auth.currentUser;
        if (!user) {
            showAlert('You must be logged in to update your password', 'danger');
            return;
        }
        
        // Get form values
        const newPassword = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        
        // Validate passwords
        if (!newPassword) {
            showAlert('Please enter a new password', 'warning');
            return;
        }
        
        if (newPassword !== confirmPassword) {
            showAlert('Passwords do not match', 'danger');
            return;
        }
        
        // Show loading
        showLoading('Updating password...');
        
        // Update password
        user.updatePassword(newPassword)
            .then(() => {
                hideLoading();
                showAlert('Password updated successfully', 'success');
                
                // Clear form
                document.getElementById('new-password').value = '';
                document.getElementById('confirm-password').value = '';
            })
            .catch(error => {
                hideLoading();
                console.error('Password update error:', error);
                
                if (error.code === 'auth/requires-recent-login') {
                    showAlert('For security reasons, please log out and log in again before changing your password', 'warning');
                } else {
                    showAlert('Failed to update password. Please try again.', 'danger');
                }
            });
    }
    
    /**
     * Handle profile photo upload
     */
    function handleProfilePhotoUpload(e) {
        const user = auth.currentUser;
        if (!user) {
            showAlert('You must be logged in to update your profile photo', 'danger');
            return;
        }
        
        const file = e.target.files[0];
        if (!file) return;
        
        // Validate file type
        const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
        if (!validTypes.includes(file.type)) {
            showAlert('Please select a valid image file (JPEG, PNG, or GIF)', 'warning');
            return;
        }
        
        // Show loading
        showLoading('Uploading profile photo...');
        
        // Create storage reference
        const storageRef = storage.ref();
        const profilePhotoRef = storageRef.child(`users/${user.uid}/profile_photo`);
        
        // Upload file
        profilePhotoRef.put(file)
            .then(snapshot => {
                // Get download URL
                return snapshot.ref.getDownloadURL();
            })
            .then(downloadURL => {
                // Update user profile
                return user.updateProfile({
                    photoURL: downloadURL
                });
            })
            .then(() => {
                // Update Firestore user document
                return firestore.collection('users').doc(user.uid).update({
                    photoURL: user.photoURL,
                    updatedAt: firebase.firestore.FieldValue.serverTimestamp()
                });
            })
            .then(() => {
                hideLoading();
                showAlert('Profile photo updated successfully', 'success');
                
                // Update UI
                const profileImage = document.getElementById('profile-image');
                if (profileImage) {
                    profileImage.src = user.photoURL;
                }
            })
            .catch(error => {
                hideLoading();
                console.error('Profile photo upload error:', error);
                showAlert('Failed to update profile photo. Please try again.', 'danger');
            });
    }
    
    /**
     * Handle account deletion
     */
    function handleDeleteAccount() {
        const user = auth.currentUser;
        if (!user) {
            showAlert('You must be logged in to delete your account', 'danger');
            return;
        }
        
        // Get confirmation email
        const confirmEmail = document.getElementById('confirm-delete-email').value;
        
        // Validate email
        if (confirmEmail !== user.email) {
            showAlert('Email does not match your account email', 'danger');
            return;
        }
        
        // Show loading
        showLoading('Deleting account...');
        
        // Delete user's data from Firestore
        const batch = firestore.batch();
        
        // Get user's projects
        firestore.collection('projects')
            .where('userId', '==', user.uid)
            .get()
            .then(projectsSnapshot => {
                // Add project deletions to batch
                projectsSnapshot.forEach(doc => {
                    batch.delete(doc.ref);
                });
                
                // Add user document deletion to batch
                const userRef = firestore.collection('users').doc(user.uid);
                batch.delete(userRef);
                
                // Commit the batch
                return batch.commit();
            })
            .then(() => {
                // Delete user from Authentication
                return user.delete();
            })
            .then(() => {
                hideLoading();
                deleteAccountModal.hide();
                
                // Show success message briefly, then redirect
                showAlert('Your account has been deleted', 'success');
                
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
            })
            .catch(error => {
                hideLoading();
                console.error('Account deletion error:', error);
                
                if (error.code === 'auth/requires-recent-login') {
                    showAlert('For security reasons, please log out and log in again before deleting your account', 'warning');
                } else {
                    showAlert('Failed to delete account. Please try again.', 'danger');
                }
                
                deleteAccountModal.hide();
            });
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
    
    // Initialize the profile page
    initProfilePage();
});
