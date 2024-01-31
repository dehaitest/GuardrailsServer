let ws;
document.getElementById('uploadForm').addEventListener('submit', function(event) {
    event.preventDefault();
    uploadFile();
});

function uploadFile() {
    const input = document.getElementById('fileInput');
    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);

    fetch('/uploadfile', {
        method: 'POST',
        body: formData, 
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        document.getElementById('result').textContent = 'File uploaded successfully. Response: ' + JSON.stringify(data);
    })
    .catch(error => {
        console.error('Error uploading file:', error);
        document.getElementById('result').textContent = 'Error uploading file.';
    });
}

document.getElementById('connectButton').addEventListener('click', function() {
    const assistantId = document.getElementById('assistant_id').value || "";
    const threadId = document.getElementById('thread_id').value || "";
    const Instruction = document.getElementById('instruction').value || "";
    connectWebSocket(assistantId, threadId, Instruction);
});

document.getElementById('sendMessageButton').addEventListener('click', function() {
    const userMessage = document.getElementById('userMessage').value;
    sendMessage(userMessage);
});

function sendMessage(userMessage) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        const messageJson = JSON.stringify(userMessage);
        ws.send(messageJson);
        appendMessageToResult("You: " + userMessage);
    } else {
        console.error('WebSocket is not connected.');
        document.getElementById('MessageResult').innerHTML += `<p>Error: WebSocket is not connected.</p>`;
    }
    document.getElementById('userMessage').value = '';
}

function appendMessageToResult(message) {
    const messageDisplay = document.getElementById('MessageResult');
    messageDisplay.innerHTML += `<p>${message}</p>`;
}

// Updated WebSocket connection function to handle incoming messages
function connectWebSocket(assistantId, threadId, Instruction) {
    //ws = new WebSocket(`ws://localhost:8000/ws/guardrails?assistant_id=${assistantId}&thread_id=${threadId}&instruction=${Instruction}`);
    ws = new WebSocket(`ws://52.37.204.155/ws/guardrails?assistant_id=${assistantId}&thread_id=${threadId}&instruction=${Instruction}`);
    ws.onopen = function() {
        document.getElementById('websocketResult').textContent = 'Connected to WebSocket.';
    };
    ws.onerror = function(error) {
        console.error('WebSocket Error:', error);
        document.getElementById('websocketResult').textContent = 'Error connecting to WebSocket.';
    };
    ws.onmessage = function(e) {
        appendMessageToResult("Server: " + e.data);
    };
}

