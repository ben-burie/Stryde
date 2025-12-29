const API_BASE_URL = 'http://localhost:5000/api';

const profileButton = document.getElementById('profileButton');
const profileMenu = document.getElementById('profileMenu');
const uploadDataBtn = document.getElementById('uploadDataBtn');
const uploadModal = document.getElementById('uploadModal');
const uploadHeader = document.getElementById('uploadHeader');
const uploadArea = document.getElementById('uploadArea');
const uploadInput = document.getElementById('uploadInput');
const loadingState = document.getElementById('loadingState');
const errorMessage = document.getElementById('errorMessage');

var DATA_UPLOADED = false;

profileButton.addEventListener('click', () => {
    const isHidden = profileMenu.classList.toggle('hidden');
    profileMenu.setAttribute('aria-hidden', isHidden ? 'true' : 'false');
});

document.addEventListener('click', (e) => {
    if (!profileButton.contains(e.target) && !profileMenu.contains(e.target)) {
        profileMenu.classList.add('hidden');
        profileMenu.setAttribute('aria-hidden', 'true');
    }
});

uploadDataBtn.addEventListener('click', () => {
    profileMenu.classList.add('hidden');
    profileMenu.setAttribute('aria-hidden', 'true');
    openUploadModal();
});

function openUploadModal() {
    uploadModal.classList.add('show');
    resetUploadModal();
}

function closeUploadModal() {
    uploadModal.classList.remove('show');
    resetUploadModal();
}

function resetUploadModal() {
    uploadInput.value = '';
    errorMessage.classList.remove('show');
    loadingState.classList.remove('show');
    uploadArea.style.display = 'block';
}

uploadArea.addEventListener('click', () => uploadInput.click());

uploadInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        uploadData(e.target.files[0]);
    }
});

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
        uploadData(e.dataTransfer.files[0]);
    }
});

function uploadData(file) {
    if (!file.name.endsWith('.csv')) {
        showError('Please upload a CSV file');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    loadingState.classList.add('show');
    uploadArea.style.display = 'none';
    uploadHeader.textContent = 'Processing Your Data';
    errorMessage.classList.remove('show');
    document.getElementById('closeModalBtn').classList.add('hidden');

    fetch(`${API_BASE_URL}/upload-data`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(result => {
        if (result.error) {
            showError('Error: ' + result.error);
            document.getElementById('closeModalBtn').classList.remove('hidden');
        } else {
            displayResults(result);
            closeUploadModal();
            DATA_UPLOADED = true;
        }
    })
    .catch(error => {
        showError('Upload failed: ' + error.message);
        document.getElementById('closeModalBtn').classList.remove('hidden');
    })
    .finally(() => {
        loadingState.classList.remove('show');
    });
}

function displayResults(result) {
    document.getElementById('vdot-value').textContent = parseFloat(result.vdot).toFixed(2);
    document.getElementById('hr-value').textContent = Math.round(result.avg_hr) + ' BPM';
    document.querySelector('.fivek-prediction-time').textContent = result.fivek_time;
    document.querySelector('.half-prediction-time').textContent = result.half_time;
    document.querySelector('.full-prediction-time').textContent = result.full_time;
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
    uploadArea.style.display = 'block';
    loadingState.classList.remove('show');
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    if (message) {
        const chatMessages = document.getElementById('chatMessages');
        const userMsg = document.createElement('div');
        userMsg.className = 'message user';
        userMsg.textContent = message;
        chatMessages.appendChild(userMsg);
        input.value = '';
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function generateTrainingPlan() {
    if (!DATA_UPLOADED) {
        alert('Please upload your data first to generate a training plan.');
        return;
    }
    const trainingPlanBox = document.getElementById('trainingPlanBox');
    const generatePlanBtn = document.getElementById('generatePlanBtn');
    const predictedFitnessSection = document.getElementById('predictedFitnessSection');
    
    trainingPlanBox.classList.remove('hidden');
    predictedFitnessSection.style.display = 'block';
    generatePlanBtn.style.display = 'none';
}

function switchTab(tabName) {
    const trainingTab = document.getElementById('training-tab');
    const chatTab = document.getElementById('chat-tab');
    const predictedFitnessSection = document.getElementById('predictedFitnessSection');
    const buttons = document.querySelectorAll('.tab-button');
    
    buttons.forEach(btn => btn.classList.remove('active'));
    
    if (tabName === 'training') {
        trainingTab.classList.add('active');
        chatTab.classList.remove('active');
        buttons[0].classList.add('active');
        if (document.getElementById('generatePlanBtn').style.display === 'none') {
                    predictedFitnessSection.style.display = 'block';
        }
    } else if (tabName === 'chat') {
        chatTab.classList.add('active');
        trainingTab.classList.remove('active');
        buttons[1].classList.add('active');
        // Hide predicted fitness when switching to chat tab
        predictedFitnessSection.style.display = 'none';
    }
}