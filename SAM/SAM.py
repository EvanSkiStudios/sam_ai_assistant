import asyncio
import json
import sys
from pathlib import Path

from ollama import Client, chat

from Tools.gemma_vision import download_image, image_cleanup
from SAM_ruleset import SAM_personality
from memories.custom_facts import random_factoids
from memories.meet_the_robinsons import fetch_chatter_description
from memories.message_memory_manager import gather_current_user_message_history, stash_user_conversation_history
from utility_scripts.system_logging import setup_logger
from utility_scripts.utility import current_date_time, split_response

# configure logging
logger = setup_logger(__name__)

# import from ruleset
sam_rules = SAM_personality

# model settings for easy swapping
sam_model_name = 'SAM_llama3.2'
sam_ollama_model = 'llama3.2'
sam_vision_model = 'gemma3'

# used for conversations
sam_current_session_chat_cache = {}  # holds everyone's messages under their username as a key
current_conversation_user = None
current_user_conversation_messages = []  # holds the current users messages to be added to the session cache


def session_information():
    return (
        sam_current_session_chat_cache,
        current_conversation_user,
        current_user_conversation_messages,
    )


def SAM_Create():
    try:
        client = Client()
        response = client.create(
            model=sam_model_name,
            from_=sam_ollama_model,
            system=sam_rules,
            stream=False,
        )
        # print(f"# Client: {response.status}")
        logger.info(f"# Client: {response.status}")
        return session_information()

    except ConnectionError as e:
        logger.error('Ollama is not running!')
        sys.exit(1)  # Exit program with error code 1

    except Exception as e:
        # Catches any other unexpected errors
        logger.error("❌ An unexpected error occurred:", e)
        sys.exit(1)


def build_system_prompt(user_name, user_nickname):
    current_user_details = fetch_chatter_description(user_name)

    factoids = random_factoids()
    current_time = current_date_time()

    system_prompt = f"""{sam_rules}
{factoids}
{current_time}
You are currently talking to {user_name}.
Their name is {user_name}.  
Their discord name is {user_nickname}. 
Refer to {user_name} as {user_nickname} unless otherwise specified. 
{current_user_details}
"""
    return system_prompt


# === Main Entry Point ===
async def SAM_Message(message_author_name, message_author_nickname, message_content, attachment_url, attachments):
    llm_response = None

    if attachment_url:
        loop = asyncio.get_event_loop()
        image_file_name = await loop.run_in_executor(None, download_image, attachment_url)

        if image_file_name:
            llm_response = await SAM_Converse_Image(
                message_author_name, message_author_nickname, message_content, image_file_name, attachments, attachment_url
            )
        else:
            logger.error("IMAGE ERROR")
            # print("IMAGE ERROR")

    if llm_response is None:
        llm_response = await SAM_Converse(message_author_name, message_author_nickname, message_content)

    cleaned = llm_response.replace("'", "\\'")
    return split_response(cleaned)


# === Core Logic ===
async def SAM_Converse(user_name, user_nickname, user_input):
    # check who we are currently talking too - if someone new is talking to us, fetch their memories
    # if it's a different user, cache the current history to file the swap out the memories
    await switch_current_user_speaking_too(user_name, user_input)

    system_prompt = build_system_prompt(user_name, user_nickname)
    full_prompt = [{"role": "system", "content": system_prompt + "Here is what they have said to you: "}] \
                  + current_user_conversation_messages \
                  + [{"role": "user", "name": user_name, "content": user_input}]

    # should prevent discord heartbeat from complaining we are taking too long
    response = await asyncio.to_thread(
        chat,
        model=sam_model_name,
        messages=full_prompt
    )

    # Add the response to the messages to maintain the history
    new_chat_entries = [
        {"role": "user", "name": user_name, "content": user_input},
        {"role": "assistant", "content": response.message.content},
    ]
    update_conversation_history(user_name, new_chat_entries)

    # Debug Console Output
    debug_print = (f"""
===================================
{user_name} REPLY:\n{user_input}\n
RESPONSE:\n{response.message.content}
===================================\n
""")
    logger.info(debug_print)

    # return the message to main script
    return response.message.content


async def SAM_Converse_Image(user_name, user_nickname, user_input, image_file_name, attachments, attachment_url):
    # check who we are currently talking too - if someone new is talking to us, fetch their memories
    # if it's a different user, cache the current history to file the swap out the memories
    await switch_current_user_speaking_too(user_name, user_input)

    # Go one directory up
    parent_dir = Path(__file__).resolve().parent
    path = parent_dir / 'images' / image_file_name

    # print(attachments)
    # print(f'Analyzing image ({image_file_name})...')
    logger.debug(f"Attachments: {attachments}")
    logger.info(f'Analyzing image ({image_file_name})...')

    system_prompt = build_system_prompt(user_name, user_nickname)
    full_prompt = [{"role": "system", "content": system_prompt + "Here is what they have said to you: "}] \
                  + current_user_conversation_messages

    response = await asyncio.to_thread(
        chat,
        model=sam_vision_model,
        messages=full_prompt + [{"role": "user", "name": user_name, "content": user_input, 'images': [path]}]
        # options={'temperature': 0},  # Make responses more deterministic
    )

    output = response.message.content
    output = output.replace("'", "").strip()

    # Add the response to the messages to maintain the history
    new_chat_entries = [
        {"role": "user", "name": user_name, "content": user_input, "attachments": attachment_url},
        {"role": "assistant", "content": output},
    ]
    update_conversation_history(user_name, new_chat_entries)

    # Debug Console Output
    debug_print = (f"""
===================================
{user_name} REPLY:\n{user_input}\n
Attachments: {attachments}\n
RESPONSE:\n{response.message.content}
===================================\n
""")
    logger.info(debug_print)

    # clean up image
    image_cleanup(image_file_name)

    # return the message to main script
    return output


# === Helpers ===
async def switch_current_user_speaking_too(user_name, user_response):
    global current_conversation_user

    if user_name == current_conversation_user:
        return

    logger.warning(f"SWITCHING CONVERSER FROM {current_conversation_user} > {user_name}")
    # print(f"⚠️ SWITCHING CONVERSER FROM {current_conversation_user} > {user_name}")

    # check if we have already spoken to this person this session
    cached = sam_current_session_chat_cache.get(user_name)
    # print(cached)
    if cached:
        logger.info(f"FOUND USER CACHE FOR {user_name}")
        # print(f"✅ FOUND USER CACHE FOR {user_name}")
        current_user_conversation_messages[:] = json.loads(cached)
    else:
        current_user_conversation_messages[:] = await gather_current_user_message_history(user_name, user_response)

    # at the end switch to the new user
    current_conversation_user = user_name


def update_conversation_history(user_name, new_messages):
    current_user_conversation_messages.extend(new_messages)
    sam_current_session_chat_cache[user_name] = json.dumps(current_user_conversation_messages)
    stash_user_conversation_history(user_name, new_messages)
    # print(current_user_conversation_messages)
    # print(sam_current_session_chat_cache)
