# **Tech Enerzal Enterprise Assistant**  

---

## **Overview**

Tech Enerzal is a state-of-the-art enterprise assistant designed to streamline business operations using **cutting-edge AI** technologies like **Natural Language Processing (NLP)**, **Retrieval-Augmented Generation (RAG)**, **Neo4j Aura** for graph-based relationships, and **MongoDB Atlas** for scalable database management. This solution optimizes document processing, IT automation, and HR support while ensuring top-tier security with local infrastructure and cloud-based vector retrieval.

Tech Enerzal is designed to reduce operational costs by 30% and eliminate dependencies on third-party APIs, offering a fully open-source, independent, and scalable solution for modern enterprises.

---

## **Key Features**

- **AI-powered NLP for Dynamic Responses**: Uses advanced NLP techniques to process and understand user queries in real-time.
- **Graph-based Knowledge Integration (Neo4j)**: Leverages Neo4j Aura to represent relationships between employees, departments, and policies for enhanced data insights.
- **Document Summarization & Retrieval**: Automates document uploads and processes them for key information extraction.
- **IT & HR Automation**: Handles IT ticket generation and HR policy updates dynamically using RAG and automated scraping.
- **Cloud-Enabled & Secure**: Seamlessly integrates **MongoDB Atlas** for scalable, cloud-based storage and **Neo4j Aura** for managing graph-based relationships, with secure access.
- **Cost-Efficient**: Built on open-source technology, minimizing operational costs.

---

## **Table of Contents**

1. [Prerequisites](#prerequisites)
2. [Project Structure](#project-structure)
3. [How to Set Up the Backend](#how-to-set-up-the-backend)
4. [What is Being Implemented](#what-is-being-implemented)
5. [How it is Implemented](#how-it-is-implemented)
6. [Neo4j Aura and MongoDB Atlas Setup](#neo4j-aura-and-mongodb-atlas-setup)
7. [How to Use the Application](#how-to-use-the-application)
8. [Future Enhancements](#future-enhancements)
9. [Contact Information](#contact-information)

---

## **Prerequisites**

Before setting up the project, ensure you have the following installed:

- **Python 3.8+**
- **MongoDB Atlas** account for cloud-based document storage.
- **Neo4j Aura** account for cloud-based graph database management.
- **FAISS** (for vector-based search) - CPU or GPU version.
- **Virtual Environment** (recommended for managing dependencies).

---

## **Project Structure**

The project follows a modular structure designed to make the system scalable, secure, and easy to manage:

Backend/
│   ├── _pycache_/                      # Python cache for compiled bytecode files
│   │    ├── RAG.cpython-311.pyc          # Compiled RAG file (Python 3.11)
│   │    ├── RAG.cpython-312.pyc          # Compiled RAG file (Python 3.12)
│
│   ├── Backend/
│       ├── Database/
│           ├── Company-Event/
│               ├── Events-2024-10.json   # JSON file storing company events data for the year 2024
│
│   ├── Database/
│       ├── HR/
│           ├── Vector/                   # Folder for FAISS vector databases related to HR
│               ├── Full_HR/              # Full HR-related FAISS index and pickle files
│                   ├── index.faiss       # FAISS index for the entire HR data
│                   ├── index.pkl         # Pickle file containing vectors or metadata
│               ├── QA_HR/                # FAISS index for HR Q&A or quick retrieval system
│                   ├── index.faiss       # FAISS index for HR-related queries
│                   ├── index.pkl         # Pickle file containing vectors for quick HR Q&A
│
│       ├── HR Policy Manual 2023 IIMA_compressed.pdf   # Compressed PDF for the HR policy manual
│       ├── hr-policy-final.json               # Final version of HR policy in JSON format
│
│   ├── Mongo_Emp_Dasboard_setup.py        # Script to set up the MongoDB employee dashboard
│   ├── vectord-db.ipynb                   # Jupyter notebook to set up the FAISS vector database
│
│   ├── Temp/                              # Temporary directory for testing or drafts
│       ├── Readme.md                      # Readme file for instructions
│       ├── Test1.txt                      # Test document for system overview
│       ├── Backend_Flask.py               # Flask backend script
│       ├── Procfile                       # Heroku Procfile for deployment
│       ├── RAG.py                         # Main RAG system implementation
│       ├── Rag2.py                        # Additional RAG-related code or extensions
│
│   ├── Requirements.txt                   # File containing Python dependencies required for the project

---

## **How to Set Up the Backend**

### **Step 1: Clone the Repository**

First, clone the repository to your local machine:

```bash
git clone <your-repo-url>
cd <your-repo-directory>
```

### **Step 2: Set Up a Virtual Environment**

It is recommended to use a virtual environment to manage dependencies. Create and activate one:

```bash
# Create virtual environment
python -m venv env

# Activate the environment
source env/bin/activate   # For Windows: env\Scripts\activate
```

### **Step 3: Install Dependencies**

Install the required Python libraries and dependencies:

```bash
pip install -r Requirements.txt
```

Key dependencies include:

- **Flask** for backend API services.
- **FAISS** for vector search and retrieval (install CPU or GPU version as per your hardware).
- **bcrypt**, **pyotp**, **qrcode** for secure 2FA.
- **PyPDF2**, **python-docx** for document processing.
- **langchain-community** for NLP-based tasks.

### **Step 4: Set Up MongoDB Atlas**

MongoDB Atlas is used for cloud-based, scalable storage of employee data, events, and HR policies. Follow these steps:

1. Create an account on **[MongoDB Atlas](https://www.mongodb.com/cloud/atlas)**.
2. Set up a new cluster and create a database.
3. Get the **connection string** for your database.
4. Update the connection string in the project’s MongoDB configuration (`Mongo_Emp_Dasboard_setup.py`).

```python
# Example MongoDB connection string setup
client = pymongo.MongoClient("<Your MongoDB Atlas Connection String>")
```

### **Step 5: Set Up Neo4j Aura**

Neo4j Aura is used for managing graph-based relationships between employees, departments, and policies. Here’s how to set it up:

1. Create an account on **[Neo4j Aura](https://neo4j.com/cloud/aura/)**.
2. Create a new project and note down your **Bolt URL**, **Username**, and **Password**.
3. Update these details in the `Neo4j_setup.py` script to establish the connection:

```python
from neo4j import GraphDatabase

# Replace these with your Neo4j Aura details
uri = "neo4j+s://<Your Aura Bolt URL>"
username = "<Your Username>"
password = "<Your Password>"

driver = GraphDatabase.driver(uri, auth=(username, password))
```

Run the `Neo4j_setup.py` to populate the initial graph with employee and department data:

```bash
python Neo4j_setup.py
```

### **Step 6: Run the Backend**

Finally, run the Flask backend to serve the APIs:

```bash
export FLASK_APP=Backend_Flask.py  # For Windows: set FLASK_APP=Backend_Flask.py
flask run
```

Access the application at `http://127.0.0.1:5000`.

---

## **What is Being Implemented**

The **Tech Enerzal Enterprise Assistant** is designed to provide a comprehensive and scalable solution for enterprise automation, leveraging both structured and unstructured data. Key functionalities include:

1. **Document Processing**: Summarizes and retrieves important data from uploaded documents (PDF, DOCX).
2. **NLP and RAG for Query Handling**: Uses advanced NLP models to understand user queries and retrieve relevant information using **FAISS**.
3. **Graph Database Integration**: **Neo4j Aura** is utilized to create and manage relationships between employees, departments, and policies.
4. **Cloud-based Storage**: Uses **MongoDB Atlas** to store and manage employee data, events, and policy documents in a scalable cloud-based solution.

---

## **How it is Implemented**

The project integrates several advanced technologies to provide seamless, real-time, and secure enterprise automation.

### **1. Flask Backend**

Flask handles the API services and user interaction. It serves as the interface for uploading documents, retrieving HR policies, and processing user queries through **RAG**.

### **2. Retrieval-Augmented Generation (RAG)**

- **Retrieval**: The FAISS system retrieves relevant documents based on vector similarity.
- **Generation**: The NLP model (using **sentence-transformers**) generates detailed responses based on the retrieved content.

### **3. FAISS for Vector Search**

FAISS handles vector-based similarity searches for fast and efficient document retrieval. Embeddings are stored in FAISS indexes (`Full_HR/index.faiss` and `QA_HR/index.faiss`).

### **4. Neo4j Aura for Graph Relationships**

Neo4j Aura manages relationships between entities such as employees, departments, and HR policies. This allows for more complex queries and understanding of how entities interact within the organization.

### **5. MongoDB Atlas for Scalable Storage**

MongoDB Atlas stores structured data such as employee details, event data, and HR policies, making it easy to scale the database as more information is added.

---

## **Neo4j Aura and MongoDB Atlas Setup**

### **Neo4j Aura**

- **Purpose**: Graph database to manage complex relationships between employees, departments, and policies.
- **Usage**: Enhances the querying process by leveraging graph-based queries to understand relational data better.

### **MongoDB Atlas**

- **Purpose**: Cloud-based NoSQL database to store scalable employee and HR policy data.
- **Usage**:

 Provides a robust, cloud-native storage solution for unstructured data that grows with the organization.

---

## **How to Use the Application**

1. **Upload a Document**:
   - Navigate to `/upload` and upload your document (PDF, DOCX).
   - The document will be processed, summarized, and stored in the vector database for future queries.

2. **Query the System**:
   - Use the `/query` endpoint to ask questions about uploaded documents or HR policies. The system will use FAISS and NLP to retrieve and generate a relevant response.

3. **Explore Relationships via Neo4j**:
   - Use Neo4j Aura’s visualization tools to explore how employees, departments, and policies are interconnected in the graph database.

---

## **Future Enhancements**

- Conversational Interface
- Integrate with Corporate Platforms
- Add Company Event's To Rag
- Add It Support to Rag
- Add Sources
- Add Conversation(Mesage history) Summarization
- Add Webpage Clickable Sources
- make use of keywords for advanced generic Response
- It support Function/Tool Calling (pre Filled Tickets)
- Add Hybrid Search
- Add Graph Rag
- Add INtegration with Employee Dashboard
- Use [open-parse](https://github.com/Filimoa/open-parse/blob/main/src/cookbooks/quickstart.ipynb) For Advance pdf and docx parsing

---

## **Contact Information**

For any questions or contributions, please contact **Tech Enerzal** at **<techenerzal@gmail.com>**.

---

This **README** now includes all the essential components such as Neo4j Aura and MongoDB Atlas, making it comprehensive for cloud-based architecture and scalable enterprise solutions.
