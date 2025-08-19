from ollama import AsyncClient

MAX_LENGTH = 20
channel_history = []


async def summarize_chat(username, content):
    messages = await add_message_to_history(username, content)
    response = await llm_summarize_chat(messages)
    print(response)


async def add_message_to_history(username, content):
    global channel_history

    if username == 'flukebot':
        username = 'you'
    else:
        username = f'user: {username}'

    new_message = f"{username} said: {content}"

    channel_history.insert(0, new_message)
    if len(channel_history) > MAX_LENGTH:
        del channel_history[-1]  # Removes the last item

    message_references = list(reversed(channel_history))  # Gets a reversed copy
    return message_references


async def llm_summarize_chat(content):

    dictation_rules = 'You are in a discord server. Here are the last few messages in the chat: '.join(content)

    client = AsyncClient()
    response = await client.chat(
        model='llama3.2',
        messages=[
            {"role": "system", "content": dictation_rules},
            {"role": "user", "content": 'Please summarize the entire chat'}
        ],
        options={'temperature': 0},  # Make responses more deterministic
    )

    output = response.message.content
    return output

