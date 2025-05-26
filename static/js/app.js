// Enomy-Finances Main JavaScript

// Global variables
let currentUser = null;
let isAuthenticated = false;

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
    updateNavigation();
});

// Authentication functions
async function login() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    if (!username || !password) {
        showError('loginError', 'Please enter both username and password');
        return;
    }

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',  // Include cookies
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            currentUser = data.user;
            isAuthenticated = true;
            updateNavigation();
            hideModal('loginModal');
            showSuccess('loginSuccess', 'Login successful!');

            // Clear form
            document.getElementById('loginForm').reset();
            hideError('loginError');

            // Redirect to appropriate dashboard based on user type
            if (window.location.pathname === '/') {
                setTimeout(() => {
                    if (currentUser.user_type === 'admin') {
                        window.location.href = '/admin';
                    } else {
                        window.location.href = '/dashboard';
                    }
                }, 1000);
            }
        } else {
            showError('loginError', data.error || 'Login failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('loginError', 'Network error. Please try again.');
    }
}

async function register() {
    const formData = {
        username: document.getElementById('registerUsername').value,
        email: document.getElementById('registerEmail').value,
        password: document.getElementById('registerPassword').value,
        first_name: document.getElementById('registerFirstName').value,
        last_name: document.getElementById('registerLastName').value,
        phone: document.getElementById('registerPhone').value
    };

    // Validate required fields
    const requiredFields = ['username', 'email', 'password', 'first_name', 'last_name'];
    for (let field of requiredFields) {
        if (!formData[field]) {
            showError('registerError', `${field.replace('_', ' ')} is required`);
            return;
        }
    }

    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',  // Include cookies
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess('registerSuccess', 'Registration successful! You can now login.');
            document.getElementById('registerForm').reset();
            hideError('registerError');

            // Switch to login modal after 2 seconds
            setTimeout(() => {
                hideModal('registerModal');
                showModal('loginModal');
            }, 2000);
        } else {
            showError('registerError', data.error || 'Registration failed');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showError('registerError', 'Network error. Please try again.');
    }
}

async function logout() {
    try {
        const response = await fetch('/api/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include'  // Include cookies
        });

        if (response.ok) {
            currentUser = null;
            isAuthenticated = false;
            updateNavigation();

            // Redirect to home page
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Logout error:', error);
    }
}

function checkAuthStatus() {
    // Check if user is logged in by making a request to user profile
    fetch('/api/user/profile', {
        credentials: 'include'  // Include cookies
    })
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Not authenticated');
        })
        .then(data => {
            currentUser = data.user;
            isAuthenticated = true;
            updateNavigation();
        })
        .catch(error => {
            currentUser = null;
            isAuthenticated = false;
            updateNavigation();
        });
}

function updateNavigation() {
    const loginNav = document.getElementById('nav-login');
    const registerNav = document.getElementById('nav-register');
    const userNav = document.getElementById('nav-user');
    const usernameSpan = document.getElementById('nav-username');

    if (isAuthenticated && currentUser) {
        loginNav.style.display = 'none';
        registerNav.style.display = 'none';
        userNav.style.display = 'block';
        usernameSpan.textContent = currentUser.first_name || currentUser.username;

        // Update dashboard link based on user type
        const dashboardLink = document.querySelector('a[href="/dashboard"]');
        if (dashboardLink && currentUser.user_type === 'admin') {
            dashboardLink.href = '/admin';
            dashboardLink.innerHTML = '<i class="fas fa-cog me-1"></i>Admin Dashboard';
        }
    } else {
        loginNav.style.display = 'block';
        registerNav.style.display = 'block';
        userNav.style.display = 'none';
    }
}

// Utility functions
function showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }
}

function hideError(elementId) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.style.display = 'none';
    }
}

function showSuccess(elementId, message) {
    const successElement = document.getElementById(elementId);
    if (successElement) {
        successElement.textContent = message;
        successElement.style.display = 'block';
    }
}

function hideSuccess(elementId) {
    const successElement = document.getElementById(elementId);
    if (successElement) {
        successElement.style.display = 'none';
    }
}

function showModal(modalId) {
    const modal = new bootstrap.Modal(document.getElementById(modalId));
    modal.show();
}

function hideModal(modalId) {
    const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
    if (modal) {
        modal.hide();
    }
}

function formatCurrency(amount, currency = 'GBP') {
    return new Intl.NumberFormat('en-GB', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

function formatNumber(number, decimals = 2) {
    return new Intl.NumberFormat('en-GB', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(number);
}

function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.add('loading');
    }
}

function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.remove('loading');
    }
}

// API helper functions
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include'  // Include cookies in the request
    };

    // Merge headers properly
    if (options.headers) {
        defaultOptions.headers = { ...defaultOptions.headers, ...options.headers };
    }

    const mergedOptions = { ...defaultOptions, ...options };

    try {
        const response = await fetch(url, mergedOptions);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }

        return data;
    } catch (error) {
        console.error('API request error:', error);
        throw error;
    }
}

// Form validation
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    const minLength = 8;
    const hasUpper = /[A-Z]/.test(password);
    const hasLower = /[a-z]/.test(password);
    const hasNumber = /\d/.test(password);

    return password.length >= minLength && hasUpper && hasLower && hasNumber;
}

// Event listeners for forms
document.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        const activeModal = document.querySelector('.modal.show');
        if (activeModal) {
            if (activeModal.id === 'loginModal') {
                login();
            } else if (activeModal.id === 'registerModal') {
                register();
            }
        }
    }
});

// Clear form errors when user starts typing
document.addEventListener('input', function(e) {
    if (e.target.type === 'text' || e.target.type === 'email' || e.target.type === 'password') {
        const formGroup = e.target.closest('.modal-body');
        if (formGroup) {
            const errorElement = formGroup.querySelector('.alert-danger');
            if (errorElement) {
                errorElement.style.display = 'none';
            }
        }
    }
});

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    // You could send this to a logging service
});

// Handle network errors
window.addEventListener('online', function() {
    console.log('Connection restored');
});

window.addEventListener('offline', function() {
    console.log('Connection lost');
    alert('You are currently offline. Some features may not work properly.');
});
