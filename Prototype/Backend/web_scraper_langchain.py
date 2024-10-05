"""
@fileoverview
This module implements a web scraper for the Business Sector Chatbot using LangChain and Neo4j.
It parses HTML files to extract company event information, saves the data to JSON files,
and inserts the events into a Neo4j graph database. The scraper is designed to work with
LangChain's vector stores and FAISS for efficient data retrieval and management.

@version 1.0
"""

# Import necessary modules
from bs4 import BeautifulSoup  # For parsing HTML content
import json  # For handling JSON data
import os  # For file system operations
from datetime import datetime  # For working with date and time
from neo4j import GraphDatabase  # For connecting and interacting with Neo4j
import numpy as np  # For numerical operations
from sklearnex import patch_sklearn, config_context  # For accelerating scikit-learn operations
patch_sklearn()  # Apply scikit-learn optimizations

# Neo4j connection class using 'with' statement and 'verify_connectivity()'
class SocialGraphDB:
    """
    A class to handle interactions with the Neo4j graph database for storing and managing company events.

    Attributes:
        uri (str): The Neo4j database URI.
        auth (tuple): A tuple containing the username and password for Neo4j authentication.
    """

    def __init__(self, uri, auth):
        """
        Initializes the SocialGraphDB instance with the provided Neo4j URI and authentication credentials.

        Args:
            uri (str): The Neo4j database URI.
            auth (tuple): A tuple containing the username and password for Neo4j authentication.
        """
        self.uri = uri
        self.auth = auth

    def verify_connection(self):
        """
        Verifies the connectivity to the Neo4j database.

        Raises:
            Exception: If the connection to Neo4j fails.
        """
        try:
            # Establish a connection to Neo4j using the provided URI and authentication
            with GraphDatabase.driver(self.uri, auth=self.auth) as driver:
                # Verify connectivity to the database
                driver.verify_connectivity()
            print("Connected to Neo4j successfully!")
        except Exception as e:
            print(f"Connection error: {e}")

    def create_event_node(self, event_data):
        """
        Creates or updates an Event node in the Neo4j database with the provided event data.

        Args:
            event_data (dict): A dictionary containing event details such as title, date, description, img_url, and event_url.
        """
        with GraphDatabase.driver(self.uri, auth=self.auth) as driver:
            with driver.session() as session:
                # Execute the transaction to create/update the Event node
                session.write_transaction(self._create_and_return_event, event_data)

    @staticmethod
    def _create_and_return_event(tx, event_data):
        """
        Static method to execute the Cypher query for creating/updating an Event node.

        Args:
            tx (Transaction): The Neo4j transaction context.
            event_data (dict): A dictionary containing event details.

        Returns:
            None
        """
        # Define the Cypher query to merge (create if not exists) an Event node with given properties
        query = (
            "MERGE (e:Event {title: $title}) "
            "SET e += {date: $date, description: $description, img_url: $img_url, event_url: $event_url}"
        )
        # Execute the query with the provided event data
        tx.run(query, title=event_data['title'], date=event_data['date'],
               description=event_data['description'],
               img_url=event_data['img_url'], event_url=event_data['event_url'])
# Scrape the events from HTML file
import os


# Scrape the events from HTML file
def scrape_events(html_file):
    """
    Scrapes event information from the specified HTML file.

    Args:
        html_file (str): The relative path to the HTML file containing event data.

    Returns:
        list: A list of dictionaries, each containing details of an event.
    """
    try:
        # Get the current script path (where the script is being run)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Define the start of the relative path folder (up until "Prototype")
        relative_start_folder = "Prototype"
        
        # Find the base path up until the "Prototype" directory dynamically
        base_path = script_dir.split(relative_start_folder)[0] + relative_start_folder

        # Join the base path with the relative path to the HTML file
        html_file_path = os.path.join(base_path, html_file)

        print(f"Trying to load HTML file from: {html_file_path}")
        
        # Check if the HTML file exists
        if not os.path.exists(html_file_path):
            print(f"HTML file not found: {html_file_path}")
            return []

        # Read the HTML file content
        with open(html_file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        print(f"HTML content loaded from {html_file_path}")

        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')

        # List to store event data
        events = []

        # Find all div elements with class 'event' representing individual events
        event_divs = soup.find_all('div', class_='event')
        print(f"Found {len(event_divs)} events in the HTML")

        # Iterate over each event div to extract event details
        for event in event_divs:
            title = event.find('h2').get_text()  # Extract event title
            date = event.find('p', class_='event-date').get_text().replace('Date: ', '')  # Extract and clean event date
            description = event.find_all('p')[1].get_text()  # Extract event description
            img_url = event.find('img')['src']  # Extract image URL
            event_url = event.find('a')['href']  # Extract event URL

            # Compile the extracted data into a dictionary
            event_data = {
                'title': title,
                'date': date,
                'description': description,
                'img_url': img_url,
                'event_url': event_url
            }

            events.append(event_data)  # Add the event data to the events list
            print(f"Scraped Event: {event_data}")

        return events

    except Exception as e:
        print(f"Error while scraping: {e}")
        return []

# Save the scraped events into a JSON file for the current month
def save_to_monthly_json(events):
    """
    Saves the list of scraped events into a monthly JSON file.

    Args:
        events (list): A list of dictionaries, each containing event details.

    Returns:
        str: A message indicating the result of the save operation.
    """
    try:
        # Get the current date and format it as 'YYYY-MM'
        current_date = datetime.now()
        month_year = current_date.strftime('%Y-%m')  # Format: YYYY-MM

        # Set the filename for this month's JSON
        json_filename = f"Events-{month_year}.json"
        json_path = os.path.join("Backend", "Database", "Company-Event", json_filename)

        # Ensure the target directory exists; create it if it doesn't
        if not os.path.exists("Backend/Database/Company-Event"):
            os.makedirs("Backend/Database/Company-Event")
            print(f"Created folder: Backend/Database/Company-Event")

        # Load existing data if the file exists, otherwise start with an empty list
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                existing_data = json.load(f)
        else:
            existing_data = []

        # Append the new events to the existing data
        existing_data.extend(events)

        # Save the updated data back to the JSON file with indentation for readability
        with open(json_path, 'w') as f:
            json.dump(existing_data, f, indent=4)

        print(f"Scraped data saved to {json_path}")
        return f"Scraped data saved to {json_path}"

    except Exception as e:
        print(f"Error while saving JSON: {e}")
        return "Error saving JSON"

# Add the scraped events to the Neo4j Aura graph database
def add_to_graph_database(events):
    """
    Inserts the list of events into the Neo4j graph database.

    Args:
        events (list): A list of dictionaries, each containing event details.

    Returns:
        str: A message indicating the result of the database insertion.
    """
    try:
        # Neo4j Aura credentials (replace with your actual credentials)
        uri = "neo4j+s://9bcdec7f.databases.neo4j.io"  # Update with your Neo4j Aura Bolt URI
        auth = ("neo4j", "cdh-HboU0Iho3e_RUa8e5lJ_At3jIUkfDLhS6uriPUs")  # Replace with your username and password

        print(f"Connecting to Neo4j at {uri} as {auth[0]}")
        db = SocialGraphDB(uri=uri, auth=auth)  # Initialize the SocialGraphDB instance

        # Verify Neo4j connection
        db.verify_connection()

        # Add each event to the graph database
        for event in events:
            db.create_event_node(event)
            print(f"Added Event to Neo4j: {event}")

        return f"{len(events)} events added to Neo4j database."

    except Exception as e:
        print(f"Error while connecting to Neo4j: {e}")
        return f"Error connecting to Neo4j: {str(e)}"

# This function will combine the scraping, saving to JSON, and adding to Neo4j steps
def run_scraping_and_saving():
    """
    Executes the complete scraping, saving, and database insertion process.

    It scrapes events from the specified HTML file, saves them to a monthly JSON file,
    and inserts them into the Neo4j graph database.

    Returns:
        None
    """
    html_file = "Frontend\pages\events.html"  # Relative path to the HTML file containing events

    # Step 1: Scrape the events from the HTML file
    events = scrape_events(html_file)

    if not events:
        print("No events scraped, skipping saving and database insertion.")
        return

    # Step 2: Save the scraped events to a monthly JSON file
    json_message = save_to_monthly_json(events)

    # Step 3: Add the scraped events to the Neo4j graph database
    db_message = add_to_graph_database(events)

    # Print results of both actions
    print(json_message)
    print(db_message)

# Run the scraping, saving, and Neo4j insertion once when the script is executed directly
if __name__ == "__main__":
    print("Running the script once.")
    run_scraping_and_saving()
