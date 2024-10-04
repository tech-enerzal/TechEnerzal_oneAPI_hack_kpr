const wrapper = document.querySelector('.wrapper')
const registerLink = document.querySelector('.register-link')
const loginLink = document.querySelector('.login-link')

registerLink.onclick = () => {
    wrapper.classList.add('active')
}

loginLink.onclick = () => {
    wrapper.classList.remove('active')
}

// Login Form
const loginForm = document.getElementById('login-form')

loginForm.onsubmit = async (e) => {
    e.preventDefault()

    const email = document.getElementById('email').value
    const password = document.getElementById('password').value
    const totp = document.getElementById('totp').value

    const data = { email, password, token: totp }

    try {
        const response = await fetch('http://localhost:5000/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })

        const result = await response.json()

        if (response.ok) {
            localStorage.setItem('token', result.token)
            window.location.href = '/pages/chat.html'  // Redirect after successful login
        } else {
            alert(result.msg || 'Login failed.')
        }
    } catch (error) {
        console.error('Error:', error)
        alert('Login failed.')
    }
}

// Signup Form
const signupForm = document.getElementById('signup-form')

signupForm.onsubmit = async (e) => {
    e.preventDefault();

    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;

    // Ensure both fields have values
    if (!email || !password) {
        alert('Please provide both email and password.');
        return;
    }

    const data = { email, password };

    try {
        const response = await fetch('http://localhost:5000/api/auth/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)  // Send data as JSON
        });

        const result = await response.json();  // Parse the JSON response

        if (response.ok) {
            alert(result.msg);  // Show success message
            const newWindow = window.open("", "_blank", "width=400,height=400");  // Opens a new window
            newWindow.document.write(`<html><head><title>Scan QR Code for TOTP</title></head>`);
            newWindow.document.write(`<body style="text-align:center;"><h3>Scan this QR Code for TOTP</h3>`);
            newWindow.document.write(`<img src="data:image/png;base64,${result.qrcode}" alt="QR Code" style="width: 200px; height: 200px;">`);
            newWindow.document.write(`</body></html>`);
        } else {
            alert(result.msg || 'Signup failed.');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during signup.');
    }
};

