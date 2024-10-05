# Updated Flask application with streaming removed

"""
@fileoverview
This Flask application serves as the backend for the Business Sector Chatbot. It handles user authentication (signup and login with TOTP),
file uploads, and chat interactions using Retrieval-Augmented Generation (RAG). The application connects to a MongoDB Atlas database to store user credentials
and employs JWT for secure access. It also integrates logging for monitoring and debugging purposes.

@version 1.0
"""

import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json
from werkzeug.utils import secure_filename
import PyPDF2
import docx
import atexit
import shutil
import logging
import bcrypt
import pyotp
import qrcode
from io import BytesIO
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import pymongo
from pymongo import MongoClient
import dns  # required for connecting with SRV

# Import the RAG module for handling chat responses
import RAG

# Initialize the Flask application
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# MongoDB Atlas connection string
atlas_connection_string = "mongodb+srv://techenerzal:Chatbot%408188@cluster0.najcz.mongodb.net/?retryWrites=true&w=majority"

# Connect to MongoDB Atlas using the provided connection string
client = MongoClient(atlas_connection_string)

# Access the specific database within MongoDB
db = client["KPR_Business_chatbot"]

# Create or access the 'Employee_Credentials' collection within the database
users = db["Employee_Credentials"]

# JWT Configuration for handling secure tokens
app.config['JWT_SECRET_KEY'] = 'Enerzal8188'  # Secret key for JWT encoding/decoding
jwt = JWTManager(app)  # Initialize JWT Manager

# Initialize logging with INFO level and a specific format
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Directory to store uploaded files temporarily
UPLOAD_FOLDER = 'Prototype/Backend/Temp'  # Use a relative path for the upload directory
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}  # Define allowed file extensions
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # Set the upload folder in Flask config

def allowed_file(filename):
    """
    Checks if the uploaded file has an allowed extension.

    Args:
        filename (str): The name of the file to check.

    Returns:
        bool: True if the file has an allowed extension, False otherwise.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_file_content(file_path, file_type):
    """
    Reads and extracts the content from a file based on its type.

    Args:
        file_path (str): The path to the file.
        file_type (str): The type of the file ('txt', 'pdf', 'docx').

    Returns:
        str: The extracted text content from the file.
    """
    if file_type == 'txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    elif file_type == 'pdf':
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ''
            for page in range(len(reader.pages)):
                text += reader.pages[page].extract_text()
            return text
    elif file_type == 'docx':
        doc = docx.Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return ''

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Endpoint to handle file uploads. It accepts files with allowed extensions, extracts their content,
    and returns the content in JSON format.

    Returns:
        Response: JSON response containing the extracted file content or an error message.
    """
    logging.info("Received file upload request.")

    # Check if the POST request has the 'file' part
    if 'file' not in request.files:
        logging.warning("No file part in the request.")
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    # Check if a file was selected
    if file.filename == '':
        logging.warning("No file selected for uploading.")
        return jsonify({'error': 'No selected file'}), 400

    # Validate and process the file if it has an allowed extension
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)  # Secure the filename to prevent directory traversal
        # Ensure the upload directory exists; create it if it doesn't
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)  # Save the file to the upload directory

        # Extract the file type and read its content
        file_type = filename.rsplit('.', 1)[1].lower()
        file_content = read_file_content(file_path, file_type)

        # Remove the file after extracting its content to free up space
        os.remove(file_path)

        # Return the extracted content as a JSON response
        logging.info(f"File '{filename}' uploaded and processed successfully.")
        return jsonify({'content': file_content}), 200

    # Return an error if the file type is not allowed
    logging.warning(f"File type '{file.filename.rsplit('.', 1)[1].lower()}' not allowed.")
    return jsonify({'error': 'File type not allowed'}), 400

def decide_model(conversation_history):
    """
    Decides which model to use based on the conversation history.

    Args:
        conversation_history (list): The history of the conversation.

    Returns:
        str: The identifier of the chosen model.
    """
    # Example logic to choose the model based on conversation length
    # if len(conversation_history) > 5:
    #     return "llama3.1:8b"  # Large model for long conversations
    # else:
    #     return "gemma2:2b"  # Small model for short conversations
    return "llama3.1:8b"  # Currently always returns the large model for heavy lifting

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Chatbot endpoint for handling messages and file content. It processes the incoming messages,
    decides which model to use, and returns the response back to the client.

    Returns:
        Response: JSON response containing the chatbot's reply or an error message.
    """
    try:
        logging.info("Received chat request.")
        data = request.json  # Parse JSON data from the request
        messages = data.get('messages')  # Retrieve the 'messages' field from the JSON
        if not messages or not isinstance(messages, list):
            logging.error("Invalid messages format received.")
            return jsonify({'error': 'Invalid messages format'}), 400

        model = decide_model(messages)  # Decide which model to use based on the conversation history
        logging.info(f"Model selected: {model}")

        # Prepare the payload for the RAG module
        payload = {
            'model': model,
            'messages': messages,
            'options': {
                "temperature": 0.8,
                "num_predict": -1,
                # "num_ctx":8192,  # Uncomment and set if context length is needed
            },
            'stream': False,
            'keep_alive': 0
        }
        logging.info("Payload prepared for RAG.generate_stream.")

        # Get the response from the RAG module
        response_generator = RAG.generate_stream(payload)
        response_chunks = list(response_generator)
        response_text = ''.join(response_chunks)
        logging.info("Received response from RAG module.")

        # Parse the response text into JSON
        response_data = json.loads(response_text)
        return jsonify(response_data), 200

    except Exception as e:
        # Log the exception with stack trace and return an error response
        logging.exception("Failed to fetch the assistant response.")
        return jsonify({'error': f'Failed to fetch the assistant response: {str(e)}'}), 500

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """
    Signup endpoint to register a new user. It hashes the user's password, generates a TOTP secret,
    creates a QR code for TOTP setup, and stores the user credentials in MongoDB.

    Returns:
        Response: JSON response containing a success message and the base64-encoded QR code,
                  or an error message if signup fails.
    """
    try:
        data = request.get_json()  # Parse JSON data from the request
        email = data.get('email')  # Retrieve the 'email' field
        password = data.get('password')  # Retrieve the 'password' field

        # Hash the password using bcrypt for secure storage
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Check if the user already exists in the database
        if users.find_one({"email": email}):
            logging.info(f"Signup attempt failed: User '{email}' already exists.")
            return jsonify({"msg": "User already exists"}), 400

        # Generate a TOTP secret for two-factor authentication
        totp_secret = pyotp.random_base32()

        # Save the user to MongoDB with the hashed password and TOTP secret
        users.insert_one({
            "email": email,
            "password": hashed_password,
            "two_factor_enabled": True,
            "two_factor_secret": totp_secret
        })
        logging.info(f"User '{email}' registered successfully with TOTP.")

        # Generate TOTP URI and QR code for authenticator app setup
        totp = pyotp.TOTP(totp_secret)
        uri = totp.provisioning_uri(email, issuer_name="ChatbotApp")  # TOTP URI for the authenticator app
        img = qrcode.make(uri)  # Create QR code image

        # Save QR code image to a buffer to send it as a base64 string
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        qrcode_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')  # Encode the image in base64

        # Return a JSON response with a success message and the QR code
        logging.info(f"QR code generated for user '{email}'.")
        return jsonify({
            "msg": "User registered successfully.",
            "qrcode": qrcode_base64  # Base64-encoded QR code string
        }), 201

    except Exception as e:
        # Return an error response if signup fails
        logging.exception("Signup failed.")
        return jsonify({"msg": "Signup failed", "error": str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Login endpoint that authenticates a user using email, password, and TOTP token.
    It verifies the credentials, validates the TOTP token, and issues a JWT upon successful authentication.

    Returns:
        Response: JSON response containing the JWT token on success,
                  or an error message if authentication fails.
    """
    try:
        logging.info("Received login request.")
        data = request.get_json()  # Parse JSON data from the request
        email = data['email']  # Retrieve the 'email' field
        password = data['password']  # Retrieve the 'password' field
        token = data.get('token')  # Retrieve the 'token' field for TOTP

        logging.debug(f"Login data received: email={email}")

        # Find the user in the database by email
        user = users.find_one({"email": email})

        # Verify if the user exists and the password is correct
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password']):
            logging.info(f"Login failed: Invalid credentials for email {email}.")
            return jsonify({'msg': 'Invalid credentials'}), 400

        # Ensure that a TOTP token is provided for two-factor authentication
        if not token:
            logging.info(f"Login failed: TOTP 2FA token not provided for email {email}.")
            return jsonify({'msg': '2FA required'}), 401

        # Verify the provided TOTP token
        totp = pyotp.TOTP(user['two_factor_secret'])
        if not totp.verify(token):
            logging.info(f"Login failed: Invalid TOTP token for email {email}.")
            return jsonify({'msg': 'Invalid 2FA token'}), 400

        # Create a JWT token after successful login
        access_token = create_access_token(identity=email)
        logging.info(f"Login successful for email {email}. JWT token generated.")

        # Return the JWT token in the response
        return jsonify({'token': access_token}), 200
    except Exception as e:
        # Log the exception and return an error response if login fails
        logging.exception("Login failed.")
        return jsonify({'msg': "Login failed", "error": str(e)}), 500

@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def profile():
    """
    Protected route to retrieve the authenticated user's profile information.
    It requires a valid JWT token to access.

    Returns:
        Response: JSON response containing the user's profile data,
                  or an error message if the user is not authenticated.
    """
    email = get_jwt_identity()  # Get the email from the JWT token
    logging.info(f"Profile request for user {email}.")
    # Retrieve user data excluding sensitive fields
    user = users.find_one({"email": email}, {"_id": 0, "password": 0, "two_factor_secret": 0})
    return jsonify(user), 200

def cleanup_upload_folder():
    """
    Cleans up the upload folder by deleting all files and directories except 'Test1.txt' and 'Readme.md'
    when the server stops. This ensures that temporary files do not accumulate over time.
    """
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        # Iterate over all files and directories in the upload folder
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # Check if the file should not be deleted
            if filename not in ['Test1.txt', 'Readme.md']:
                try:
                    # If it's a file or a symbolic link, delete it
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.remove(file_path)
                        logging.info(f"Deleted file: {file_path}")
                    # If it's a directory, delete it and all its contents
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        logging.info(f"Deleted directory and its contents: {file_path}")
                except Exception as e:
                    logging.error(f'Failed to delete {file_path}. Reason: {e}')
        logging.info("Upload folder cleaned up, 'Test1.txt' and 'Readme.md' preserved.")
    else:
        logging.info("Upload folder does not exist.")

# Register the cleanup function to run when the application exits
atexit.register(cleanup_upload_folder)

if __name__ == '__main__':
    # Ensure the upload directory exists; create it if it doesn't
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        logging.info(f"Created upload directory at {app.config['UPLOAD_FOLDER']}.")

    logging.info("Starting Flask app...")
    # Run the Flask application on all available IPs on port 5000 with debug mode enabled
    app.run(host='0.0.0.0', port=5000, debug=True)
