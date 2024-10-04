/**
 * @fileoverview Manages user authentication interactions, including login and signup processes.
 * Handles UI transitions between login and registration forms, submits authentication requests
 * to the backend API, and manages responses such as token storage and QR code display for TOTP.
 * @version 1.0
 */

/**
 * Selects the main wrapper element that contains both login and registration forms.
 * @type {HTMLElement}
 */
const wrapper = document.querySelector('.wrapper');

/**
 * Selects the link element that triggers the registration form display.
 * @type {HTMLElement}
 */
const registerLink = document.querySelector('.register-link');

/**
 * Selects the link element that triggers the login form display.
 * @type {HTMLElement}
 */
const loginLink = document.querySelector('.login-link');

/**
 * Event handler for the registration link click.
 * Adds the 'active' class to the wrapper to display the registration form.
 */
registerLink.onclick = () => {
    wrapper.classList.add('active');
};

/**
 * Event handler for the login link click.
 * Removes the 'active' class from the wrapper to display the login form.
 */
loginLink.onclick = () => {
    wrapper.classList.remove('active');
};

/**
 * Selects the login form element by its ID.
 * @type {HTMLFormElement}
 */
const loginForm = document.getElementById('login-form');

const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const totpInput = document.getElementById('totp');

/**
 * Event handler for the login form submission.
 * Prevents the default form submission, collects user input, sends a POST request to the login API,
 * handles the response by storing the token and redirecting on success, or alerting the user on failure.
 * @param {Event} e - The form submission event.
 */
loginForm.addEventListener('submit', async function(event) {
    event.preventDefault();

    const email = emailInput.value.trim();
    const password = passwordInput.value.trim();
    const totp = totpInput.value.trim();

    try {
        const response = await fetch('http://localhost:5000/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email, password: password, token: totp })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.msg || `HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        if (data.token) {
            // Store the token in localStorage
            localStorage.setItem('token', data.token);
            console.log('Login successful. Token stored.');

            // Optionally redirect to the chat page or show the chat interface
            window.location.href = '/pages/chat.html';
        } else {
            console.error('Login failed:', data.msg);
            alert('Login failed: ' + data.msg);
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Login error: ' + error.message);
    }
});

/**
 * Selects the signup form element by its ID.
 * @type {HTMLFormElement}
 */
const signupForm = document.getElementById('signup-form');

/**
 * Event handler for the signup form submission.
 * Prevents the default form submission, validates user input, sends a POST request to the signup API,
 * handles the response by displaying a QR code for TOTP setup on success, or alerting the user on failure.
 * @param {Event} e - The form submission event.
 */
signupForm.onsubmit = async (e) => {
    e.preventDefault(); // Prevent the default form submission behavior

    // Retrieve user input values from the form fields
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;

    // Ensure both email and password fields have values
    if (!email || !password) {
        alert('Please provide both email and password.');
        return;
    }

    // Construct the data object to be sent in the POST request
    const data = { email, password };

    try {
        // Send a POST request to the signup API endpoint with the user credentials
        const response = await fetch('http://localhost:5000/api/auth/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)  // Convert the data object to a JSON string
        });

        // Parse the JSON response from the server
        const result = await response.json();  // Parse the JSON response

        if (response.ok) {
            // If the response is successful, alert the user with the success message
            alert(result.msg);
            // Open a new window to display the QR code for TOTP setup
            const newWindow = window.open("", "_blank", "width=400,height=400");
            newWindow.document.write(`<html><head><title>Scan QR Code for TOTP</title></head>`);
            newWindow.document.write(`<body style="text-align:center;"><h3>Scan this QR Code for TOTP</h3>`);
            newWindow.document.write(`<img src="data:image/png;base64,${result.qrcode}" alt="QR Code" style="width: 200px; height: 200px;">`);
            newWindow.document.write(`</body></html>`);
        } else {
            // If the response is not successful, alert the user with the received message or a default message
            alert(result.msg || 'Signup failed.');
        }
    } catch (error) {
        // Log any errors to the console and alert the user of the failure
        console.error('Error:', error);
        alert('An error occurred during signup.');
    }
};
