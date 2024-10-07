# **Tech Enerzal Enterprise Assistant**

## Overview

**Tech Enerzal** is an AI-powered enterprise assistant designed to optimize business operations through advanced technologies, including **Natural Language Processing (NLP)**, **Retrieval-Augmented Generation (RAG)**, **Neo4j Aura**, and **MongoDB Atlas**. The system enhances document processing, HR management, IT automation, and data retrieval while providing a seamless, secure user experience via a responsive web interface.

For specific setup and implementation details, please refer to the **Frontend** and **Backend** README files in their respective directories.

---

## Key Features

### Backend:
- **AI-driven NLP and RAG** for real-time document retrieval and response generation.
- **Graph-based data** using **Neo4j Aura** for managing employee and department relationships.
- **Cloud storage** with **MongoDB Atlas** for scalable data management.
- **Automated document processing** for HR and IT services.

### Frontend:
- **Responsive user interface** built with HTML, CSS, and JavaScript.
- **Interactive Chatbot** for document submission and real-time queries.
- **Event management system** for browsing and registering for company events.
- **TOTP-based two-factor authentication** (2FA) for secure login.

---

## Project Structure

The project is split into **frontend** and **backend** modules for clear separation of concerns:

```bash
TechEnerzal/
│
├── Backend/          # Backend files for Flask, RAG, and database management.
│   ├── README.md     # Detailed backend instructions.
│
├── Frontend/         # Frontend files for web interface.
│   ├── README.md     # Detailed frontend instructions.
│
└── README.md         # This combined README file.
```

---

## Prerequisites

### Backend:
- Python 3.8+
- MongoDB Atlas and Neo4j Aura accounts
- FAISS for vector-based search

### Frontend:
- Node.js and npm (optional, most dependencies are CDN-based)
- A live server for local development

For detailed instructions on setting up the backend and frontend environments, see the respective **Backend** and **Frontend** README files.

---

## How to Set Up

### Backend Setup

1. **Clone the repository** and navigate to the `Backend` directory.
2. Set up a virtual environment and install the necessary dependencies.
3. Configure **MongoDB Atlas** and **Neo4j Aura** by updating connection strings in the respective Python scripts.
4. Run the Flask application.

For complete setup instructions, refer to `Backend/README.md`.

### Frontend Setup

1. **Clone the repository** and navigate to the `Frontend` directory.
2. Serve the frontend files using **Live Server** or any HTTP server for local development.

For more details, refer to `Frontend/README.md`.

---

## Key Technologies

- **Flask**: Backend API services.
- **Neo4j Aura**: Graph database for relationship management.
- **MongoDB Atlas**: NoSQL database for scalable storage.
- **FAISS**: Vector search for document retrieval.
- **HTML/CSS/JavaScript**: Frontend technologies for a responsive user interface.

---

## How It Works

### Backend:
- **RAG** handles information retrieval using FAISS vectors for efficient search.
- **NLP** interprets user queries and generates responses based on the retrieved content.
- **Graph relationships** in Neo4j enhance querying capabilities.

### Frontend:
- The **chat interface** allows users to upload documents and ask questions in real-time.
- **Event management** enables users to view and register for company events.
- **Secure login** through TOTP-based two-factor authentication.

For detailed explanations of each component, please refer to the **Backend** and **Frontend** README files.

---

## Future Enhancements

- **Backend**: Advanced IT support integration, hybrid search, and conversation summarization.
- **Frontend**: Dark mode, voice interaction, and progressive web app (PWA) support.

---

## Contact Information

For any questions or contributions, please contact **Tech Enerzal** at **techenerzal@gmail.com**.

---

This **README** provides an overview of the project. For detailed instructions and technical setups, refer to the **Backend/README.md** and **Frontend/README.md** files.

---
