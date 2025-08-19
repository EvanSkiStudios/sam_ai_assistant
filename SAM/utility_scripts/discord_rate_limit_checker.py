import os
import requests
import datetime

from dotenv import load_dotenv

# Load Env
load_dotenv()
BOT_TOKEN = os.getenv("TOKEN")
BOT_APPLICATION_ID = os.getenv("APPLICATION_ID")
BOT_SERVER_ID = os.getenv("SERVER_ID")
BOT_SERVER_CHANNEL_ID = os.getenv("GMCD_CHANNEL_ID")


def get_discord_rate_limit_headers(endpoint: str, token: str):
    url = f"https://discord.com/api/v10/{endpoint}"

    headers = {
        "Authorization": f"Bot {token}",
    }

    response = requests.get(url, headers=headers)

    rate_limit_headers = {}
    for key, value in response.headers.items():
        if key.lower().startswith("x-ratelimit"):
            # Special handling for "X-RateLimit-Reset"
            if key.lower() == "x-ratelimit-reset":
                try:
                    epoch_time = float(value)
                    readable_time = datetime.datetime.fromtimestamp(epoch_time, datetime.UTC)
                    rate_limit_headers[key] = readable_time
                except ValueError:
                    rate_limit_headers[key] = value  # fallback
            else:
                rate_limit_headers[key] = value

    return rate_limit_headers


# Example usage:
if __name__ == "__main__":
    # Replace with your bot token and a valid endpoint (e.g., "users/@me")
    # endpoint = f"channels/{BOT_SERVER_CHANNEL_ID}/messages"
    endpoint = f"users/@me"

    headers = get_discord_rate_limit_headers(endpoint, BOT_TOKEN)
    for k, v in headers.items():
        print(f"{k}: {v}")
