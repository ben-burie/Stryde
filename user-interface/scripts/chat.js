// Chat functionality
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
        
        // Display user message
        const userMsg = document.createElement('div');
        userMsg.className = 'message user';
        userMsg.textContent = message;
        chatMessages.appendChild(userMsg);
        input.value = '';
        input.focus();
        
        // Display loading message while waiting for response
        const loadingMsg = document.createElement('div');
        loadingMsg.className = 'message coach loading';
        loadingMsg.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
        chatMessages.appendChild(loadingMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Get response from API
        getResponse(message).then(response => {
            // Remove loading message
            chatMessages.removeChild(loadingMsg);
            
            // Display coach response
            const botMsg = document.createElement('div');
            botMsg.className = 'message coach';
            botMsg.textContent = response;
            chatMessages.appendChild(botMsg);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }).catch(error => {
            // Remove loading message
            chatMessages.removeChild(loadingMsg);
            
            // Display error message
            const errorMsg = document.createElement('div');
            errorMsg.className = 'message coach error';
            errorMsg.textContent = 'Error: ' + error.message;
            chatMessages.appendChild(errorMsg);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        });
    }
}

function getResponse(message) {
    const token = localStorage.getItem('authToken');
    
    return fetch(`${API_BASE_URL}/api/chat-response`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            message: message
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Chat Response:', data);
        
        if (data.status === 'success') {
            return data.response;
        } else {
            throw new Error(data.message || 'Failed to get response');
        }
    })
    .catch(error => {
        console.error('Error getting chat response:', error);
        throw error;
    });
}