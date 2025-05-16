/**
 * MaiVid Studio - Authentication JS
 * Handles Firebase authentication, user management, and session handling
 */

// Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyAkvC6JUKaY4jGpJfmPm8WEUbRWnUvA8Bk",
    authDomain: "maivid-studio.firebaseapp.com",
    projectId: "maivid-studio",
    storageBucket: "maivid-studio.appspot.com",
    messagingSenderId: "789632542316",
    appId: "1:789632542316:web:fad7bc3e724cf2a49a8c6e",
    measurementId: "G-RS2YE4BN4W"
};

// Initialize Firebase (with compat version for easier API)
if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
}

// Auth instance
const auth = firebase.auth();

// Firestore instance
let db = null;
try {
    db = firebase.firestore();
} catch (e) {
    console.error("Firestore initialization error:", e);
}

// Current user state
let currentUser = null;

// Check if user is on login/register page
const isAuthPage = window.location.pathname.includes('login') || window.location.pathname.includes('register');

/**
 * Initialize auth state listener
 */
function initAuth() {
    // Set up auth state listener
    auth.onAuthStateChanged(user => {
        if (user) {
            currentUser = user;
            console.log('User signed in:', user.email);
            
            // Create/update user document in Firestore if available
            if (db) {
                updateUserDocument(user);
            }
            
            // If on login/register page, redirect to home or projects
            if (isAuthPage) {
                window.location.href = '/projects';
            } else {
                // Update UI for logged in state
                updateAuthUI(true);
            }
        } else {
            currentUser = null;
            console.log('No user signed in');
            
            // If not on auth page, redirect to login
            if (!isAuthPage) {
                window.location.href = '/login';
            } else {
                // Update UI for logged out state
                updateAuthUI(false);
            }
        }
    });
    
    // Set up form event listeners
    setupEventListeners();
}

/**
 * Update user document in Firestore
 */
function updateUserDocument(user) {
    const userRef = db.collection('users').doc(user.uid);
    
    // Update last login and basic info
    userRef.set({
        email: user.email,
        displayName: user.displayName || '',
        photoURL: user.photoURL || '',
        lastLogin: firebase.firestore.FieldValue.serverTimestamp()
    }, { merge: true })
    .then(() => {
        console.log('User document updated');
    })
    .catch(error => {
        console.error('Error updating user document:', error);
    });
}

/**
 * Update UI based on auth state
 */
function updateAuthUI(isLoggedIn) {
    // Update logout button visibility if it exists
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.style.display = isLoggedIn ? 'block' : 'none';
    }
    
    // Specific page updates
    const currentPath = window.location.pathname;
    
    if (currentPath.includes('profile') && isLoggedIn) {
        updateProfileUI();
    }
    
    if (currentPath.includes('projects') && isLoggedIn) {
        // Projects page will handle its own UI update
    }
}

/**
 * Set up auth-related event listeners
 */
function setupEventListeners() {
    // Login form
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Register form
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
    
    // Google sign-in buttons
    const googleLoginBtn = document.getElementById('google-login');
    if (googleLoginBtn) {
        googleLoginBtn.addEventListener('click', handleGoogleSignIn);
    }
    
    const googleSignupBtn = document.getElementById('google-signup');
    if (googleSignupBtn) {
        googleSignupBtn.addEventListener('click', handleGoogleSignIn);
    }
    
    // Logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
}

/**
 * Handle email/password login
 */
function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const rememberMe = document.getElementById('remember-me').checked;
    
    // Set persistence based on remember me
    const persistence = rememberMe ? 
        firebase.auth.Auth.Persistence.LOCAL : 
        firebase.auth.Auth.Persistence.SESSION;
    
    // Show loading
    showLoading('Signing in...');
    
    // Set persistence then sign in
    auth.setPersistence(persistence)
        .then(() => {
            return auth.signInWithEmailAndPassword(email, password);
        })
        .then(userCredential => {
            hideLoading();
            console.log('Login successful');
            window.location.href = '/projects';
        })
        .catch(error => {
            hideLoading();
            console.error('Login error:', error);
            showErrorMessage(getAuthErrorMessage(error.code));
        });
}

/**
 * Handle email/password registration
 */
function handleRegister(e) {
    e.preventDefault();
    
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    const termsAccepted = document.getElementById('terms').checked;
    
    // Validate form
    if (password !== confirmPassword) {
        showErrorMessage('Passwords do not match');
        return;
    }
    
    if (!termsAccepted) {
        showErrorMessage('You must accept the Terms of Service and Privacy Policy');
        return;
    }
    
    // Show loading
    showLoading('Creating account...');
    
    // Create user
    auth.createUserWithEmailAndPassword(email, password)
        .then(userCredential => {
            const user = userCredential.user;
            
            // Update profile with display name
            return user.updateProfile({
                displayName: name
            });
        })
        .then(() => {
            hideLoading();
            console.log('Registration successful');
            window.location.href = '/projects';
        })
        .catch(error => {
            hideLoading();
            console.error('Registration error:', error);
            showErrorMessage(getAuthErrorMessage(error.code));
        });
}

/**
 * Handle Google sign-in
 */
function handleGoogleSignIn() {
    const provider = new firebase.auth.GoogleAuthProvider();
    
    // Show loading
    showLoading('Signing in with Google...');
    
    auth.signInWithPopup(provider)
        .then(result => {
            hideLoading();
            console.log('Google sign-in successful');
            window.location.href = '/projects';
        })
        .catch(error => {
            hideLoading();
            console.error('Google sign-in error:', error);
            showErrorMessage(getAuthErrorMessage(error.code));
        });
}

/**
 * Handle logout
 */
function handleLogout() {
    // Show loading
    showLoading('Signing out...');
    
    auth.signOut()
        .then(() => {
            hideLoading();
            console.log('Logout successful');
            window.location.href = '/login';
        })
        .catch(error => {
            hideLoading();
            console.error('Logout error:', error);
            alert('Failed to sign out. Please try again.');
        });
}

/**
 * Update profile UI with user data
 */
function updateProfileUI() {
    if (!currentUser) return;
    
    // Set profile image
    const profileImage = document.getElementById('profile-image');
    if (profileImage && currentUser.photoURL) {
        profileImage.src = currentUser.photoURL;
    }
    
    // Set profile name and email
    const profileName = document.getElementById('profile-name');
    if (profileName) {
        profileName.textContent = currentUser.displayName || 'Unnamed User';
    }
    
    const profileEmail = document.getElementById('profile-email');
    if (profileEmail) {
        profileEmail.textContent = currentUser.email;
    }
    
    // Set email in account form
    const emailField = document.getElementById('email');
    if (emailField) {
        emailField.value = currentUser.email;
    }
    
    // Set display name in profile form
    const displayNameField = document.getElementById('display-name');
    if (displayNameField) {
        displayNameField.value = currentUser.displayName || '';
    }
    
    // Set member since date
    const memberSince = document.getElementById('member-since');
    if (memberSince) {
        const createdAt = new Date(currentUser.metadata.creationTime);
        memberSince.textContent = createdAt.toLocaleDateString();
    }
    
    // If Firestore is available, get additional user data
    if (db) {
        db.collection('users').doc(currentUser.uid).get()
            .then(doc => {
                if (doc.exists) {
                    const userData = doc.data();
                    
                    // Set bio and website if they exist
                    const bioField = document.getElementById('bio');
                    if (bioField && userData.bio) {
                        bioField.value = userData.bio;
                    }
                    
                    const websiteField = document.getElementById('website');
                    if (websiteField && userData.website) {
                        websiteField.value = userData.website;
                    }
                    
                    // Set project count
                    const projectCount = document.getElementById('project-count');
                    if (projectCount && userData.projectCount) {
                        projectCount.textContent = userData.projectCount;
                    }
                    
                    // Set video count
                    const videoCount = document.getElementById('video-count');
                    if (videoCount && userData.videoCount) {
                        videoCount.textContent = userData.videoCount;
                    }
                    
                    // Set account type
                    const accountType = document.getElementById('account-type');
                    if (accountType && userData.accountType) {
                        accountType.textContent = userData.accountType;
                    }
                }
            })
            .catch(error => {
                console.error('Error getting user data:', error);
            });
    }
}

/**
 * Show error message in error container
 */
function showErrorMessage(message) {
    const errorContainer = document.getElementById('error-message');
    if (errorContainer) {
        errorContainer.textContent = message;
        errorContainer.style.display = 'block';
        
        // Hide after 5 seconds
        setTimeout(() => {
            errorContainer.style.display = 'none';
        }, 5000);
    }
}

/**
 * Get user-friendly error message based on Firebase error code
 */
function getAuthErrorMessage(errorCode) {
    switch (errorCode) {
        case 'auth/email-already-in-use':
            return 'This email is already in use by another account.';
        case 'auth/invalid-email':
            return 'The email address is not valid.';
        case 'auth/weak-password':
            return 'The password is too weak. Please use at least 6 characters.';
        case 'auth/user-disabled':
            return 'This account has been disabled.';
        case 'auth/user-not-found':
            return 'No account found with this email.';
        case 'auth/wrong-password':
            return 'Incorrect password. Please try again.';
        case 'auth/too-many-requests':
            return 'Too many unsuccessful login attempts. Please try again later.';
        case 'auth/popup-closed-by-user':
            return 'Sign in was cancelled. Please try again.';
        default:
            return 'An error occurred. Please try again.';
    }
}

/**
 * Show loading indicator
 */
function showLoading(message = 'Loading...') {
    // Create loading element if it doesn't exist
    let loadingEl = document.getElementById('loading-indicator');
    
    if (!loadingEl) {
        loadingEl = document.createElement('div');
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
    } else {
        // Update message
        const messageEl = loadingEl.querySelector('.text-dark');
        if (messageEl) {
            messageEl.textContent = message;
        }
        
        // Show the loading indicator
        loadingEl.style.display = 'flex';
    }
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
 * Get current user
 */
function getCurrentUser() {
    return currentUser;
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!currentUser;
}

// Initialize auth when DOM is loaded
document.addEventListener('DOMContentLoaded', initAuth);

// Export for use in other modules
window.authModule = {
    getCurrentUser,
    isAuthenticated
};
