# used for getting information about chatter, https://youtu.be/3j8Fc59bFsE?t=11

import os
import json


# get location of details
running_dir = os.path.dirname(os.path.realpath(__file__))
memories_location = os.path.join(running_dir, "meet_the_robinsons")


def fetch_chatter_description(username):
    user_details_file = os.path.join(memories_location, f"{username}.json")

    if not os.path.exists(user_details_file):
        print(f'⚠️ No User Details for {username}')
        return ""

    user_detail_string = f"Use this information about {username} when speaking to them: "

    # Load the message history
    with open(user_details_file, "r") as f:
        user_details = json.load(f)

    # Join all strings into one
    combined_details = " ".join(user_details)
    return user_detail_string + combined_details
