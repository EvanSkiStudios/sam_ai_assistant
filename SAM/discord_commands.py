import json
import os
import random
import discord

from memories.message_memory_manager import remove_user_conversation_file


def command_set_activity(current_activity=None):
    possible_activities = [
        discord.Game(name="Hello Kitty Island Adventure", platform="steam", type=discord.ActivityType.playing),
        discord.Streaming(name="Memes", url="https://www.twitch.tv/evanskistudios"),
        discord.Activity(type=discord.ActivityType.listening, name='Never Gonna Give You Up'),
        discord.Activity(type=discord.ActivityType.watching, name="Shrek 7"),
        discord.CustomActivity(name="Cheering Alyssa on!", emoji="🥳"),
        discord.CustomActivity(name="<coroutine object S.A.M at 0x000001AB2C3D4567>", emoji="😘"),
        discord.CustomActivity(name="Fantasising about Rick Astley", emoji="😳"),
        None  # Clear status
    ]

    # Remove the current activity from the list if it matches
    if current_activity in possible_activities:
        possible_activities.remove(current_activity)

    # Pick a new one randomly from the rest
    return random.choice(possible_activities)


def discord_activity_mapper(activity):
    activity_type_map = {
        discord.ActivityType.playing: "playing",
        discord.ActivityType.streaming: "streaming",
        discord.ActivityType.listening: "listening to",
        discord.ActivityType.watching: "watching",
        discord.ActivityType.competing: "competing in",
        discord.ActivityType.custom: "Custom"
    }
    return activity_type_map.get(activity.type, f"Unknown({activity.type.name.lower()})")


async def command_status(client, ctx, arg):
    print(f"Command issued: Status")

    # set the status to custom if supplied otherwise get a random one from the list in set_activity
    if arg is not None:
        # max character limit
        arg = arg[:128]
        activity = discord.CustomActivity(name=f"{arg}", emoji=' ')
        await client.change_presence(activity=activity)
    else:
        activity = command_set_activity(client.activity)
        await client.change_presence(activity=activity)

    # Get the new activity to respond with the new info about the status
    if activity is not None:
        if activity.type == discord.ActivityType.custom:
            await ctx.send(f"Custom Status is now: {activity.name}")
        else:
            await ctx.send(f"Status is now: {discord_activity_mapper(activity)} {activity.name}")
    else:
        await ctx.send("Status has been cleared.")
        print("Status Cleared")
        return

    print(f"Changed Status to: {activity.type} {activity.name}")


def convo_delete_history(username):
    result = remove_user_conversation_file(username)
    return result


async def command_history(ctx, arg):
    print(f"Command issued: history > {arg}")
    if arg is not None:
        arg = arg.lower()

    if arg == "save":
        information_message = """
In order to save conversation history I require consent to save your discord messages.
Only the messages you send to me will be saved and only used to remember details and conversation history.
Your conversation history is never sold or given to anyone or any 3rd party.
At any point you can run the command "$s clearhistory" to remove your conversation history.
Please send me a DM with "save history" to opt in. or "delete history" to opt out.
"""
        await ctx.reply(ctx.author.mention + information_message)
        return

    if arg == "delete":
        user = ctx.author.name
        outcome = convo_delete_history(user)
        outcome_message = "Unknown Error, Try again later!"

        if outcome == 1:
            print(f"Deleted Conversation history for {user}")
            outcome_message = f"Deleted Conversation history for {user}"

        if outcome == -1:
            print(f"No Conversation history for {user}")
            outcome_message = f"No Conversation history for {user}"

        await ctx.send(outcome_message)
        return

    await ctx.reply(f"{arg} is not valid argument for history command <save/delete>")


async def command_save_history(user):
    # get location of consent file
    running_dir = os.path.dirname(os.path.realpath(__file__))
    file_location = str(running_dir) + "/memories/"
    consent_file = os.path.join(file_location, "__consent_users.json")

    if not os.path.exists(consent_file):
        print("❌❌❌ Can not find user consent file!!")
        return "unexpected Error Please Try again later"

    # Load the message history
    with open(consent_file, "r") as f:
        file_data = json.load(f)

    # add user to list
    if str(user) not in file_data:
        file_data.append(str(user))

        # Save the updated data back to the file
        with open(consent_file, 'w') as file:
            json.dump(file_data, file, indent=4)

    return (
        "Your conversation history will now be saved.\nAt anytime send me 'delete history' to opt out.\nPlease also "
        "see the command to delete conversation history by using '$fb help'")


async def command_delete_history(user):
    # get location of consent file
    running_dir = os.path.dirname(os.path.realpath(__file__))
    file_location = str(running_dir) + "/memories/"
    consent_file = os.path.join(file_location, "__consent_users.json")

    if not os.path.exists(consent_file):
        print("❌❌❌ Can not find user consent file!!")
        return "unexpected Error Please Try again later"

    # Load the existing data
    with open(consent_file, 'r') as file:
        data = json.load(file)

    # Remove "dave" if it exists
    if str(user) in data:
        data.remove(str(user))

    # Save the updated data back to the file
    with open(consent_file, 'w') as file:
        json.dump(data, file, indent=4)

    return_message = "You have been removed from the history collection list"

    outcome = convo_delete_history(user)
    outcome_message = "Unknown Error with current conversation history, Try again later!"

    if outcome == 1:
        outcome_message = "Conversation History has been deleted"

    if outcome == -1:
        outcome_message = ("Conversation History might not exist or an Error Occurred, Please Contact Evanski to have "
                           "your history deleted")

    return return_message + "\n" + outcome_message


async def command_delete(client, ctx, arg):
    messages = arg.split(',')

    deleted = []
    failed = []

    for msg_id in messages:
        try:
            msg_id = int(msg_id)
            msg = await ctx.channel.fetch_message(msg_id)
            if msg.author == client.user:
                await msg.delete()
                deleted.append(msg_id)
            else:
                failed.append((msg_id, "Not sent by bot"))
        except discord.NotFound:
            failed.append((msg_id, "Message not found"))
        except discord.Forbidden:
            failed.append((msg_id, "Missing permissions"))
        except discord.HTTPException as e:
            failed.append((msg_id, f"HTTP error: {e}"))

    report = []
    if deleted:
        report.append(f"✅ Deleted: {', '.join(map(str, deleted))}")
    if failed:
        report.append("❌ Failed:\n" + "\n".join(f"{i}: {reason}" for i, reason in failed))

    print(report)
    await ctx.send("Deleted: (" + str(len(deleted)) + ") Messages", delete_after=10)


