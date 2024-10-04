document.addEventListener('DOMContentLoaded', function() {
    const chatBubbles = document.querySelector('.chat-bubbles');
    const initialBubbles = document.querySelector('.initial-bubbles');
    const sendButton = document.getElementById('sendButton');
    const input = document.getElementById('userInput');
    const logo = document.getElementById('logo');
    const fileUpload = document.getElementById('fileUpload'); // For file upload

    // Handle click on initial chat bubbles
    document.querySelectorAll('.initial-bubbles .chat-bubble').forEach(bubble => {
        bubble.addEventListener('click', function() {
            const message = this.getAttribute('data-message');
            sendMessage(message);
        });
    });

    // Handle send button click
    sendButton.addEventListener('click', function() {
        const message = input.value.trim();
        if (message !== '') {
            sendMessage(message);
        }
    });

    // Handle ENTER key press
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
    
 // Add the initial system message
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
- Always be empathetic and understanding, especially when dealing with sensitive HR or IT issues.

Remember, your goal is to make every employee interaction positive and helpful, ensuring that they feel supported by Tech Enerzal.
`
// #- Use Markdown when generating responses

 // Add the system message to the conversation history
 conversationHistory.push({ role: "system", content: initialSystemMessage });

 // Function to prune conversation history to last 3 user/assistant interactions, excluding the system message
function pruneConversationHistory() {
    // Exclude the initial system message when pruning
    if (conversationHistory.length > 4) { // 1 system message + last 3 entries
        conversationHistory = [conversationHistory[0], ...conversationHistory.slice(-3)];
    }
}

    async function sendMessage(message) {
        if (message) {
            // Remove initial bubbles and logo
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

            // Clear input and disable it
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

                // Create assistant response bubble (empty initially)
                const assistantBubble = document.createElement('div');
                assistantBubble.className = 'chat-bubble chat-bubble-assistant shadow-sm';
                chatBubbles.appendChild(assistantBubble);

                // Read and process the streamed response
                const reader = response.body.getReader();
                let decoder = new TextDecoder();
                let assistantMessage = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break; // Stream finished

                    // Decode the chunk
                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\n'); // Split on newline characters

                    lines.forEach(line => {
                        if (line) {
                            // Append the line to the assistant message
                            assistantMessage += line;

                            // Use marked.js to convert Markdown to HTML
                            const assistantMessageHTML = marked.parse(assistantMessage);

                            // Update the assistant bubble with the parsed content
                            assistantBubble.innerHTML = `<p>${assistantMessageHTML}</p>`;
                        }
                    });

                    chatBubbles.scrollTop = chatBubbles.scrollHeight; // Scroll to bottom as content comes in
                }

                // Final conversion of the full assistant message once streaming is done
                const finalAssistantMessageHTML = marked.parse(assistantMessage);
                assistantBubble.innerHTML = `<p>${finalAssistantMessageHTML}</p>`;

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

    // Handle file upload
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
                        Here is the content of the file parse in text format:
                        ${content}
                    `;

                    // Add this system message to the conversation history, but do not display it to the user
                    conversationHistory.push({ role: "system", content: systemMessage });
                    console.log(conversationHistory)

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
