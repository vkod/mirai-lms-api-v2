#!/usr/bin/env python3
import csv
import json
import os
import requests
import time
import argparse
import sys

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process personas and call digital twin agent API')
    parser.add_argument('--csv-path', default='personas.csv', help='Path to the CSV file')
    parser.add_argument('--api-url', default='https://mirai-lms-api.azurewebsites.net/create_digital_twin_agent', help='URL of the API endpoint')
    parser.add_argument('--limit', type=int, default=10, help='Limit the number of rows to process (for testing)')
    args = parser.parse_args()

    csv_path = args.csv_path
    api_url = args.api_url
    row_limit = args.limit

    # Check if the CSV file exists
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)

    # Read the CSV file
    print(f"Reading persona data from {csv_path}...")
    personas = []
    
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            personas = [row for idx, row in enumerate(reader) if idx < row_limit or row_limit <= 0]
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

    # Process each row in the CSV
    total_count = len(personas)
    current_count = 0

    for persona in personas:
        current_count += 1
        
        # Ensure required columns exist
        if not ('persona' in persona and 'webtraffic' in persona):
            print(f"Warning: Skipping row {current_count}: Missing required 'persona' or 'webtraffic' column")
            continue
        
        #Print the webtraffic data for debugging
        print(f"Webtraffic data for persona '{persona['persona']}': {persona['webtraffic']}")

        # Ensure webtraffic_data is a string - don't parse the JSON
        webtraffic_data = persona['webtraffic']
            
        # Print the data type for debugging
        print(f"Webtraffic data type: {type(webtraffic_data)}")

        # Prepare the request body based on API definition
        # The API now expects a JSON body with data and existing_digital_twin
        body = {
            'data': webtraffic_data,
            'existing_digital_twin': ''
        }
        
        # Show progress
        print(f"[{current_count}/{total_count}] Processing persona: {persona['persona']}")
        
        try:
            # Call the API with JSON body
            print(f"  Sending request to {api_url}")
            print(f"  Request body: {json.dumps(body)}")
            
            # Make the request with json body
            response = requests.post(api_url, json=body)
            
            # Print full response for debugging
            print(f"  Response status code: {response.status_code}")
            print(f"  Response headers: {response.headers}")
            
            # Try to print response body - might be JSON or text
            try:
                print(f"  Response body: {json.dumps(response.json())}")
            except json.JSONDecodeError:
                print(f"  Response body (text): {response.text[:500]}...")
            
            response.raise_for_status()  # Raise an exception for 4XX/5XX responses
            print(f"  Success: Request completed successfully")
        except requests.exceptions.RequestException as e:
            print(f"  Error: Failed to process persona: {persona['persona']}")
            print(f"  Details: {str(e)}")
        
        # Optional: Add a small delay to avoid overwhelming the API
        time.sleep(0.1)

    print(f"Processing complete. Processed {current_count} personas.")

if __name__ == "__main__":
    main()