# Rag.py - Complete code with all changes and working code

import re
import json
import logging
import warnings
import requests
import ast

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

# Hardcoded employee data (since We can't put Secret api key in Public repo)
sample_employee = {
    "employee_id": 1,
    "name": "John Doe",
    "department": "IT",
    "job_title": "Software Engineer",
    "salary": 75000.00,
    "leaves_taken_this_month": 2
}

# Define allowed fields for get_employee_data
ALLOWED_FIELDS = ["employee_id", "name", "department", "job_title", "salary", "leaves_taken_this_month"]

# Define field name mapping for normalization
FIELD_NAME_MAPPING = {
    'employeeid': 'employee_id',
    'name': 'name',
    'department': 'department',
    'jobtitle': 'job_title',
    'salary': 'salary',
    'leavestakenthismonth': 'leaves_taken_this_month',
    # Add more mappings as needed
}

def get_employee_data(fields):
    """
    Fetch specific personal data fields of an employee.
    Only allowed fields are returned. Fields not in the allowed list are ignored.
    """
    logging.debug(f"Fetching employee data for fields: {fields}")
    # Normalize and map fields
    mapped_fields = []
    invalid_fields = []
    for field in fields:
        normalized_field = field.replace('_', '').replace(' ', '').lower()
        if normalized_field in FIELD_NAME_MAPPING:
            mapped_field = FIELD_NAME_MAPPING[normalized_field]
            mapped_fields.append(mapped_field)
        else:
            invalid_fields.append(field)
    if invalid_fields:
        logging.warning(f"Requested invalid fields: {invalid_fields}")
    # Fetch data for valid fields
    employee_info = {field: sample_employee.get(field) for field in mapped_fields}
    return {
        "employee_info": employee_info,
        "invalid_fields": invalid_fields
    }

def get_hr_policy(user_query):
    """
    Fetch HR policy information by querying the vector database.
    """
    logging.debug(f"Fetching HR policy for query: {user_query}")
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
    top_policies = reranked_hr_results[:1]
    logging.info(f"Selected top {len(top_policies)} HR policies.")

    # Prepare the combined policy text
    policy_text = '\n\n'.join([policy['text'] for policy in top_policies])

    return policy_text

def generate_stream(payload):
    logging.info("Starting generate_stream...")
    # Extract model, messages, options from payload
    model = payload.get('model', 'default-model')
    messages = payload.get('messages', [])
    options = payload.get('options', {})
    temperature = options.get('temperature', 0.8)
    max_tokens = options.get('num_predict', int(4096))
    context_length = options.get('num_ctx', int(8192))
    stream = False  # Streaming is disabled
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
        # Define the available functions
        available_functions = [
            {
                "name": "get_employee_data",
                "description": "Fetch specific personal data fields of an employee from the database.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fields": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ALLOWED_FIELDS
                            },
                            "description": "List of employee data fields to retrieve. Allowed fields are: employee_id, name, department, job_title, salary, leaves_taken_this_month."
                        }
                    },
                    "required": ["fields"]
                }
            },
            {
                "name": "get_hr_policy",
                "description": "Fetch HR policy information by querying the vector database.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_query": {
                            "type": "string",
                            "description": "The query related to HR policy that is to be similarity searched in HR dataset."
                        }
                    },
                    "required": ["user_query"]
                }
            }
        ]

        # Initialize flag to include tools in the payload
        include_tools = True

        while True:
            if include_tools:
                tools_payload = [
                    {
                        "type": "function",
                        "function": func
                    } for func in available_functions
                ]
            else:
                tools_payload = []

            # Prepare payload for the model API call
            model_api_url = 'http://localhost:11434/api/chat'  # Replace with your actual model API endpoint
            api_payload = {
                'model': model,
                'messages': messages,
                'stream': False,
                'tools': tools_payload,
                'keep_alive': 0
            }
            logging.info(f"API payload: {json.dumps(api_payload)}")

            # Make the API call
            logging.info(f"Making API call to {model_api_url}")
            response = requests.post(model_api_url, json=api_payload)
            logging.info(f"API response status: {response.status_code}")
            response.raise_for_status()
            response_data = response.json()
            logging.info(f"API response data: {json.dumps(response_data)}")

            # Check if the model wants to call a function
            if 'message' in response_data and 'tool_calls' in response_data['message']:
                tool_calls = response_data['message']['tool_calls']
                for tool_call in tool_calls:
                    function_name = tool_call['function']['name']
                    arguments = tool_call['function']['arguments']
                    logging.info(f"Model requested to call function: {function_name} with arguments: {arguments}")

                    # Execute the corresponding function
                    if function_name == 'get_employee_data':
                        requested_fields = arguments.get('fields', [])
                        if isinstance(requested_fields, str):
                            try:
                                requested_fields = ast.literal_eval(requested_fields)
                            except Exception as e:
                                logging.error(f"Failed to parse requested_fields: {requested_fields}. Error: {str(e)}")
                                requested_fields = []
                        function_result = get_employee_data(requested_fields)
                        # Prepare an assistant message with the function result
                        employee_info = function_result.get('employee_info', {})
                        invalid_fields = function_result.get('invalid_fields', [])
                        context_message = "Employee Data:\n"
                        for field, value in employee_info.items():
                            context_message += f"{field}: {value}\n"
                        if invalid_fields:
                            context_message += f"\nNote: The following requested fields are not available or invalid and were ignored: {', '.join(invalid_fields)}"

                        # Add context as an assistant message
                        messages.append({
                            'role': 'assistant',
                            'content': context_message
                        })
                    elif function_name == 'get_hr_policy':
                        user_query = arguments.get('user_query', '')
                        function_result = get_hr_policy(user_query)
                        # Add policy text as an assistant message
                        messages.append({
                            'role': 'assistant',
                            'content': f"HR Policy Information:\n{function_result}"
                        })
                    else:
                        logging.error(f"Unknown function requested: {function_name}")
                        error_message = f"Error: Function {function_name} not found."
                        messages.append({
                            'role': 'assistant',
                            'content': error_message
                        })

                    logging.info(f"Function {function_name} executed and assistant message added.")

                # After processing function calls, set include_tools to False to prevent further tool calls
                include_tools = False
                continue  # Continue the loop to make the next API call without tools
            else:
                # No function call needed, send the assistant's reply directly
                if 'message' in response_data:
                    message = response_data['message']
                    # Ensure content is not empty
                    if message.get('content'):
                        yield json.dumps(message)
                    else:
                        # If content is empty, possibly the model did not generate a response
                        logging.warning("Assistant's response content is empty.")
                        yield json.dumps({"error": "Assistant did not generate any content."})
                else:
                    logging.error("Invalid response format from the model API.")
                    yield json.dumps({"error": "Invalid response from the model API."})
                break  # Exit the loop as no further processing is needed

    except Exception as e:
        logging.exception("Error in generate_stream")
        yield json.dumps({"error": f"Error in generating response: {str(e)}"})
