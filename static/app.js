document.addEventListener('DOMContentLoaded', () => {
    // marked js config
    marked.setOptions({
        highlight: function(code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                try {
                    return hljs.highlight(code, {language: lang}).value;
                } catch (err) {
                    console.error('Highlight.js error:', err);
                }
            }
            return hljs.highlightAuto(code).value;
        },
        breaks: true,
        gfm: true,
        sanitize: false
    });

    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    // const form = document.getElementById('.chat-input-form');

    let history = [];
    let isStreaming = false;

    function applySyntaxHighlighting(element) {
        const codeBlocks = element.querySelectorAll('pre code');
        codeBlocks.forEach((block) => {
            hljs.highlightElement(block);
        });
    }

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
                messageDiv.innerHTML = ''; // Raw text for streaming
            } else {
                messageDiv.innerHTML = marked.parse(text);
                applySyntaxHighlighting(messageDiv);
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
            streamingDiv.textContent += content;
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    }

    // Finalize streaming message
    function finalizeStreamingMessage(fullContent) {
        const streamingDiv = document.getElementById('streaming-message');
        if (streamingDiv) {
            streamingDiv.innerHTML = marked.parse(fullContent);
            applySyntaxHighlighting(streamingDiv);
            streamingDiv.removeAttribute('id');
            console.log('msg complete')
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
        let buffer = '';

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
                buffer += chunk;
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; 

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const jsonStr = line.slice(6).trim();
                        if (jsonStr) {
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