const API_BASE_URL = 'http://127.0.0.1:5000/api';


function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (message === '') return;
    
    const chatMessages = document.getElementById('chatMessages');
    
    // User message
    const userMessage = document.createElement('div');
    userMessage.className = 'message user';
    userMessage.textContent = message;
    chatMessages.appendChild(userMessage);
    
    input.value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Simulate coach response
    setTimeout(() => {
        const coachMessage = document.createElement('div');
        coachMessage.className = 'message coach';
        coachMessage.textContent = getCoachResponse(message);
        chatMessages.appendChild(coachMessage);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 500);
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function getCoachResponse(message) {
    const responses = [
        "That sounds great! Keep me posted on your progress.",
        "I love your commitment to training. Let's see what we can achieve!",
        "Based on your stats, you're doing really well. Stay consistent!",
        "Make sure to get enough rest between your intense workouts.",
        "Your VDOT is improving! Let's push even further.",
        "Remember to hydrate well during your runs."
    ];
    return responses[Math.floor(Math.random() * responses.length)];
}

function handleLogout() {
    if (confirm('Are you sure you want to logout?')) {
        alert('Logged out successfully!');
        // In a real app, this would redirect to login page
    }
}

// Profile menu handling
const profileButton = document.getElementById('profileButton');
const profileMenu = document.getElementById('profileMenu');
const uploadInput = document.getElementById('uploadInput');

function toggleProfileMenu(open) {
    const show = typeof open === 'boolean' ? open : profileMenu.classList.contains('hidden');
    if (show) {
        profileMenu.classList.remove('hidden');
        profileButton.setAttribute('aria-expanded', 'true');
        profileMenu.setAttribute('aria-hidden', 'false');
        // move focus to first item
        const first = profileMenu.querySelector('.profile-menu-item');
        if (first) first.focus();
    } else {
        profileMenu.classList.add('hidden');
        profileButton.setAttribute('aria-expanded', 'false');
        profileMenu.setAttribute('aria-hidden', 'true');
    }
}

profileButton.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleProfileMenu();
});

// Close when clicking outside
document.addEventListener('click', (e) => {
    if (!profileButton.contains(e.target) && !profileMenu.contains(e.target)) {
        toggleProfileMenu(false);
    }
});

// Esc key closes the menu
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        toggleProfileMenu(false);
    }
});

// Menu item handlers
document.getElementById('uploadDataBtn').addEventListener('click', () => {
    toggleProfileMenu(false);
    uploadInput.click();
});

uploadInput.addEventListener('change', (e) => {
    const file = e.target.files && e.target.files[0];
    if (file) {
        uploadData(file);
    } else {
        alert('No file selected');
    }
});

document.getElementById('accountSettingsBtn').addEventListener('click', () => {
    toggleProfileMenu(false);
    alert('Open account settings');
});

document.getElementById('logoutBtn').addEventListener('click', () => {
    toggleProfileMenu(false);
    handleLogout();
});

// FLASK ENDPOINTS BELOW ------------------------------------
function uploadData(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    fetch(`${API_BASE_URL}/upload-data`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.text())
    .then(text => {
        console.log('Raw response:', text);
        const result = JSON.parse(text);
        
        if (result.error) {
            alert('Error: ' + result.error);
        } else {
            document.getElementById('vdot-value').textContent = parseFloat(result.vdot).toFixed(2);
            document.querySelector('.hr-value').textContent = Math.round(result.avg_hr) + ' BPM';
            document.querySelector('.fivek-prediction-time').textContent = result.fivek_time;
            document.querySelector('.half-prediction-time').textContent = result.half_time;
            document.querySelector('.full-prediction-time').textContent = result.full_time;
        }
    })
    .catch(error => {
        alert('Upload failed: ' + error.message);
    });
}