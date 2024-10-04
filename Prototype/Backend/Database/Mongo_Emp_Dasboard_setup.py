import pymongo
from pymongo import MongoClient
import dns  # required for connecting with SRV

# MongoDB Atlas connection string
# Note: It's better to store this in an environment variable for security reasons
atlas_connection_string = "mongodb+srv://techenerzal:Chatbot%408188@cluster0.najcz.mongodb.net/?retryWrites=true&w=majority"

# Connect to MongoDB Atlas using the provided connection string
client = MongoClient(atlas_connection_string)

# Access your database (in this case, "KPR_Business_chatbot")
db = client["KPR_Business_chatbot"]

# Create or access the "Employee_Dashboard" collection within the database
employees = db["Employee_Dashboard"]

# Create an index on the 'employee_id' field to ensure that it is unique across all documents
employees.create_index([("employee_id", pymongo.ASCENDING)], unique=True)

# Define a sample document to be inserted into the "Employee_Dashboard" collection
sample_employee = {
    "employee_id": 1,                # Unique employee ID
    "name": "John Doe",              # Employee's name
    "department": "IT",              # Department where the employee works
    "job_title": "Software Engineer",# Employee's job title
    "salary": 75000.00,              # Employee's salary
    "leaves_taken_this_month": 2     # Number of leaves taken by the employee this month
}

# Insert the sample document into the "Employee_Dashboard" collection
result = employees.insert_one(sample_employee)

# Confirm that the connection to MongoDB was successful and print the ID of the inserted document
print("Connected to MongoDB Atlas successfully.")
print("Sample document inserted with ID:", result.inserted_id)

# Optional: Print details about the collection, such as the number of documents and the indexes in place
print("\nCollection details:")
print(f"Number of documents: {employees.count_documents({})}")  # Count and print the total number of documents in the collection
print("Indexes:")
for index in employees.list_indexes():  # Loop through and print details of all indexes in the collection
    print(f"  {index['name']}: {index['key']}")

# Close the connection to MongoDB Atlas once all operations are complete
client.close()
