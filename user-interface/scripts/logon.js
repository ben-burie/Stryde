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

document.getElementById('loginForm').addEventListener('submit', (e) => {
    e.preventDefault();
    alert('Login submitted!');
});

document.getElementById('signupForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const password = document.getElementById('signupPassword').value;
    const confirm = document.getElementById('confirmPassword').value;
    
    if (password !== confirm) {
        alert('Passwords do not match!');
        return;
    }
    
    alert('Account created!');
});