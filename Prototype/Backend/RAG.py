# Updated Rag.py with proper API calls for 'determine_database_requirements'
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

# Hardcoded employee data (since We can't put Secret api key in Public repo)
sample_employee = {
    "employee_id": 1,
    "name": "John Doe",
    "department": "IT",
    "job_title": "Software Engineer",
    "salary": 75000.00,
    "leaves_taken_this_month": 2
}

def get_employee_data(fields):
    """
    Fetch specific personal data fields of an employee.
    Since we have only one employee, return data from sample_employee.
    """
    logging.debug(f"Fetching employee data for fields: {fields}")
    employee_info = {field: sample_employee.get(field) for field in fields}
    return employee_info

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
    top_policies = reranked_hr_results[:3]
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
        # Define the available functions
        available_functions = [
            {
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
            },
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
                                "enum": ["employee_id", "name", "department", "job_title", "salary", "leaves_taken_this_month"]
                            },
                            "description": "List of employee data fields to retrieve."
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

        # Step 1: Initial API call with functions
        logging.info("Step 1: Making initial API call with functions.")

        # Prepare payload for the initial model API call
        model_api_url = 'http://localhost:11434/api/chat'  # Replace with your actual model API endpoint
        initial_payload = {
            'model': model,
            'messages': messages,
            'stream': False,
            'tools': [
                {
                    "type": "function",
                    "function": func
                } for func in available_functions
            ],
            'keep_alive': 0
        }
        logging.debug(f"Initial API payload: {initial_payload}")

        # Make the initial API call
        logging.info(f"Making initial API call to {model_api_url}")
        initial_response = requests.post(model_api_url, json=initial_payload)
        initial_response.raise_for_status()
        response_data = initial_response.json()
        logging.debug(f"Initial response data: {response_data}")

        # Check if the model wants to call a function
        while True:
            if 'message' in response_data and 'tool_calls' in response_data['message']:
                tool_calls = response_data['message']['tool_calls']
                for tool_call in tool_calls:
                    function_name = tool_call['function']['name']
                    arguments = tool_call['function']['arguments']
                    logging.info(f"Model requested to call function: {function_name} with arguments: {arguments}")

                    # Execute the corresponding function
                    if function_name == 'get_employee_data':
                        function_result = get_employee_data(arguments.get('fields', []))
                    elif function_name == 'get_hr_policy':
                        function_result = get_hr_policy(arguments.get('user_query', ''))
                    else:
                        # For 'determine_database_requirements', since we don't have an implementation, we can simulate a response or handle it appropriately
                        logging.error(f"Function {function_name} is not implemented on the backend.")
                        function_result = {"error": f"Function {function_name} is not implemented."}

                    logging.debug(f"Function {function_name} returned: {function_result}")

                    # Add the function result to the messages
                    messages.append({
                        'role': 'function',
                        'name': function_name,
                        'content': json.dumps(function_result)
                    })

                    # Make another API call to the model with the updated messages
                    logging.info("Making subsequent API call with function result.")
                    subsequent_payload = {
                        'model': model,
                        'messages': messages,
                        'stream': False,
                        'tools': [
                            {
                                "type": "function",
                                "function": func
                            } for func in available_functions
                        ],
                        'keep_alive': 0
                    }
                    logging.debug(f"Subsequent API payload: {subsequent_payload}")

                    subsequent_response = requests.post(model_api_url, json=subsequent_payload)
                    subsequent_response.raise_for_status()
                    response_data = subsequent_response.json()
                    logging.debug(f"Subsequent response data: {response_data}")

                    # Check if the model wants to call another function
                    continue

            else:
                # No function call needed, send the assistant's reply directly
                if 'message' in response_data:
                    message = response_data['message']
                    yield json.dumps(message)
                else:
                    logging.error("Invalid response format from the model API.")
                    yield json.dumps({"error": "Invalid response from the model API."})
                break

    except Exception as e:
        logging.exception("Error in generate_stream")
        yield json.dumps({"error": f"Error in generating response: {str(e)}"})

