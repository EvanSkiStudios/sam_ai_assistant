import asyncio
import json
from pathlib import Path

from ollama import Client, chat

from Tools.gemma_vision import download_image, image_cleanup
from flukebot_ruleset import flukebot_personality
from memories.custom_facts import random_factoids
from memories.meet_the_robinsons import fetch_chatter_description
from memories.message_memory_manager import gather_current_user_message_history, stash_user_conversation_history
from utility_scripts.utility import current_date_time, split_response

# import from ruleset
flukebot_rules = flukebot_personality

# model settings for easy swapping
flukebot_model_name = 'flukebot_llama3.2'
flukebot_ollama_model = 'llama3.2'

# used for conversations
flukebot_current_session_chat_cache = {}
current_conversation_user = None
current_user_conversation_messages = []


def session_information():
    return (
        flukebot_current_session_chat_cache,
        current_conversation_user,
        current_user_conversation_messages,
    )


def Flukebot_Create():
    client = Client()
    response = client.create(
        model=flukebot_model_name,
        from_=flukebot_ollama_model,
        system=flukebot_rules,
        stream=False,
    )
    print(f"# Client: {response.status}")
    return session_information()


def build_system_prompt(user_name, user_nickname):
    current_user_details = fetch_chatter_description(user_name)

    factoids = random_factoids()
    current_time = current_date_time()
    return (
            flukebot_rules + "\n" +
            factoids + "\n" +
            current_time + "\n" +
            f"You are currently talking to {user_name}. Their name is {user_name}.\n" +
            f"Their display name is {user_nickname}.\n" +
            f"If {user_name} asks what their name is, use their display name.\n" +
            current_user_details
    )


# === Main Entry Point ===
async def Flukebot_Message(message_author_name, message_author_nickname, message_content, attachment_url, attachments):
    llm_response = None

    if attachment_url:
        loop = asyncio.get_event_loop()
        image_file_name = await loop.run_in_executor(None, download_image, attachment_url)

        if image_file_name:
            llm_response = await Flukebot_Converse_Image(
                message_author_name, message_author_nickname, message_content, image_file_name, attachments
            )
        else:
            print("IMAGE ERROR")

    if llm_response is None:
        llm_response = await Flukebot_Converse(message_author_name, message_author_nickname, message_content)

    cleaned = llm_response.replace("'", "\\'")
    return split_response(cleaned)


# === Core Logic ===
async def Flukebot_Converse(user_name, user_nickname, user_input):
    # check who we are currently talking too - if someone new is talking to us, fetch their memories
    # if it's a different user, cache the current history to file the swap out the memories
    await switch_current_user_speaking_too(user_name)

    system_prompt = build_system_prompt(user_name, user_nickname)
    full_prompt = [{"role": "system", "content": system_prompt + "Here is what they have said to you: "}] \
                  + current_user_conversation_messages \
                  + [{"role": "user", "name": user_name, "content": user_input}]

    # should prevent discord heartbeat from complaining we are taking too long
    response = await asyncio.to_thread(
        chat,
        model=flukebot_model_name,
        messages=full_prompt
    )

    # Add the response to the messages to maintain the history
    new_chat_entries = [
        {"role": "user", "name": user_name, "content": user_input},
        {"role": "assistant", "content": response.message.content},
    ]
    update_conversation_history(user_name, new_chat_entries)

    # Debug Console Output
    print("\n===================================\n")
    print(f"{user_name} REPLY:\n" + user_input + '\n')
    print("RESPONSE:\n" + response.message.content)
    print("\n===================================\n")

    # return the message to main script
    return response.message.content


async def Flukebot_Converse_Image(user_name, user_nickname, user_input, image_file_name, attachments):
    # check who we are currently talking too - if someone new is talking to us, fetch their memories
    # if it's a different user, cache the current history to file the swap out the memories
    await switch_current_user_speaking_too(user_name)

    # Go one directory up
    parent_dir = Path(__file__).resolve().parent
    path = parent_dir / 'images' / image_file_name

    print(attachments)
    print(f'Analyzing image ({image_file_name})...')

    system_prompt = build_system_prompt(user_name, user_nickname)
    full_prompt = [{"role": "system", "content": system_prompt + "Here is what they have said to you: "}] \
                  + current_user_conversation_messages

    response = await asyncio.to_thread(
        chat,
        model='gemma3',
        messages=full_prompt + [{"role": "user", "name": user_name, "content": user_input, 'images': [path]}]
        # options={'temperature': 0},  # Make responses more deterministic
    )

    output = response.message.content
    output = output.replace("'", "").strip()

    # Add the response to the messages to maintain the history
    new_chat_entries = [
        {"role": "user", "name": user_name, "content": user_input},
        {"role": "assistant", "content": output},
    ]
    update_conversation_history(user_name, new_chat_entries)

    # Debug Console Output
    print("\n===================================\n")
    print(f"{user_name} REPLY:\n" + user_input + '\n')
    print(attachments)
    print("RESPONSE:\n" + output)
    print("\n===================================\n")

    # clean up image
    image_cleanup(image_file_name)

    # return the message to main script
    return output


# === Helpers ===
async def switch_current_user_speaking_too(user_name):
    global current_conversation_user

    if user_name == current_conversation_user:
        return

    print(f"⚠️ SWITCHING CONVERSER FROM {current_conversation_user} > {user_name}")

    # check if we have already spoken to this person this session
    cached = flukebot_current_session_chat_cache.get(user_name)
    # print(cached)
    if cached:
        print(f"✅ FOUND USER CACHE FOR {user_name}")
        current_user_conversation_messages[:] = json.loads(cached)
    else:
        current_user_conversation_messages[:] = await gather_current_user_message_history(user_name)
        current_conversation_user = user_name


def update_conversation_history(user_name, new_messages):
    current_user_conversation_messages.extend(new_messages)
    flukebot_current_session_chat_cache[user_name] = json.dumps(current_user_conversation_messages)
    stash_user_conversation_history(user_name, new_messages)
    # print(current_user_conversation_messages)
    # print(flukebot_current_session_chat_cache)
