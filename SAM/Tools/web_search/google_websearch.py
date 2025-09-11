import requests
import os

from dotenv import load_dotenv

# Load Env
load_dotenv()
API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

# Create a CSE client instance
cse_client = requests.Session()
cse_url = f"https://customsearch.googleapis.com/customsearch/v1?key={API_KEY}&cx={ENGINE_ID}"


def google_search(search_query):
    string = f"&q={search_query}"
    search_string = cse_url + string

    # Make a GET request to the CSE API
    response = cse_client.get(search_string)

    if response.status_code != 200:
        return []

    # Parse JSON response and extract top result
    json_data = response.json()

    # Return a clean list (title, snippet, link)
    if "items" in json_data:
        results = []
        for item in json_data["items"][:5]:  # limit to first 5
            results.append({
                "title": item.get("title"),
                "snippet": item.get("snippet"),
                "link": item.get("link")
            })
        return results
    else:
        return []
