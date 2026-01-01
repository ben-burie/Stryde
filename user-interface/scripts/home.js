const API_BASE_URL = 'http://localhost:5000';

// Prevent back button
window.history.pushState(null, null, window.location.href);
window.onpopstate = function() {
    window.history.pushState(null, null, window.location.href);
};

// On page load, verify user is authenticated
window.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('authToken');
    
    if (!token) {
        window.location.href = '/';
        return;
    }
    
    // Verify token is valid
    try {
        const response = await fetch(`${API_BASE_URL}/api/verify-token`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            localStorage.removeItem('authToken');
            window.location.replace('/');
        }

        // Fetch user data
        const dataResponse = await fetch(`${API_BASE_URL}/api/get-user-data`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (dataResponse.ok) {
            const userData = await dataResponse.json();
            DATA_UPLOADED = true;

            document.getElementById('vdot-value').textContent = parseFloat(userData.vdot).toFixed(2);
            document.getElementById('hr-value').textContent = Math.round(userData.avg_hr) + ' BPM';
            document.querySelector('.fivek-prediction-time').textContent = userData.fivek_time;
            document.querySelector('.half-prediction-time').textContent = userData.half_time;
            document.querySelector('.full-prediction-time').textContent = userData.full_time;
        } else {
            console.error('Failed to fetch user data');
        }

    } catch (error) {
        console.error('Token verification failed:', error);
        localStorage.removeItem('authToken');
        window.location.replace('/');
    }
});

// Get DOM elements
const profileButton = document.getElementById('profileButton');
const profileMenu = document.getElementById('profileMenu');
const uploadDataBtn = document.getElementById('uploadDataBtn');
const uploadModal = document.getElementById('uploadModal');
const uploadHeader = document.getElementById('uploadHeader');
const uploadArea = document.getElementById('uploadArea');
const uploadInput = document.getElementById('uploadInput');
const loadingState = document.getElementById('loadingState');
const errorMessage = document.getElementById('errorMessage');

let DATA_UPLOADED = false;

// Profile menu toggle
profileButton.addEventListener('click', () => {
    profileMenu.classList.toggle('hidden');
});

document.addEventListener('click', (e) => {
    if (!profileButton.contains(e.target) && !profileMenu.contains(e.target)) {
        profileMenu.classList.add('hidden');
    }
});

// Upload data button
uploadDataBtn.addEventListener('click', () => {
    profileMenu.classList.add('hidden');
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

// Upload area interactions
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

    const token = localStorage.getItem('authToken');

    loadingState.classList.add('show');
    uploadArea.style.display = 'none';
    uploadHeader.textContent = 'Processing Your Data';
    errorMessage.classList.remove('show');
    document.getElementById('closeModalBtn').classList.add('hidden');

    fetch(`${API_BASE_URL}/api/upload-data`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
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

//------------------------------------------------------------------------------
//Training plan generation
function generateTrainingPlan() {
    if (!DATA_UPLOADED) {
        alert('Please upload your data first to generate a training plan.');
        return;
    }

    const trainingPlanBox = document.getElementById('trainingPlanBox');
    const generatePlanBtn = document.getElementById('generatePlanBtn');
    const predictedFitnessSection = document.getElementById('predictedFitnessSection');

    // Show the training plan box and hide the button
    trainingPlanBox.classList.remove('hidden');
    predictedFitnessSection.style.display = 'block';
    generatePlanBtn.style.display = 'none';

    // Show loading state in the training plan box
    trainingPlanBox.innerHTML = `
        <div class="loading-container">
            <div class="spinner"></div>
            <h3>Generating Your Training Plan</h3>
            <p>This may take a minute as we analyze your data...</p>
        </div>
    `;

    const token = localStorage.getItem('authToken');

    fetch(`${API_BASE_URL}/api/training-plan`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        console.log('Response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Training Plan Response:', data);
        
        if (data.status === 'success') {
            const trainingPlan = data.response;
            console.log('Training Plan:', trainingPlan);
            displayTrainingPlan(trainingPlan, trainingPlanBox);
        } else {
            trainingPlanBox.innerHTML = '<p class="error">Failed to generate training plan. Please try again.</p>';
        }
    })
    .catch(error => {
        console.error('Error generating training plan:', error);
        trainingPlanBox.innerHTML = `<p class="error">Error: ${error.message}</p>`;
    })
    .finally(() => {
        generatePlanBtn.style.display = 'block';
    });
}

function displayTrainingPlan(plan, container) {

    const htmlPlan = markdownToHtml(plan);
    
    container.innerHTML = `
        <div class="training-plan-content">
            <h3>Your 30-Day Training Plan</h3>
            <div class="plan-text" id="planContent">
                ${htmlPlan}
            </div>
        </div>
    `;

    window.currentPlanText = plan;

    const generatePlanBtn = document.getElementById('generatePlanBtn');
    generatePlanBtn.textContent = 'Download PDF';
    generatePlanBtn.style.display = 'block';
    generatePlanBtn.onclick = function(e) {
        e.preventDefault();
        downloadPlanAsPDF(plan);
    };
}

function downloadPlanAsPDF() {
    if (typeof jsPDF === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
        script.onload = function() {
            generatePDFWithJsPDF();
        };
        document.head.appendChild(script);
    } else {
        generatePDFWithJsPDF();
    }
}

function generatePDFWithJsPDF() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4'
    });

    const planText = window.currentPlanText;
    const pageHeight = doc.internal.pageSize.getHeight();
    const pageWidth = doc.internal.pageSize.getWidth();
    const margin = 15;
    const maxWidth = pageWidth - (2 * margin);
    
    // Set font - use helvetica which is built-in to jsPDF
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(12);
    
    let yPosition = margin;
    const lineHeight = 6;
    const pageBottomMargin = 15;

    // Add title
    doc.setFontSize(18);
    doc.setFont('helvetica', 'bold');
    doc.text('Your 30-Day Training Plan Produced by Stryde', margin, yPosition);
    yPosition += 15;
    doc.setFontSize(12);
    doc.setFont('helvetica', 'normal');

    // Split text into lines and process
    const lines = planText.split('\n');

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];

        // Check for headers
        if (line.startsWith('## ')) {
            // Section header
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(14);
            line = line.replace('## ', '');
            yPosition += 5;
        } else if (line.startsWith('### ')) {
            // Sub header
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(13);
            line = line.replace('### ', '');
            yPosition += 3;
        } else if (line.startsWith('* ') || line.startsWith('- ')) {
            // Bullet point
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(11);
            
            // Handle indentation for nested bullets
            let indentLevel = 0;
            let tempLine = line;
            while (tempLine.startsWith('  ')) {
                indentLevel++;
                tempLine = tempLine.substring(2);
            }
            tempLine = tempLine.replace(/^[\*\-]\s+/, '');
            
            // Remove markdown formatting
            tempLine = tempLine.replace(/\*\*(.*?)\*\*/g, '$1');
            tempLine = tempLine.replace(/_([^_]+?)_/g, '$1');
            
            const bulletIndent = margin + (indentLevel * 5);
            const textWidth = maxWidth - (indentLevel * 5);
            
            // Wrap text
            const wrappedLines = doc.splitTextToSize(tempLine, textWidth);
            wrappedLines.forEach((wrappedLine, index) => {
                if (index === 0) {
                    doc.text('• ' + wrappedLine, bulletIndent, yPosition);
                } else {
                    doc.text(wrappedLine, bulletIndent + 5, yPosition);
                }
                yPosition += lineHeight;
                
                // Check if we need a new page
                if (yPosition > pageHeight - pageBottomMargin) {
                    doc.addPage();
                    yPosition = margin;
                }
            });
            continue;
        } else if (line.trim() === '') {
            // Empty line
            yPosition += 4;
        } else {
            // Regular text
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(11);
        }

        // Remove markdown formatting from regular text
        line = line.replace(/\*\*(.*?)\*\*/g, '$1');
        line = line.replace(/_([^_]+?)_/g, '$1');
        
        // Wrap text to fit page width
        const wrappedLines = doc.splitTextToSize(line, maxWidth);
        
        wrappedLines.forEach((wrappedLine) => {
            if (yPosition > pageHeight - pageBottomMargin) {
                doc.addPage();
                yPosition = margin;
            }
            
            doc.text(wrappedLine, margin, yPosition);
            yPosition += lineHeight;
        });

        // Reset font to normal
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(11);
    }

    // Save the PDF
    doc.save('Stryde-30-Day-Training-Plan.pdf');
}

function addFormattedText(doc, text, x, y, maxWidth, lineHeight) {
    // Process markdown formatting: **bold**, *italic*, etc.
    const parts = [];
    let lastIndex = 0;
    
    // Match **bold** and *italic*
    const boldRegex = /\*\*(.*?)\*\*/g;
    const italicRegex = /(?<!\*)\*(.*?)\*(?!\*)/g;
    
    let match;
    
    // Split by bold first
    const boldMatches = [...text.matchAll(boldRegex)];
    if (boldMatches.length > 0) {
        let currentIndex = 0;
        let currentY = y;
        let isFirstLine = true;
        
        for (let i = 0; i < text.length; ) {
            let boldMatch = boldMatches.find(m => m.index === i);
            
            if (boldMatch) {
                doc.setFont('helvetica', 'bold');
                doc.text(boldMatch[1], x, currentY);
                i += boldMatch[0].length;
            } else {
                // Find next bold or get to end
                let nextBoldIndex = boldMatches.filter(m => m.index > i).length > 0 
                    ? boldMatches.find(m => m.index > i).index 
                    : text.length;
                
                let chunk = text.substring(i, nextBoldIndex);
                doc.setFont('helvetica', 'normal');
                doc.text(chunk, x, currentY);
                i = nextBoldIndex;
            }
        }
    } else {
        doc.setFont('helvetica', 'normal');
        doc.text(text, x, y, { maxWidth: maxWidth });
    }
}


function markdownToHtml(markdown) {
    let html = markdown;
    
    // Split into lines to process list items correctly
    let lines = html.split('\n');
    let processedLines = [];
    let listStack = [0]; // Track nesting level
    
    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];
        
        // Check if line is a list item (starts with * or - followed by space)
        const listMatch = line.match(/^(\s*)([\*\-])\s+(.+)$/);
        
        if (listMatch) {
            let indent = listMatch[1].length;
            let content = listMatch[3];
            let currentLevel = Math.floor(indent / 2); // Each 2 spaces = 1 level
            let previousLevel = listStack[listStack.length - 1];
            
            // Close lists if we're decreasing indent
            while (previousLevel > currentLevel) {
                processedLines.push('</ul>');
                listStack.pop();
                previousLevel = listStack[listStack.length - 1];
            }
            
            // Open new lists if we're increasing indent
            while (previousLevel < currentLevel) {
                processedLines.push('<ul>');
                listStack.push(previousLevel + 1);
                previousLevel = currentLevel;
            }
            
            processedLines.push('<li>' + content + '</li>');
        } else {
            // Close any open lists if line is not a list item
            if (line.trim() !== '' && listStack.length > 1) {
                while (listStack.length > 1) {
                    processedLines.push('</ul>');
                    listStack.pop();
                }
            }
            
            if (line.trim() !== '') {
                processedLines.push(line);
            }
        }
    }
    
    // Close any remaining open lists
    while (listStack.length > 1) {
        processedLines.push('</ul>');
        listStack.pop();
    }
    
    html = processedLines.join('\n');
    
    // Now process other markdown elements
    
    // Headers (# ## ###) - must be done before italic processing
    html = html.replace(/^### (.*?)$/gm, '<h4>$1</h4>');
    html = html.replace(/^## (.*?)$/gm, '<h3>$1</h3>');
    html = html.replace(/^# (.*?)$/gm, '<h2>$1</h2>');
    
    // Bold (**text**) - must be before italic
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic (_text_ or *text* but not at line starts since those are lists)
    html = html.replace(/([^\s\*])\*([^\*\n]+?)\*([^\s\*])/g, '$1<em>$2</em>$3');
    html = html.replace(/_([^_\n]+?)_/g, '<em>$1</em>');
    
    // Horizontal rules (---)
    html = html.replace(/^---$/gm, '<hr>');
    
    // Paragraph breaks (double newlines)
    html = html.replace(/\n\n+/g, '</p><p>');
    html = '<p>' + html + '</p>';
    
    // Clean up empty paragraphs and unwanted wrapping
    html = html.replace(/<p><\/p>/g, '');
    html = html.replace(/<p><ul>/g, '<ul>');
    html = html.replace(/<\/ul><\/p>/g, '</ul>');
    html = html.replace(/<p><h/g, '<h');
    html = html.replace(/<\/h\d><\/p>/g, '</h\d>');
    html = html.replace(/<p><hr>/g, '<hr>');
    html = html.replace(/<\/hr><\/p>/g, '');
    
    return html;
}

// Tab switching
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
        predictedFitnessSection.style.display = 'none';
    }
}

function logout() {
    localStorage.removeItem('authToken');

    window.location.replace('/');

    window.history.pushState(null, null, '/');
    window.onpopstate = function() {
        window.history.pushState(null, null, '/');
    };
}

document.getElementById('logoutBtn').addEventListener('click', logout);