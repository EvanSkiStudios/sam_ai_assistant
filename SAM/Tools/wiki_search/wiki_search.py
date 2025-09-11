import requests


cse_client = requests.Session()
cse_client.headers.update({
    "User-Agent": "SAM (https://github.com/EvanSkiStudios/sam_ai_assistant; EvanskiStudios@gmail.com)"
})


def wiki_search(query):
    query = query.replace(' ', '_')

    request_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
    print(request_url)

    response = cse_client.get(request_url)
    return response.content