# RAG.py

import logging
import re
import json
import warnings
import requests
import pymongo
from pymongo import MongoClient

# FAISS imports
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS

# Ranker imports (for future use)
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
faiss_Full_HR = FAISS.load_local(
    "Prototype/Backend/Database/HR/Vector/Full_HR",
    embedding_function,
    allow_dangerous_deserialization=True
)
faiss_QA_HR = FAISS.load_local(
    "Prototype/Backend/Database/HR/Vector/QA_HR",
    embedding_function,
    allow_dangerous_deserialization=True
)
logging.info("FAISS vector stores loaded.")

# Initialize the ranker (for future use)
logging.debug("Initializing the ranker...")
ranker = Ranker(model_name="rank-T5-flan", cache_dir="/Temp")
logging.info("Ranker initialized.")

# MongoDB Atlas connection string
atlas_connection_string = "mongodb+srv://techenerzal:Chatbot%408188@cluster0.najcz.mongodb.net/?retryWrites=true&w=majority"

def determine_database_requirements_func(arguments):
    # This function is a placeholder as the assistant (LLM) provides 'database_required' and 'categories'
    pass

def get_employee_data_func(arguments, employee_id):
    fields = arguments.get('fields')
    if not fields:
        return "Please specify which fields you want to retrieve."

    # Map field names to database fields
    valid_fields = {
        'employee_id': 'employee_id',
        'name': 'name',
        'department': 'department',
        'job_title': 'job_title',
        'salary': 'salary',
        'leaves_taken_this_month': 'leaves_taken_this_month',
        # Add other fields as needed
    }

    # Build the projection dictionary for MongoDB
    projection = {valid_fields[field]: 1 for field in fields if field in valid_fields}
    if not projection:
        return "Invalid fields requested."

    # Connect to MongoDB
    client = MongoClient(atlas_connection_string)
    db = client["KPR_Business_chatbot"]
    employees = db["Employee_Dashboard"]

    # Fetch the employee data based on employee_id
    employee = employees.find_one({"employee_id": int(employee_id)}, projection)
    client.close()

    if employee:
        # Remove the '_id' field if it exists
        employee.pop('_id', None)
        return employee
    else:
        return "Employee not found."

def get_hr_policy_func(arguments):
    policy_name = arguments.get('policy_name')
    if not policy_name:
        return "Please specify the HR policy you want to retrieve."

    # Query the vector database for the policy
    try:
        logging.info(f"Searching for HR policy: {policy_name}")
        # Perform similarity search using FAISS vector store
        k = 5  # Number of top results to retrieve
        search_results = faiss_Full_HR.similarity_search(policy_name, k=k)
        logging.debug(f"Retrieved {len(search_results)} documents from vector store.")

        if not search_results:
            return f"No HR policy found matching '{policy_name}'."

        # Combine the contents of the top search results
        policy_content = "\n\n".join([doc.page_content for doc in search_results])

        return policy_content

    except Exception as e:
        logging.exception("Error querying the vector database for HR policy.")
        return f"An error occurred while retrieving the HR policy: {str(e)}"

def get_company_events_func(arguments):
    # For now, keep this function as pass
    pass

# Define the function tools
determine_database_requirements = {
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

get_employee_data = {
    "name": "get_employee_data",
    "description": "Fetch specific personal data fields of an employee from the MongoDB database.",
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

get_hr_policy = {
    "name": "get_hr_policy",
    "description": "Fetch HR policy information by querying the vector database.",
    "parameters": {
        "type": "object",
        "properties": {
            "policy_name": {
                "type": "string",
                "description": "The name or topic of the HR policy to retrieve."
            }
        },
        "required": ["policy_name"]
    }
}

get_company_events = {
    "name": "get_company_events",
    "description": "Fetch company event information from the database.",
    "parameters": {
        "type": "object",
        "properties": {
            "event_name": {
                "type": "string",
                "description": "The name of the company event to retrieve."
            }
        },
        "required": ["event_name"]
    }
}

def generate_stream(payload):
    logging.info("Starting generate_stream...")
    # Extract model, messages, options from payload
    model = payload.get('model', 'default-model')
    messages = payload.get('messages', [])
    options = payload.get('options', {})
    temperature = options.get('temperature', 0.8)
    max_tokens = options.get('num_predict', 4096)
    context_length = options.get('num_ctx', 8192)
    stream = payload.get('stream', True)  # We'll handle streaming to the frontend separately
    logging.debug(f"Model: {model}, Temperature: {temperature}, Max Tokens: {max_tokens}, Stream: {stream}")

    # Process messages to get user question and chat history
    if not messages or not isinstance(messages, list):
        logging.error("Invalid messages format in payload.")
        raise ValueError('Invalid messages format')

    # Get employee_id from payload
    employee_id = payload.get('employee_id')

    # Include the function tools in the payload
    tools = [
        {
            'type': 'function',
            'function': determine_database_requirements
        },
        {
            'type': 'function',
            'function': get_employee_data
        },
        {
            'type': 'function',
            'function': get_hr_policy
        },
        {
            'type': 'function',
            'function': get_company_events
        }
    ]

    # Prepare the model API payload
    model_payload = {
        'model': model,
        'messages': messages,
        'options': {
            'temperature': temperature,
            'num_predict': max_tokens,
            'num_ctx': context_length,
        },
        'tools': tools,
        'stream': False,  # Do not stream from the assistant
        'keep_alive': 0
    }

    try:
        while True:
            # Make the API call to the LLM model
            logging.info("Making API call to the LLM model.")
            response = requests.post('http://localhost:11434/api/chat', json=model_payload)
            response.raise_for_status()
            logging.info("API call successful.")

            assistant_response = response.json()

            # Process the assistant's response
            if 'message' in assistant_response:
                message = assistant_response['message']

                if 'tool_calls' in message:
                    # Handle function calls internally
                    for tool_call in message['tool_calls']:
                        function_name = tool_call['function']['name']
                        arguments = tool_call['function']['arguments']

                        # **Add this check to parse arguments if they are a string**
                        if isinstance(arguments, str):
                            arguments = json.loads(arguments)

                        logging.info(f"Assistant called function: {function_name} with arguments: {arguments}")

                        if function_name == 'determine_database_requirements':
                            # The assistant provides 'database_required' and 'categories' in arguments
                            database_required = arguments.get('database_required')
                            categories = arguments.get('categories', [])

                            # Prepare a message to send back to the assistant
                            content = json.dumps({
                                'database_required': database_required,
                                'categories': categories
                            })
                            messages.append({
                                'role': 'function',
                                'name': 'determine_database_requirements',
                                'content': content
                            })

                        elif function_name == 'get_employee_data':
                            result = get_employee_data_func(arguments, employee_id)
                            messages.append({
                                'role': 'function',
                                'name': 'get_employee_data',
                                'content': json.dumps(result)
                            })

                        elif function_name == 'get_hr_policy':
                            result = get_hr_policy_func(arguments)
                            messages.append({
                                'role': 'function',
                                'name': 'get_hr_policy',
                                'content': json.dumps(result)
                            })

                        elif function_name == 'get_company_events':
                            # Keep this function as pass; no data will be provided
                            messages.append({
                                'role': 'function',
                                'name': 'get_company_events',
                                'content': "No data available for company events."
                            })

                        else:
                            # Handle unknown functions
                            logging.warning(f"Unknown function called: {function_name}")
                            messages.append({
                                'role': 'function',
                                'name': function_name,
                                'content': f"Function {function_name} is not recognized."
                            })

                    # Update model_payload with new messages
                    model_payload['messages'] = messages
                    continue  # Make another API call

                else:
                    # No function calls, assistant has provided the final response
                    assistant_reply = message.get('content', '').strip()
                    if stream:
                        # Stream the response to the front-end
                        for chunk in assistant_reply:
                            yield json.dumps({'content': chunk})
                    else:
                        # Send the full response at once
                        yield json.dumps({'content': assistant_reply})
                    break  # Exit the loop

            else:
                # Handle other responses
                logging.warning("No 'message' in assistant_response")
                break  # Exit the loop

    except Exception as e:
        logging.exception("Error in generate_stream")
        yield json.dumps({"error": f"Error in generating response: {str(e)}"})
