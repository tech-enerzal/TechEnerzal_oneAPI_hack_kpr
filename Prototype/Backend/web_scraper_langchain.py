# Import necessary modules
from bs4 import BeautifulSoup  # For parsing HTML
import json  # For handling JSON data
import os  # For file system operations
from datetime import datetime  # For working with dates
from neo4j import GraphDatabase  # For Neo4j integration
import numpy as np
from sklearnex import patch_sklearn, config_context
patch_sklearn()

# Neo4j connection class using 'with' statement and 'verify_connectivity()'
class SocialGraphDB:

    def __init__(self, uri, auth):
        self.uri = uri
        self.auth = auth

    def verify_connection(self):
        try:
            # Verify Neo4j connectivity using 'with' and 'verify_connectivity'
            with GraphDatabase.driver(self.uri, auth=self.auth) as driver:
                driver.verify_connectivity()
            print("Connected to Neo4j successfully!")
        except Exception as e:
            print(f"Connection error: {e}")

    def create_event_node(self, event_data):
        with GraphDatabase.driver(self.uri, auth=self.auth) as driver:
            with driver.session() as session:
                session.write_transaction(self._create_and_return_event, event_data)

    @staticmethod
    def _create_and_return_event(tx, event_data):
        query = (
            "MERGE (e:Event {title: $title}) "
            "SET e += {date: $date, description: $description, img_url: $img_url, event_url: $event_url}"
        )
        tx.run(query, title=event_data['title'], date=event_data['date'], description=event_data['description'],
               img_url=event_data['img_url'], event_url=event_data['event_url'])

# Scrape the events from HTML file
import os

# Scrape the events from HTML file
def scrape_events(html_file):
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

        event_divs = soup.find_all('div', class_='event')
        print(f"Found {len(event_divs)} events in the HTML")

        for event in event_divs:
            title = event.find('h2').get_text()
            date = event.find('p', class_='event-date').get_text().replace('Date: ', '')
            description = event.find_all('p')[1].get_text()
            img_url = event.find('img')['src']
            event_url = event.find('a')['href']

            event_data = {
                'title': title,
                'date': date,
                'description': description,
                'img_url': img_url,
                'event_url': event_url
            }

            events.append(event_data)
            print(f"Scraped Event: {event_data}")

        return events

    except Exception as e:
        print(f"Error while scraping: {e}")
        return []

# Save the scraped events into a JSON file for the current month
def save_to_monthly_json(events):
    try:
        current_date = datetime.now()
        month_year = current_date.strftime('%Y-%m')  # Format: YYYY-MM

        # Set the filename for this month's JSON
        json_filename = f"Events-{month_year}.json"
        json_path = os.path.join("Backend", "Database", "Company-Event", json_filename)

        # Ensure the folder exists
        if not os.path.exists("Backend/Database/Company-Event"):
            os.makedirs("Backend/Database/Company-Event")
            print(f"Created folder: Backend/Database/Company-Event")

        # Load existing data if the file exists, otherwise start fresh
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                existing_data = json.load(f)
        else:
            existing_data = []

        # Append the new events
        existing_data.extend(events)

        # Save the updated data back to the JSON file
        with open(json_path, 'w') as f:
            json.dump(existing_data, f, indent=4)

        print(f"Scraped data saved to {json_path}")
        return f"Scraped data saved to {json_path}"

    except Exception as e:
        print(f"Error while saving JSON: {e}")
        return "Error saving JSON"

# Add the scraped events to the Neo4j Aura graph database
def add_to_graph_database(events):
    try:
        # Neo4j Aura credentials (replace with your credentials)
        uri = "neo4j+s://9bcdec7f.databases.neo4j.io"  # Update with your Neo4j Aura Bolt URI
        auth = ("neo4j", "cdh-HboU0Iho3e_RUa8e5lJ_At3jIUkfDLhS6uriPUs")  # Replace with your username and password

        print(f"Connecting to Neo4j at {uri} as {auth[0]}")
        db = SocialGraphDB(uri=uri, auth=auth)

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
    html_file = "Frontend\pages\events.html"

    # Step 1: Scrape the events
    events = scrape_events(html_file)

    if not events:
        print("No events scraped, skipping saving and database insertion.")
        return

    # Step 2: Save to JSON file for the current month
    json_message = save_to_monthly_json(events)

    # Step 3: Add to Neo4j graph database
    db_message = add_to_graph_database(events)

    # Print results of both actions
    print(json_message)
    print(db_message)

# Run the scraping, saving, and Neo4j insertion once
if __name__ == "__main__":
    print("Running the script once.")
    run_scraping_and_saving()
