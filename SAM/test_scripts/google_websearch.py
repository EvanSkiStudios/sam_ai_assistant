import requests
import os

from dotenv import load_dotenv

# Load Env
load_dotenv()
API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

# Create a CSE client instance
cse_client = requests.Session()

SEARCH_QUERY = "evanskistudios"
cse_url = f"https://customsearch.googleapis.com/customsearch/v1?key={API_KEY}&cx={ENGINE_ID}"


def google_search(SEARCH_QUERY):
    string = f"&q={SEARCH_QUERY}"
    search_string = cse_url + string

    # Make a GET request to the CSE API
    response = cse_client.get(search_string)

    # Parse JSON response and extract top result
    json_data = response.json()
    top_result = json_data["items"][0]

    # Loop through all results and print cleanly
    if "items" in json_data:
        # for idx, item in enumerate(json_data["items"], start=1):
            # print(f"\nResult {idx}:")
            # print(f" Title: {item.get('title')}")
            # print(f" URL: {item.get('link')}")
            # print(f" Snippet: {item.get('snippet')}")
        return json_data
    else:
        print("No results found.")
        return {}
