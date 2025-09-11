from ollama import ChatResponse, chat

import SAM_ruleset
from Tools.web_search.google_websearch import google_search
from Tools.wiki_search.wiki_search import wiki_search

search_model = 'SAM_llama3.2'


def search_the_web(query):
    return google_search(query)


def search_wikipedia(query):
    return wiki_search(query)


messages = [
    # {'role': 'system',
    #  'content': 'You will be given information from google, It contains several results for the users query. Use the information to answer the users question.'},
    {'role': 'user', 'content': 'search the internet for "prometheus rising" by evanskistudios'}
]
print('Prompt:', messages[0]['content'])

available_functions = {
    'search_the_web': search_the_web,
    #'search_wikipedia': search_wikipedia
}

response: ChatResponse = chat(
    search_model,
    messages=messages,
    # tools=[search_the_web, search_wikipedia],
    tools=[search_the_web],
    options={'temperature': 0.2},  # Make responses less or more deterministic
)

if response.message.tool_calls:
    # There may be multiple tool calls in the response
    for tool in response.message.tool_calls:
        # Ensure the function is available, and then call it
        if function_to_call := available_functions.get(tool.function.name):
            print('Calling function:', tool.function.name)
            print('Arguments:', tool.function.arguments)
            output = function_to_call(**tool.function.arguments)
            print('Function output:', output)
        else:
            print('Function', tool.function.name, 'not found')

# Only needed to chat with the model using the tool call results
if response.message.tool_calls:
    # Add the function response to messages for the model to use
    messages.append(response.message)
    messages.append({'role': 'tool', 'content': str(output), 'tool_name': tool.function.name})

    # Get final response from model with function outputs
    final_response = chat(search_model, messages=[{'role': 'system', 'content': SAM_ruleset.SAM_personality}] + messages)
    print('Final response:', final_response.message.content)

else:
    print('No tool calls returned from model')
    response = chat(search_model, messages=[{'role': 'system', 'content': SAM_ruleset.SAM_personality}] + messages)
    print(response)
