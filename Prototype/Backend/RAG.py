# Updated Rag.py with hardcoded employee data retrieval
import re
import json
import logging
import warnings
import requests

# FAISS imports
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS

# Ranker (assuming you have a Ranker class)
from flashrank import Ranker, RerankRequest

# Suppress warnings
warnings.filterwarnings("ignore")

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize embedding function
logging.debug("Initializing embedding function...")
embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
logging.info("Embedding function initialized.")

# Load FAISS vector stores
logging.debug("Loading FAISS vector stores...")
faiss_Full_HR = FAISS.load_local("Prototype/Backend/Database/HR/Vector/Full_HR", embedding_function, allow_dangerous_deserialization=True)
faiss_QA_HR = FAISS.load_local("Prototype/Backend/Database/HR/Vector/QA_HR", embedding_function, allow_dangerous_deserialization=True)
logging.info("FAISS vector stores loaded.")

# Initialize the ranker
logging.debug("Initializing the ranker...")
ranker = Ranker(model_name="rank-T5-flan", cache_dir="/Temp")
logging.info("Ranker initialized.")

# Hardcoded employee data (since there's only one entry)
sample_employee = {
    "employee_id": 1,
    "name": "John Doe",
    "department": "IT",
    "job_title": "Software Engineer",
    "salary": 75000.00,
    "leaves_taken_this_month": 2
}

def generate_stream(payload):
    logging.info("Starting generate_stream...")
    # Extract model, messages, options from payload
    model = payload.get('model', 'default-model')
    messages = payload.get('messages', [])
    options = payload.get('options', {})
    temperature = options.get('temperature', 0.8)
    max_tokens = options.get('num_predict', int(4096))
    context_length = options.get('num_ctx', int(8192))
    stream = False  # Disable streaming when tool calling is involved
    logging.debug(f"Model: {model}, Temperature: {temperature}, Max Tokens: {max_tokens}, Stream: {stream}")

    # Process messages to get user question and chat history
    if not messages or not isinstance(messages, list):
        logging.error("Invalid messages format in payload.")
        raise ValueError('Invalid messages format')

    # Extract the user's latest message
    user_message = messages[-1].get('content', '')
    logging.debug(f"User message: {user_message}")
    # Build chat history (excluding the last message)
    chat_history = messages[:-1]

    try:
        # Step 1: Get user query (user_message already obtained)
        logging.info("Step 1: User query obtained.")

        # Step 2: Determine if the database is required using the 'determine_database_requirements' function
        logging.info("Step 2: Determining if the database is required.")
        determine_db_requirements_function = {
            "name": "determine_database_requirements",
            "description": "Determine if the user's query requires accessing the database and specify the categories of data needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "database_required": {
                        "type": "boolean",
                        "description": "Whether the database is required to answer the query."
                    },
                    "categories": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["personal_data", "hr_policy", "company_events"]
                        },
                        "description": "List of data categories required."
                    }
                },
                "required": ["database_required"]
            }
        }

        # Prepare payload for the function calling
        function_call_payload = {
            'model': 'gemma2:2b',
            'messages': [
                {'role': 'user', 'content': user_message}
            ],
            'stream': False,
            'tools': [
                {
                    "type": "function",
                    "function": determine_db_requirements_function
                }
            ],
            'keep_alive': 0
        }

        logging.debug(f"Function call payload: {function_call_payload}")

        # Make the API call to determine database requirements
        function_api_url = 'http://localhost:11434/api/chat'
        logging.info(f"Making API call to {function_api_url} to determine database requirements.")
        function_response = requests.post(function_api_url, json=function_call_payload)
        function_response.raise_for_status()
        function_data = function_response.json()
        logging.debug(f"Function response data: {function_data}")

        # Check if functions are called
        database_required = False
        categories = []
        if 'message' in function_data and 'tool_calls' in function_data['message']:
            tool_calls = function_data['message']['tool_calls']
            for tool_call in tool_calls:
                if tool_call['function']['name'] == 'determine_database_requirements':
                    args = tool_call['function']['arguments']
                    database_required = args.get('database_required', False)
                    categories = args.get('categories', [])
                    logging.info(f"Database required: {database_required}, Categories: {categories}")
        else:
            logging.warning("No tool calls found in the response.")

        if database_required:
            logging.info("Database is required. Proceeding based on categories.")
            if 'personal_data' in categories:
                # Call 'get_employee_data' function
                logging.info("Fetching personal employee data.")
                get_employee_data_function = {
                    "name": "get_employee_data",
                    "description": "Fetch specific personal data fields of an employee from the database.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "fields": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["employee_id", "name", "department", "job_title", "salary", "leaves_taken_this_month"]
                                },
                                "description": "List of employee data fields to retrieve."
                            }
                        },
                        "required": ["fields"]
                    }
                }

                # Prepare payload for fetching employee data
                employee_data_payload = {
                    'model': model,
                    'messages': messages,
                    'stream': False,
                    'tools': [
                        {
                            "type": "function",
                            "function": get_employee_data_function
                        }
                    ],
                    'keep_alive': 0
                }

                # Make the API call to get employee data
                logging.info(f"Making API call to {function_api_url} to get employee data.")
                employee_response = requests.post(function_api_url, json=employee_data_payload)
                employee_response.raise_for_status()
                employee_data = employee_response.json()
                logging.debug(f"Employee data response: {employee_data}")

                # Process the employee data
                if 'message' in employee_data and 'tool_calls' in employee_data['message']:
                    tool_calls = employee_data['message']['tool_calls']
                    for tool_call in tool_calls:
                        if tool_call['function']['name'] == 'get_employee_data':
                            args = tool_call['function']['arguments']
                            fields = args.get('fields', [])
                            # Fetch data from the hardcoded sample_employee
                            employee_info = {field: sample_employee.get(field) for field in fields}
                            logging.debug(f"Fetched employee info: {employee_info}")
                            # Add the employee info to the messages
                            messages.append({
                                'role': 'system',
                                'content': f"Employee Data: {employee_info}"
                            })
            if 'hr_policy' in categories:
                # Call 'get_hr_policy' function
                logging.info("Fetching HR policy information.")
                get_hr_policy_function = {
                    "name": "get_hr_policy",
                    "description": "Fetch HR policy information by querying the vector database.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "User_Query": {
                                "type": "string",
                                "description": "The query related to HR policy that is to be similarity searched in HR dataset."
                                }
                        },
                        "required": ["User_Query"]
                    }
                }

                # Prepare payload for fetching HR policy
                hr_policy_payload = {
                    'model': model,
                    'messages': messages,
                    'stream': False,
                    'tools': [
                        {
                            "type": "function",
                            "function": get_hr_policy_function
                        }
                    ],
                    'keep_alive': 0
                }

                # Make the API call to get HR policy
                logging.info(f"Making API call to {function_api_url} to get HR policy.")
                hr_policy_response = requests.post(function_api_url, json=hr_policy_payload)
                hr_policy_response.raise_for_status()
                hr_policy_data = hr_policy_response.json()
                logging.debug(f"HR policy data response: {hr_policy_data}")

                # Process the HR policy data
                if 'message' in hr_policy_data and 'tool_calls' in hr_policy_data['message']:
                    tool_calls = hr_policy_data['message']['tool_calls']
                    for tool_call in tool_calls:
                        if tool_call['function']['name'] == 'get_hr_policy':
                            args = tool_call['function']['arguments']
                            user_query = args.get('User_Query', '')
                            # Query the vector database
                            k_full = 10
                            hr_candidates = faiss_Full_HR.similarity_search(user_query, k=k_full)
                            logging.debug(f"Retrieved {len(hr_candidates)} HR policy documents.")

                            # Re-rank and select top policies
                            hr_passages = [{
                                'id': doc.metadata.get('ids', ''),
                                'text': doc.page_content,
                                'meta': doc.metadata
                            } for doc in hr_candidates]

                            rerank_request = RerankRequest(query=user_query, passages=hr_passages)
                            reranked_hr_results = ranker.rerank(rerank_request)
                            logging.debug("Reranked HR policy results obtained.")

                            # Select top HR policies
                            top_policies = reranked_hr_results[:3]
                            logging.info(f"Selected top {len(top_policies)} HR policies.")

                            # Prepare context and add to messages
                            context_sections = '\n\n'.join([policy['text'] for policy in top_policies])
                            messages.append({
                                'role': 'system',
                                'content': f'HR Policy Information:\n{context_sections}'
                            })

        # Step 7: Call the model via API
        logging.info("Step 7: Calling the model via API.")
        # Prepare payload for the model API
        model_api_url = 'http://localhost:11434/api/chat'  # Replace with your actual model API endpoint
        model_payload = {
            'model': model,
            'messages': messages,  # Use the modified messages list
            'options': {
                'temperature': temperature,
                "num_predict": max_tokens,
                "num_ctx": context_length,
            },
            'stream': False,  # Streaming is disabled when functions are involved
            'keep_alive': 0
        }
        logging.debug(f"Model API payload prepared with messages.")

        # Function to get the response from the model API
        def get_model_response():
            logging.debug(f"Making model API call to {model_api_url}")
            response = requests.post(model_api_url, json=model_payload)
            response.raise_for_status()
            data = response.json()
            logging.info("Model API call successful.")
            logging.debug(f"Model response data: {data}")
            return data

        # Get the response
        model_response = get_model_response()

        # Check for 'tools' field and handle accordingly
        if 'message' in model_response:
            message = model_response['message']
            if 'tool_calls' in message:
                logging.info("Functions were called in the response.")
                # Process tool calls as per your application's logic
                # Ensure intermediary setup is not displayed to the user
                # Prepare the final assistant message without intermediary details
                final_response = {
                    'role': 'assistant',
                    'content': message.get('content', '')
                }
                yield json.dumps(final_response)
            else:
                # No functions were called, simply return the assistant's reply
                yield json.dumps(message)
        else:
            logging.error("Invalid response format from the model API.")
            yield json.dumps({"error": "Invalid response from the model API."})

    except Exception as e:
        logging.exception("Error in generate_stream")
        yield json.dumps({"error": f"Error in generating response: {str(e)}"})

