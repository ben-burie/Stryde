const API_BASE_URL = 'http://localhost:5000';

function switchToLogin() {
    document.getElementById('loginForm').classList.remove('hidden');
    document.getElementById('signupForm').classList.add('hidden');
    
    document.getElementById('loginBtn').classList.add('active');
    document.getElementById('loginBtn').classList.remove('inactive');
    document.getElementById('signupBtn').classList.remove('active');
    document.getElementById('signupBtn').classList.add('inactive');
    
    document.getElementById('sliderBg').classList.remove('active');
}

function switchToSignup() {
    document.getElementById('loginForm').classList.add('hidden');
    document.getElementById('signupForm').classList.remove('hidden');
    
    document.getElementById('loginBtn').classList.remove('active');
    document.getElementById('loginBtn').classList.add('inactive');
    document.getElementById('signupBtn').classList.add('active');
    document.getElementById('signupBtn').classList.remove('inactive');
    
    document.getElementById('sliderBg').classList.add('active');
}

// LOGIN FORM
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const btn = document.getElementById('loginSubmitBtn');
    
    btn.disabled = true;
    btn.textContent = 'Logging in...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();

        if (!response.ok) {
            showAlert('loginAlert', `Login failed: ${data.message || data.error}`, 'danger');
        } else {
            // Save token to localStorage
            if (data.token) {
                localStorage.setItem('authToken', data.token);
                showAlert('loginAlert', 'Login successful! Redirecting...', 'success');
                
                // Redirect to home after 1 second
                setTimeout(() => {
                    window.location.href = '/home.html';
                }, 1000);
            }
        }
    } catch (err) {
        showAlert('loginAlert', `Error: ${err.message}`, 'danger');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Log In';
    }
});

// SIGNUP FORM
document.getElementById('signupForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    const confirm = document.getElementById('confirmPassword').value;
    const btn = document.getElementById('signupSubmitBtn');
    
    // Validate passwords match
    if (password !== confirm) {
        showAlert('signupAlert', 'Passwords do not match!', 'danger');
        return;
    }
    
    // Validate password length
    if (password.length < 6) {
        showAlert('signupAlert', 'Password must be at least 6 characters!', 'danger');
        return;
    }
    
    btn.disabled = true;
    btn.textContent = 'Creating account...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            showAlert('signupAlert', `Signup failed: ${data.message || data.error}`, 'danger');
        } else {
            showAlert('signupAlert', 'Account created! Switching to login...', 'success');
            document.getElementById('signupForm').reset();
            
            setTimeout(() => {
                switchToLogin();
            }, 1500);
        }
    } catch (err) {
        showAlert('signupAlert', `Error: ${err.message}`, 'danger');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Create Account';
    }
});

// HELPER FUNCTION
function showAlert(elementId, message, type = 'danger') {
    const alertEl = document.getElementById(elementId);
    if (alertEl) {
        alertEl.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>`;
    }
}