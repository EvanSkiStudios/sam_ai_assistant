import time
from datetime import datetime
from utility_scripts.system_logging import setup_logger

# configure logging
logger = setup_logger(__name__)

# used for limited responses to bots
bot_reply_timeout = {}
MAX_MESSAGES = 3
COOLDOWN_SECONDS = 60


def handle_bot_message(username):
    now = time.time()

    # Initialize user if not exists
    if username not in bot_reply_timeout:
        bot_reply_timeout[username] = {
            "message_count": 1,
            "cooldown_until": 0
        }
        return 0

    user_data = bot_reply_timeout[username]

    # Check if cooldown is active
    if now < user_data["cooldown_until"]:
        cooldown_time = datetime.fromtimestamp(user_data['cooldown_until'])
        formatted_time = cooldown_time.strftime('%I:%M %p')  # 12-hour:Minute AM/PM
        logger.warning(f"{username} is on cooldown until {formatted_time}")
        return -1

    # Reset message count if cooldown has expired
    if user_data["cooldown_until"] != 0 and now >= user_data["cooldown_until"]:
        user_data["message_count"] = 0
        user_data["cooldown_until"] = 0

    # Increment message count
    user_data["message_count"] += 1

    # Trigger cooldown if message count exceeds MAX_MESSAGES
    if user_data["message_count"] > MAX_MESSAGES:
        user_data["cooldown_until"] = now + COOLDOWN_SECONDS
        user_data["message_count"] = 0
        logger.warning(f"{username} is now on cooldown for {COOLDOWN_SECONDS} seconds.")
    else:
        logger.info(f"{username} message count: {user_data['message_count']}")

    return 0
