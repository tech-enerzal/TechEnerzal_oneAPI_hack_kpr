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

# Initialize embedding function (for future use)
logging.debug("Initializing embedding function...")
embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
logging.info("Embedding function initialized.")

# Load FAISS vector stores (for future use)
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

    # Implement logic to fetch HR policy from the database
    # For demonstration, return a sample policy
    return f"Details of HR Policy: {policy_name}"

def get_company_events_func(arguments):
    event_name = arguments.get('event_name')
    if not event_name:
        return "Please specify the company event you want to know about."

    # Implement logic to fetch company event from the database
    # For demonstration, return a sample event
    return f"Details of Company Event: {event_name}"

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
    "description": "Fetch HR policy information from the database.",
    "parameters": {
        "type": "object",
        "properties": {
            "policy_name": {
                "type": "string",
                "description": "The name of the HR policy to retrieve."
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
    stream = payload.get('stream', True)
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
        'stream': stream,
        'keep_alive': 0
    }

    try:
        # Make the API call to the LLM model
        logging.info("Making API call to the LLM model.")
        response = requests.post('http://localhost:11434/api/chat', json=model_payload, stream=stream)
        response.raise_for_status()
        logging.info("API call successful.")

        # Process the assistant's response
        if stream:
            for line in response.iter_lines():
                if line:
                    assistant_response = json.loads(line.decode('utf-8'))

                    # Handle function calls
                    if 'message' in assistant_response:
                        message = assistant_response['message']
                        if 'tool_calls' in message:
                            for tool_call in message['tool_calls']:
                                function_name = tool_call['function']['name']
                                arguments = tool_call['function']['arguments']

                                if function_name == 'determine_database_requirements':
                                    # The assistant provides 'database_required' and 'categories' in arguments
                                    database_required = arguments.get('database_required')
                                    categories = arguments.get('categories', [])

                                    if database_required:
                                        # If database is required and categories include 'hr_policy' or 'company_events'
                                        if 'hr_policy' in categories or 'company_events' in categories:
                                            # Proceed to search vector DB and generate response with context
                                            # Steps are commented out for future implementation
                                            """
                                            logging.info("Database is required. Proceeding to search vector DB and generate response with context.")
                                            k_full = 10  # Number of documents to retrieve
                                            full_hr_candidates = faiss_Full_HR.similarity_search(user_message, k=k_full)
                                            logging.debug(f"Retrieved {len(full_hr_candidates)} documents from full HR dataset.")

                                            # Step 4: Query the QA of the top 2 selected Sections from Full HR
                                            top_sections = full_hr_candidates[:2]
                                            section_names = [doc.metadata.get('section_name') for doc in top_sections]
                                            logging.debug(f"Top section names: {section_names}")

                                            # Retrieve related FAQs from faiss_QA_HR
                                            qa_candidates = []
                                            for section_name in section_names:
                                                logging.debug(f"Querying FAQs for section: {section_name}")
                                                k_qa = 10
                                                qa_results = faiss_QA_HR.similarity_search(
                                                    user_message,
                                                    k=k_qa,
                                                    filter={'section_name': section_name}
                                                )
                                                qa_candidates.extend(qa_results)
                                                logging.debug(f"Retrieved {len(qa_results)} FAQs for section {section_name}")

                                            # Re-ranking the QA passages
                                            logging.info("Re-ranking the QA passages.")
                                            qa_passages = [{
                                                'id': doc.metadata.get('ids', ''),
                                                'text': doc.page_content,
                                                'meta': doc.metadata
                                            } for doc in qa_candidates]
                                            logging.debug(f"Total QA passages for re-ranking: {len(qa_passages)}")

                                            rerank_request = RerankRequest(query=user_message, passages=qa_passages)
                                            reranked_qa_results = ranker.rerank(rerank_request)
                                            logging.debug("Reranked QA results obtained.")

                                            # Select top FAQs
                                            top_faqs = reranked_qa_results[:3]
                                            logging.info(f"Selected top {len(top_faqs)} FAQs.")

                                            # Prepare context
                                            context_sections = '\n\n'.join([doc.page_content for doc in top_sections])
                                            context_faqs = '\n\n'.join([faq['text'] for faq in top_faqs])

                                            # context = f"Sections:\n{context_sections}\n\nFAQs:\n{context_faqs}"
                                            context = f"Sections:\n{context_sections}\n"

                                            logging.debug("Context prepared.")

                                            # Insert system message with context before the last user message
                                            messages.insert(-1, {
                                                'role': 'system',
                                                'content': f'Using the provided context from the database for Tech Enerzal to answer the user query.\nContext="{context}"'
                                            })
                                            logging.debug("Inserted system message with context into messages.")
                                            """

                                            # For now, we proceed without adding context

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
                                    result = get_company_events_func(arguments)
                                    messages.append({
                                        'role': 'function',
                                        'name': 'get_company_events',
                                        'content': json.dumps(result)
                                    })

                                else:
                                    # Handle unknown functions
                                    logging.warning(f"Unknown function called: {function_name}")

                            # Make another API call with updated messages
                            model_payload['messages'] = messages
                            response = requests.post('http://localhost:11434/api/chat', json=model_payload, stream=stream)
                            response.raise_for_status()
                            continue  # Process the new response

                        else:
                            # No function calls, yield the assistant's message
                            assistant_reply = message.get('content', '').strip()
                            yield json.dumps({'content': assistant_reply})

                    else:
                        # Handle other responses
                        pass

        else:
            assistant_response = response.json()
            # Process the assistant's response similarly
            if 'message' in assistant_response:
                message = assistant_response['message']
                assistant_reply = message.get('content', '').strip()
                yield json.dumps({'content': assistant_reply})

    except Exception as e:
        logging.exception("Error in generate_stream")
        yield json.dumps({"error": f"Error in generating response: {str(e)}"})
