import asyncio
import os
import discord

import discord_commands as bc

from discord.ext import commands
from dotenv import load_dotenv

from emoji_reactions_manager import llm_emoji_react_to_message, gather_server_emotes
from flukebot import Flukebot_Create, Flukebot_Message

# Load Env
load_dotenv()
BOT_TOKEN = os.getenv("TOKEN")
BOT_APPLICATION_ID = os.getenv("APPLICATION_ID")
BOT_SERVER_ID = os.getenv("GMCD_SERVER_ID")
BOT_TEST_SERVER_ID = os.getenv("TEST_SERVER_ID")
BOT_DM_CHANNEL_ID = os.getenv("DM_CHANNEL_ID")
BOT_CHANNEL_ID = os.getenv("GMCD_CHANNEL_ID")
GMC_DISCUSSION_THREAD = os.getenv("GMCD_NOT_ALLOWED_THREAD_D")
GMC_NO_CONTEXT_THREAD = os.getenv("GMCD_NOT_ALLOWED_THREAD_NC")

# set discord intents
intents = discord.Intents.default()
intents.message_content = True
intents.emojis = True
intents.emojis_and_stickers = True

activity_status = bc.command_set_activity()

command_prefix = "$fb "
client = commands.Bot(
    command_prefix=command_prefix,
    intents=intents,
    activity=activity_status,
    status=discord.Status.online
)

emote_dict = {}


class MyHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        help_message = """
For Full documentation see: [The Github Repo](<https://github.com/EvanSkiStudios/flukebot>)
Commands are issued like so: `$fb <command> <argument>`
```Here are my commands:
"""
        for cog, commands_list in mapping.items():
            for command in commands_list:
                help_message += f"`{command.name}` - {command.help or 'No description'}\n"
        help_message += "```"
        await self.get_destination().send(help_message)


# assign help command from bot_commands
client.help_command = MyHelpCommand()

# Startup LLM
Flukebot_Create()


# --------- BOT EVENTS ---------
@client.event
async def on_ready():
    # When the bot has logged in, call back
    print(f'We have logged in as {client.user}')


@client.event
async def on_disconnect():
    print(f"{client.user} disconnected!")


@client.event
async def on_connect():
    activity = bc.command_set_activity()
    new_status = discord.Status.online
    await client.change_presence(activity=activity, status=new_status)

    global emote_dict
    emote_dict = gather_server_emotes(client, BOT_SERVER_ID, BOT_TEST_SERVER_ID)


@client.event
async def on_close():
    print(f"{client.user} closed!")


# ------- BOT COMMANDS ----------
@client.command(help="Changes Status to random or supplied custom")
async def status(ctx, *, arg=None):
    await bc.command_status(client, ctx, arg)


@client.command(help="Sets the conversation history between you and FlukeBot, depending on the argument")
async def history(ctx, arg=None):
    await bc.command_history(ctx, arg)


@client.command(help="Deletes the supplied Flukebot messages by id")
async def delete(ctx, *, arg=None):
    await bc.command_delete(client, ctx, arg)


@client.command(help="Sanity Check for input")
async def ping(ctx, *, arg=None):
    await ctx.send(f"Pong!")


# ------- MESSAGE HANDLERS ---------
async def llm_chat(message, username, user_nickname, message_content):
    async with message.channel.typing():
        attachment_url = None
        attachments = None
        if message.attachments:
            for media in message.attachments:
                content_type = str(media.content_type).lower()
                # print(content_type)
                attachment_url = media.url if content_type in ("image/png", "image/jpeg", "image/webp") else None
                # Unhandled formats will give  (status code: 500) from the bot
                attachments = message.attachments
                # currently only looks at one image if there are multiple
            # print(message.content) # gifs from the panel are just message content - currently cant see gifs anyway

        response = await Flukebot_Message(username, user_nickname, message_content, attachment_url, attachments)

    if response == -1:
        return

    for i, part in enumerate(response):
        if not message.author.bot and i == 0:
            await message.reply(part)
        else:
            await message.channel.send(part)


async def react_to_messages(message, message_lower):
    global emote_dict

    try:
        # reaction
        reaction = await llm_emoji_react_to_message(message_lower, emote_dict)

        # discord limits by 20 reactions
        limit = 20
        reaction = reaction[:limit]
        for emoji in reaction:
            if emoji.find('no reaction') == -1:
                await message.add_reaction(emoji)

    except discord.HTTPException as e:
        print(f"⚠️ {type(e).__name__} - {e}")
        pass  # Suppresses all API-related errors (e.g., invalid emoji, rate limit)


channels_blacklist = [GMC_DISCUSSION_THREAD, GMC_NO_CONTEXT_THREAD]


@client.event
async def on_message(message):
    await client.process_commands(message)  # This line is required!

    message_lower = message.content.lower()
    username = message.author.name
    user_nickname = message.author.display_name

    if message.mention_everyone:
        return
    if message_lower.find(command_prefix) != -1:
        return

    # if str(message.channel.id) == BOT_CHANNEL_ID:
        # noinspection PyAsyncCall
        # asyncio.create_task(summarize_chat(username, message.content))

    if message.author == client.user:
        return

    # noinspection PyAsyncCall
    asyncio.create_task(react_to_messages(message, message_lower))
    # task.add_done_callback(lambda t: t.exception())  # Prevent warning if task crashes
    #  -- Its fine we don't care if it returns

    if str(message.channel.id) in channels_blacklist:
        return

    # DMs
    if isinstance(message.channel, discord.DMChannel):
        # print(f"{message_content}")

        if message_lower.find('save history') != -1:
            output = await bc.command_save_history(username)
            await message.channel.send(output)
            return

        if message_lower.find('delete history') != -1:
            output = await bc.command_delete_history(username)
            await message.channel.send(output)
            return

        await llm_chat(message, username, user_nickname, message_lower)
        return

    # replying to bot directly
    if message.reference:
        referenced_message = await message.channel.fetch_message(message.reference.message_id)
        if referenced_message.author == client.user:
            message_content = message_lower.replace(f"<@{BOT_APPLICATION_ID}>", "")
            await llm_chat(message, username, user_nickname, message_content)
            return

    # Pinging the bot
    if message_lower.find(str(BOT_APPLICATION_ID)) != -1:
        message_content = message_lower.replace(f"<@{BOT_APPLICATION_ID}> ", "")
        await llm_chat(message, username, user_nickname, message_content)
        return

    # if the message includes "flukebot" it will trigger and run the code
    if message_lower.find('flukebot') != -1:
        await llm_chat(message, username, user_nickname, message_lower)
        return


# Startup discord Bot
client.run(BOT_TOKEN)
