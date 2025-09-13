document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    // const form = document.getElementById('.chat-input-form');

    let history = [];
    let isStreaming = false;

    // Adding messages to chat box
    function addMessage(text, sender, isStreaming = false) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        if (sender === 'user') {
            messageDiv.classList.add('user-message');
            messageDiv.innerHTML = marked.parse(text);
        } else {
            messageDiv.classList.add('bot-message');
            if (isStreaming) {
                messageDiv.id = 'streaming-message';
                messageDiv.innerHTML = marked.parse(text); // Raw text for streaming
            } else {
                messageDiv.innerHTML = marked.parse(text);
            }
        }
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
        return messageDiv;
    }

    // Update streaming message
    function updateStreamingMessage(content) {
        const streamingDiv = document.getElementById('streaming-message');
        if (streamingDiv) {
            streamingDiv.innerHTML += content;
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    }

    // Finalize streaming message
    function finalizeStreamingMessage(fullContent) {
        const streamingDiv = document.getElementById('streaming-message');
        if (streamingDiv) {
            streamingDiv.innerHTML = marked.parse(fullContent);
            streamingDiv.removeAttribute('id');
        }
    }

    // Function to send a message to backend
    async function sendMessage() {
        const message = userInput.value.trim();
        const modelSelect = document.getElementById('model-select');
        const selectedModel = modelSelect.value;

        if (!message || isStreaming) return;

        // Add user message to the chatbox
        addMessage(message, 'user');
        userInput.value = ''; // Clear the input field

        // Disable send button and input during streaming
        isStreaming = true;
        sendBtn.disabled = true;
        sendBtn.textContent = 'Sending...';
        userInput.disabled = true;

        // Add empty bot message for streaming
        addMessage('', 'bot', true);
        let fullResponse = '';

        try {
            const apiUrl = `/api/chat/${selectedModel}`;

            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message, history: history }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            if (data.type === 'chunk') {
                                fullResponse += data.content;
                                updateStreamingMessage(data.content);
                            } else if (data.type === 'end') {
                                finalizeStreamingMessage(fullResponse);
                                history = data.history;
                            } else if (data.type === 'error') {
                                finalizeStreamingMessage(`Error: ${data.content}`);
                            }
                        } catch (e) {
                            console.error('Error parsing JSON:', e);
                        }
                    }
                }
            }

        } catch (error) {
            console.error('Streaming error:', error);
            finalizeStreamingMessage('Sorry, something went wrong. Please try again later.');
        } finally {
            // Re-enable send button and input
            isStreaming = false;
            sendBtn.disabled = false;
            sendBtn.textContent = 'Send';
            userInput.disabled = false;
            userInput.focus();
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !isStreaming) {
            event.preventDefault(); // Prevents a newline from being added
            sendMessage();
        }
    });
});