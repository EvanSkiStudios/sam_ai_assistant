import json
import os

from memories.faiss_database import build_or_load_faiss_index, get_relevant_messages, faiss_index_delete
from utility_scripts.json_load_20 import json_get_last_n
from utility_scripts.system_logging import setup_logger

# configure logging
logger = setup_logger(__name__)

# get locations
memories_dir = os.path.dirname(os.path.realpath(__file__))


def gather_relevant_history(user_name, user_response):
    faiss_data = build_or_load_faiss_index(user_name)
    if faiss_data is None:
        logger.warning(f"⚠️ No Faiss found for {user_name}")
        return []

    relevant_messages = get_relevant_messages(user_response, faiss_data["index"], faiss_data["metadata"])
    # todo -- probably some future error handling here

    return relevant_messages


async def gather_current_user_message_history(user_name, user_response):
    users_dir = os.path.join(memories_dir, 'users')
    user_folder = os.path.join(users_dir, user_name)

    user_conversation_memory_file = os.path.join(user_folder, f"{user_name}.json")

    if not os.path.exists(user_conversation_memory_file):
        logger.warning(f"⚠️ No memories found for {user_name}")
        return []

    # Load the message history
    # message_history_references = json_get_last_n(user_conversation_memory_file)

    # Load the message history
    with open(user_conversation_memory_file, "r") as f:
        message_history_references = json.load(f)

    logger.info(f"✅ Finished processing memories")
    return message_history_references


def stash_user_conversation_history(user_name, conversation_data):
    consent_file = os.path.join(memories_dir, "__consent_users.json")

    if not os.path.exists(consent_file):
        logger.error("❌❌❌ Can not find user consent file!!")
        return

    # Load the existing data
    with open(consent_file, 'r') as file:
        data = json.load(file)

    # Check if user is in consent file
    if str(user_name) not in data:
        return

    users_dir = os.path.join(memories_dir, 'users')
    user_folder = os.path.join(users_dir, user_name)

    os.makedirs(user_folder, exist_ok=True)

    user_conversation_memory_file = os.path.join(user_folder, f"{user_name}.json")

    if os.path.exists(user_conversation_memory_file):
        logger.info(f"☁️ Memories found for: {user_name}")

        # Step 1: Read the original JSON file
        with open(user_conversation_memory_file, "r") as f:
            message_history_references = json.load(f)  # Loads existing list

        # Step 2: Append new info
        message_history_references.extend(conversation_data)
        # print(f"Memories: {message_history_references}")

        # Step 3: Save the updated data back to the same file
        with open(user_conversation_memory_file, "w") as f:
            json.dump(message_history_references, f, indent=4)  # Pretty print is optional

        logger.info(f"✅ Memories Saved")

    else:
        logger.warning(f"⚠️ Creating New Memories for: {user_name}")
        with open(user_conversation_memory_file, "w") as f:
            json.dump(conversation_data, f)
        f.close()


def remove_user_conversation_file(user_name):
    users_dir = os.path.join(memories_dir, 'users')
    user_folder = os.path.join(users_dir, user_name)

    # todo -- have it remove the faiss database as well
    outcome = faiss_index_delete(user_name)

    user_conversation_memory_file = os.path.join(user_folder, f"{user_name}.json")

    if os.path.exists(user_conversation_memory_file):
        os.remove(user_conversation_memory_file)
        return 1
    else:
        return -1

