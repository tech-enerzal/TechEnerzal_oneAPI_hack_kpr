import base64
from flask import Flask, request, Response, jsonify
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

# Import the RAG module
import RAG

app = Flask(__name__)
CORS(app)

# MongoDB Atlas connection string
atlas_connection_string = "mongodb+srv://techenerzal:Chatbot%408188@cluster0.najcz.mongodb.net/?retryWrites=true&w=majority"

# Connect to MongoDB Atlas
client = MongoClient(atlas_connection_string)

# Access your database
db = client["KPR_Business_chatbot"]

# Create or access a collection
users = db["Employee_Credentials"]

# JWT Configuration
app.config['JWT_SECRET_KEY'] = 'Enerzal8188'
jwt = JWTManager(app)

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Directory to store uploaded files temporarily
UPLOAD_FOLDER = 'Prototype/Backend/Temp'  # Use a relative path
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper function to check if the file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to read the content of the file
def read_file_content(file_path, file_type):
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

# Endpoint to handle file uploads
@app.route('/api/upload', methods=['POST'])
def upload_file():

    logging.info("Received file upload request.")

    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    # If user does not select a file, the browser also
    # submits an empty part without a filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Ensure the upload directory exists
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Extract the file type and read content
        file_type = filename.rsplit('.', 1)[1].lower()
        file_content = read_file_content(file_path, file_type)

        # Remove the file after reading it
        os.remove(file_path)

        # Return the extracted content
        return jsonify({'content': file_content}), 200

    return jsonify({'error': 'File type not allowed'}), 400

# Stream the response from the chatbot API
def stream_response(generator_function):
    try:
        for response_chunk in generator_function:
            yield response_chunk + '\n'
            logging.debug(response_chunk)
    except Exception as e:
        error_message = json.dumps({"error": f"Failed to fetch the assistant response: {str(e)}"})
        logging.exception("Error in stream_response")
        yield error_message + '\n'

# Function to decide the model based on some logic
def decide_model(conversation_history):
    # # Example logic to choose the model
    # if len(conversation_history) > 5:
    #     return "llama3.1:8b"  # Some large model for long conversations
    # else:
    #     return "gemma2:2b"  # Some small model for short conversations
    return "llama3.1:8b"  # Large model for heavy lifting (e.g., document parsing)
    #return "gemma2:27b" 

# Chatbot endpoint for handling messages and file content
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        logging.info("Received chat request.")
        data = request.json
        messages = data.get('messages')
        if not messages or not isinstance(messages, list):
            logging.error("Invalid messages format.")
            return jsonify({'error': 'Invalid messages format'}), 400

        model = decide_model(messages)
        logging.info(f"Model selected: {model}")

        payload = {
            'model': model,
            'messages': messages,
            'options': {
                "temperature": 0.8,
                "num_predict": -1,                
                #"num_ctx":8192,
            },
            'stream': True,
            'keep_alive': 0
        }
        logging.info("Payload prepared for RAG.generate_stream.")

        def generate_response():
            response_generator = RAG.generate_stream(payload)
            for chunk in response_generator:
                yield chunk

        logging.info("Starting to stream response to frontend.")
        return Response(stream_response(generate_response()), content_type='application/json')

    except Exception as e:
        logging.exception("Failed to fetch the assistant response.")
        return jsonify({'error': f'Failed to fetch the assistant response: {str(e)}'}), 500

# Signup Route - Register the user and require them to set up TOTP
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Check if user already exists
        if users.find_one({"email": email}):
            return jsonify({"msg": "User already exists"}), 400

        # Generate TOTP secret
        totp_secret = pyotp.random_base32()

        # Save the user to MongoDB with the TOTP secret
        users.insert_one({
            "email": email,
            "password": hashed_password,
            "two_factor_enabled": True,
            "two_factor_secret": totp_secret
        })

        # Generate TOTP URI and QR code
        totp = pyotp.TOTP(totp_secret)
        uri = totp.provisioning_uri(email, issuer_name="ChatbotApp")  # TOTP URI for the authenticator app
        img = qrcode.make(uri)  # Create QR code image

        # Save QR code image to a buffer to send it as a base64 string
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        qrcode_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return jsonify({
            "msg": "User registered successfully.",
            "qrcode": qrcode_base64  # Correct base64-encoded QR code string
        }), 201
        
    except Exception as e:
        return jsonify({"msg": "Signup failed", "error": str(e)}), 500


# Login Route - TOTP is mandatory for all users
@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        logging.info("Received login request.")
        data = request.get_json()
        email = data['email']
        password = data['password']
        token = data.get('token')

        logging.debug(f"Login data received: email={email}")

        # Find user by email
        user = users.find_one({"email": email})

        if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password']):
            logging.info(f"Login failed: Invalid credentials for email {email}.")
            return jsonify({'msg': 'Invalid credentials'}), 400

        # TOTP is required for all users during login
        if not token:
            logging.info(f"Login failed: TOTP 2FA token not provided for email {email}.")
            return jsonify({'msg': '2FA required'}), 401

        totp = pyotp.TOTP(user['two_factor_secret'])
        if not totp.verify(token):
            logging.info(f"Login failed: Invalid TOTP token for email {email}.")
            return jsonify({'msg': 'Invalid 2FA token'}), 400

        # Create JWT token after successful login
        access_token = create_access_token(identity=email)
        logging.info(f"Login successful for email {email}. JWT token generated.")

        return jsonify({'token': access_token}), 200
    except Exception as e:
        logging.exception("Login failed.")
        return jsonify({'msg': "Login failed", "error": str(e)}), 500

# Verify JWT-protected route to retrieve user data
@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def profile():
    email = get_jwt_identity()
    logging.info(f"Profile request for user {email}.")
    user = users.find_one({"email": email}, {"_id": 0, "password": 0, "two_factor_secret": 0})
    return jsonify(user), 200

# Function to clean up the upload folder when the server stops
def cleanup_upload_folder():
    if os.path.exists(app.config['UPLOAD_FOLDER']):        
        # List all files and directories in the upload folder
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # Check if the file is not 'Test1.txt'
            if filename not in ['Test1.txt', 'Readme.md']:
                try:
                    # If it's a file or a symbolic link, delete it
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.remove(file_path)
                    # If it's a directory, delete it and all its contents
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')
        print("Upload folder cleaned up, 'Test1.txt' preserved.")
    else:
        print("Upload folder does not exist.")
        

atexit.register(cleanup_upload_folder)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    logging.info("Starting Flask app...")
    app.run(host='0.0.0.0', port=5000, debug=True)
