from ollama import ChatResponse, chat

from Tools.wiki_search.wiki_search import wiki_search


def search_wikipedia(query):
    return wiki_search(query)


messages = [
    {'role': 'system', 'content': 'You will be given a json of a wikipedia page summary, use it to answer the user'},
    {'role': 'user', 'content': 'Search the wikipedia for donald trump'}
]
print('Prompt:', messages[0]['content'])

available_functions = {
  'search_wikipedia': search_wikipedia
}

response: ChatResponse = chat(
  'llama3.2',
  messages=messages,
  tools=[search_wikipedia],
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
  final_response = chat('llama3.2', messages=messages)
  print('Final response:', final_response.message.content)

else:
  print('No tool calls returned from model')