import json
import os
import requests

from dotenv import load_dotenv

# Load Env
load_dotenv()
GOOGLE_SEARCH_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")


def google_search(s: str):
    url_syntax = (
        "https://www.googleapis.com/customsearch/v1?" +
        f"key={GOOGLE_SEARCH_KEY}" +
        f"&cx={GOOGLE_ENGINE_ID}&" +
        f"q={str(s)}"
    )
    print(f"{url_syntax}")

    response = requests.get(url_syntax)

    # Check if the request was successful
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=4))
        return response.json()
    else:
        print(f"Request failed with status code {response.status_code}")
        return response.status_code


google_search_tool = {
    'type': 'function',
    'function': {
        'name': 'google_search_tool',
        'description': 'Searches Online',
        'parameters': {
            'type': 'object',
            'required': ['s'],
            'properties': {
                's': {'type': 'string', 'description': 'Search query string'}
            },
        },
    },
}
