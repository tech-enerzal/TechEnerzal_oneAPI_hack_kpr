# **Tech Enerzal Frontend**  

---

## **Overview**

The **Tech Enerzal Frontend** is a responsive web interface designed for seamless user interaction with an AI-powered chatbot, event management system, and other enterprise services. This frontend integrates with the **backend**, allowing users to interact with the chatbot, manage their accounts, explore features, check pricing, and register for upcoming events.

---

## **Key Features**

- **Responsive Design**: Built with **HTML**, **CSS**, and **Bootstrap** for cross-device compatibility.
- **Interactive Chatbot Interface**: Users can chat with the AI-powered assistant and upload documents for processing.
- **Event Management**: Users can browse, search, and register for company events.
- **2FA Integration**: Supports TOTP-based two-factor authentication on the login page.
- **Clean Navigation**: Intuitive and clean navigation throughout the pages for a smooth user experience.

---

## **Table of Contents**

1. [Prerequisites](#prerequisites)
2. [Project Structure](#project-structure)
3. [How to Set Up the Frontend](#how-to-set-up-the-frontend)
4. [What is Implemented](#what-is-implemented)
5. [How it Works](#how-it-works)
6. [Future Enhancements](#future-enhancements)
7. [Contact Information](#contact-information)

---

## **Prerequisites**

Before you start, ensure you have the following:

- **Node.js** and **npm** (for managing frontend dependencies).
- **Live Server** or **Apache** (optional, for serving HTML locally during development).

---

## **Project Structure**

Here is an overview of the **Frontend** file structure:

```bash
Frontend/
│
├── assets/                     # Contains images and media used in the frontend
│   ├── Dashboard.png
│   ├── ENERZAL_LOGO.jpg
│   ├── enerzal.jpg
│   ├── Loading.gif
│   └── logo.jpg
│
├── css/                        # All stylesheets used in the frontend
│   ├── about-style.css
│   ├── chat-styles.css
│   ├── contact-style.css
│   ├── features-styles.css
│   ├── login-style.css
│   ├── pricing-styles.css
│   └── styles.css              # Global stylesheet for consistency across all pages
│
├── js/                         # JavaScript files for frontend logic
│   ├── chat.js                 # Manages the chat interface and interactions
│   └── login.js                # Handles login and two-factor authentication (TOTP)
│
├── pages/                      # Contains the main HTML files for the website
│   ├── about.html
│   ├── chat.html
│   ├── contact.html
│   ├── events.html
│   ├── features.html
│   ├── login.html
│   └── pricing.html
│
├── index.html                  # Homepage for Enerzal
└── Readme.md                   # The README you're reading
```

---

## **How to Set Up the Frontend**

### **1. Clone the Repository**

Start by cloning the repository to your local machine:

```bash
git clone <your-repo-url>
cd Frontend
```

### **2. Install Dependencies**

Make sure you have **Node.js** and **npm** installed. Although most dependencies for the frontend are handled via CDN (like Bootstrap), you can install any additional required dependencies using **npm**:

```bash
npm install
```

### **3. Serve the Files Locally**

You can use a live server (such as the **Live Server** extension in VS Code or any web server) to run the frontend locally. If using **Live Server**:

- Right-click on `index.html` and select **"Open with Live Server"** in VS Code.

Alternatively, you can serve the files using **Python**’s simple HTTP server:

```bash
# In the project directory
python -m http.server 8000
```

Now, visit `http://localhost:8000` to view the website.

---

## **What is Implemented**

### **1. Responsive HTML Pages**

- **Home (`index.html`)**: Introductory page with a call to action for users to get started with **Enerzal**.
- **About Us (`about.html`)**: Highlights the mission, vision, and team behind **Enerzal**.
- **Chat Interface (`chat.html`)**: Provides a real-time chat interface for users to interact with the AI assistant and upload documents.
- **Contact Us (`contact.html`)**: A form that allows users to contact the team with their queries.
- **Event Management (`events.html`)**: Lists company events and allows users to register or search for specific events.
- **Features (`features.html`)**: Showcases the primary features of the **Enerzal** platform, including AI-driven chatbot capabilities.
- **Pricing (`pricing.html`)**: Contains pricing plans for users and an option to set up a meeting to discuss enterprise solutions.
- **Login (`login.html`)**: Handles user login, including **two-factor authentication (TOTP)**.

### **2. CSS Files**

- **Global Styles (`styles.css`)**: Defines common styling elements like fonts, colors, and layout used across all pages.
- **Page-Specific Styles**: Each page (e.g., **about**, **chat**, **contact**, **login**) has its own dedicated stylesheet to control specific design aspects.

### **3. JavaScript Functionality**

- **Chat Logic (`chat.js`)**: Manages the chat interface where users can send messages, upload files, and receive responses from the backend API.
- **Login Script (`login.js`)**: Handles form validation, login authentication, and two-factor authentication using **TOTP**.

---

## **How It Works**

1. **Homepage (`index.html`)**:
   - Users are greeted with a clean and modern interface.
   - A **Get Started** button leads to the **Login** page.

2. **Chat Interface (`chat.html`)**:
   - The chat window provides real-time interaction with the AI assistant.
   - Users can type queries, send messages, and upload files like PDFs or DOCX documents for processing.
   - Backend APIs (not covered here) power the responses received by users.

3. **Login Page (`login.html`)**:
   - Users enter their **username** and **password**.
   - **Two-factor authentication** is handled via TOTP codes, making the login process more secure.
   - A **QR Code** is displayed for scanning and setting up TOTP on first login.

4. **Event Management (`events.html`)**:
   - Lists company events with options to register or search for specific events.
   - Each event is accompanied by a date, description, and registration link.

5. **Other Pages (`about.html`, `pricing.html`, etc.)**:
   - These pages provide additional information about **Enerzal**, its features, pricing plans, and contact details.
   - Each page is linked via the navigation bar for easy access.

---

## **Future Enhancements**

- **Dark Mode**: Adding a dark mode toggle to improve user experience.
- **Chatbot Improvements**: Enhancing the chatbot interface to include voice interaction.
- **Localization**: Adding support for multiple languages to serve a global audience.
- **Progressive Web App (PWA)**: Converting the frontend into a PWA for offline access and native app-like experience.
  
---

## **Contact Information**

For any questions or contributions, please contact **Tech Enerzal** at **<techenerzal@gmail.com>**.

---

This **README.md** is designed to be comprehensive and informative, covering all aspects of the **Tech Enerzal Frontend**. It guides users on how to set up, what is implemented, and how everything works together.
