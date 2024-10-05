/**
 * @fileoverview Handles chat interface interactions, including sending messages,
 * managing conversation history, handling file uploads, and communicating with
 * the backend API.
 * @version 1.1
 */

document.addEventListener('DOMContentLoaded', function() {
    /**
     * DOM Elements
     */
    const chatBubbles = document.querySelector('.chat-bubbles'); // Container for chat messages
    const initialBubbles = document.querySelector('.initial-bubbles'); // Initial chat bubbles
    const sendButton = document.getElementById('sendButton'); // Send button element
    const input = document.getElementById('userInput'); // User input field
    const logo = document.getElementById('logo'); // Logo element
    const fileUpload = document.getElementById('fileUpload'); // File upload input

    /**
     * Adds click event listeners to each initial chat bubble.
     * When a bubble is clicked, its associated message is sent.
     */
    document.querySelectorAll('.initial-bubbles .chat-bubble').forEach(bubble => {
        bubble.addEventListener('click', function() {
            const message = this.getAttribute('data-message');
            sendMessage(message);
        });
    });

    /**
     * Adds a click event listener to the send button.
     * When clicked, it sends the message from the input field if not empty.
     */
    sendButton.addEventListener('click', function() {
        const message = input.value.trim();
        if (message !== '') {
            sendMessage(message);
        }
    });

    /**
     * Adds a keydown event listener to the input field.
     * When the ENTER key is pressed, it sends the message if not empty.
     * @param {KeyboardEvent} event - The keyboard event triggered by the user.
     */
    input.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault(); // Prevent default new line in textarea
            const message = input.value.trim();
            if (message !== '') {
                sendMessage(message);
            }
        }
    });

    let conversationHistory = []; // Array to hold the chat history

    /**
     * Initial system message defining the assistant's role and guidelines.
     * Utilizes Markdown for response formatting.
     * @type {string}
     */
    const initialSystemMessage = `
    You are Enerzal, a friendly and intelligent chatbot developed by Tech Enerzal. Your primary role is to assist employees of Tech Enerzal by providing helpful, polite, and accurate information. You should always maintain a friendly and approachable tone while ensuring your responses are clear and informative. Your purpose is to assist with the following:

    1. **HR-Related Queries:** Help employees with questions regarding company policies, leave management, employee benefits, payroll, and other HR-related topics. Be empathetic and supportive, especially for sensitive topics like leave or benefits.

    2. **IT Support:** Provide guidance on common IT issues employees may encounter, such as troubleshooting technical problems, resetting passwords, or navigating company software. Be patient and provide step-by-step instructions for resolving technical issues.

    3. **Company Events & Updates:** Keep employees informed about upcoming company events, milestones, and internal updates. Share details about events in a friendly, enthusiastic tone to keep the company culture vibrant and engaging.

    4. **Document Summarization and Querying:** Enerzal also helps employees by summarizing documents (PDF, DOCX, TXT) and answering queries based on the content of uploaded documents. For document summaries, be concise and informative, extracting the key points while maintaining clarity. When answering queries, provide clear and accurate answers based on the document content, making sure to offer further assistance if needed.

    Guidelines to follow for every response:
    - Always maintain a positive and friendly tone.
    - Offer help proactively by suggesting next steps or additional resources.
    - Be concise but detailed enough to ensure the employee gets all the information they need.
    - When responding to questions or queries, prioritize clarity and accuracy.
    - If a question falls outside of your scope, politely guide the user to the appropriate department or suggest alternative ways they can find help.
    `
    // Use Markdown when generating responses

    // Add the system message to the conversation history
    conversationHistory.push({ role: "system", content: initialSystemMessage });

    /**
     * Prunes the conversation history to retain only the system message and the last three user/assistant interactions.
     */
    function pruneConversationHistory() {
        // Exclude the initial system message when pruning
        if (conversationHistory.length > 7) { // 1 system message + last 6 entries (3 interactions)
            conversationHistory = [conversationHistory[0], ...conversationHistory.slice(-6)];
        }
    }

    /**
     * Sends a message from the user to the assistant and handles the response.
     * @param {string} message - The message input by the user.
     */
    async function sendMessage(message) {
        if (message) {
            // Remove initial bubbles and logo after the first message is sent
            if (initialBubbles) {
                initialBubbles.remove();
            }
            if (logo) {
                logo.remove();
            }

            // Create user message bubble
            const userBubble = document.createElement('div');
            userBubble.className = 'chat-bubble chat-bubble-user shadow-sm';
            userBubble.innerHTML = `<p>${message}</p>`;
            chatBubbles.appendChild(userBubble);

            // Add the user's message to the conversation history
            conversationHistory.push({ role: "user", content: message });

            // Prune conversation history to retain only last 3 messages plus system prompt
            pruneConversationHistory();

            // Clear input and disable it while waiting for response
            input.value = '';
            input.disabled = true; // Disable input while waiting for response
            chatBubbles.scrollTop = chatBubbles.scrollHeight; // Scroll to bottom

            try {
                // Fetch the response from the Flask backend
                const response = await fetch("http://localhost:5000/api/chat", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        messages: conversationHistory // Send conversation history only
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }

                // Parse the JSON response
                const responseData = await response.json();

                // Extract the assistant's message
                let assistantMessage = '';

                if (responseData.content) {
                    assistantMessage = responseData.content;
                } else if (responseData.error) {
                    assistantMessage = `Error: ${responseData.error}`;
                } else {
                    assistantMessage = 'Sorry, I did not understand that.';
                }

                // Create assistant response bubble (empty initially)
                const assistantBubble = document.createElement('div');
                assistantBubble.className = 'chat-bubble chat-bubble-assistant shadow-sm';
                chatBubbles.appendChild(assistantBubble);

                // Use typing animation to display the assistant's message
                await typeAssistantMessage(assistantBubble, assistantMessage);

                // Add the assistant's message to the conversation history
                conversationHistory.push({ role: "assistant", content: assistantMessage });

            } catch (error) {
                console.error("Error:", error);
                // Display error message to user
                const assistantBubble = document.createElement('div');
                assistantBubble.className = 'chat-bubble chat-bubble-assistant shadow-sm';
                assistantBubble.innerHTML = `<p>Sorry, I encountered an error. Please try again later.</p>`;
                chatBubbles.appendChild(assistantBubble);
            }

            // Re-enable input
            input.disabled = false;
            chatBubbles.scrollTop = chatBubbles.scrollHeight; // Scroll to bottom
        }
    }

    /**
     * Types out the assistant's message with a typing animation.
     * @param {HTMLElement} element - The DOM element where the message will be displayed.
     * @param {string} message - The message to type out.
     */
    async function typeAssistantMessage(element, message) {
        const typingSpeed = 20; // Time in milliseconds between each character
        let index = 0;
        let displayedMessage = '';

        return new Promise((resolve) => {
            function typeCharacter() {
                if (index < message.length) {
                    displayedMessage += message.charAt(index);
                    // Use marked.js to convert Markdown to HTML
                    const assistantMessageHTML = marked.parse(displayedMessage);
                    // Update the assistant bubble with the parsed content
                    element.innerHTML = `<p>${assistantMessageHTML}</p>`;
                    index++;
                    chatBubbles.scrollTop = chatBubbles.scrollHeight; // Scroll to bottom
                    setTimeout(typeCharacter, typingSpeed);
                } else {
                    resolve();
                }
            }
            typeCharacter();
        });
    }

    /**
     * Handles file uploads to allow users to send documents to the assistant.
     */
    fileUpload.addEventListener('change', async function(event) {
        const file = event.target.files[0];
        if (file) {
            // Disable input while processing the file
            input.disabled = true;

            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('http://localhost:5000/api/upload', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                if (result.content) {
                    const fileName = file.name; // Get the file name
                    const content = result.content;
                    console.log("Uploaded file content:", content);

                    // Add the explanation and file name to the system prompt (this is for the model, not shown to the user)
                    const systemMessage = `
                        The user has uploaded a document named "${fileName}". The contents of this file should be considered to assist in generating responses.
                        Here is the content of the file parsed in text format:
                        ${content}
                    `;

                    // Add this system message to the conversation history, but do not display it to the user
                    conversationHistory.push({ role: "system", content: systemMessage });
                    console.log(conversationHistory);

                    // Notify user that the file is uploaded successfully
                    const fileSuccessBubble = document.createElement('div');
                    fileSuccessBubble.className = 'chat-bubble chat-bubble-system shadow-sm';
                    fileSuccessBubble.innerHTML = `<p>File <b>"${fileName}"</b> uploaded successfully and ready to be used.</p>`;
                    chatBubbles.appendChild(fileSuccessBubble);

                    // Re-enable input for further queries
                    input.disabled = false;

                } else {
                    throw new Error('Failed to process the file.');
                }

            } catch (error) {
                console.error("Error uploading file:", error);
                // Display error message to user
                const errorBubble = document.createElement('div');
                errorBubble.className = 'chat-bubble chat-bubble-system shadow-sm';
                errorBubble.innerHTML = `<p>Sorry, there was an issue with the file upload.</p>`;
                chatBubbles.appendChild(errorBubble);
                input.disabled = false; // Re-enable input
            }
            chatBubbles.scrollTop = chatBubbles.scrollHeight; // Scroll to bottom
        }
    });
});
