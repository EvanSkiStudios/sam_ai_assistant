import emoji
import regex
from ollama import Client, chat, ChatResponse, AsyncClient


def is_emoji(text):
    """
    Checks if a string is an emoji.

    Args:
    text: The string to check.

    Returns:
    True if the string is an emoji, False otherwise.
    """
    return text in emoji.EMOJI_DATA


def extract_emojis_and_words(text):
    clusters = regex.findall(r'\X', text)

    result = []
    buffer = ""
    for cluster in clusters:
        if regex.search(r'\p{Emoji}', cluster):
            # flush buffer before adding emoji
            if buffer:
                result.append(buffer)
                buffer = ""
            result.append(cluster)
        elif not cluster.isspace():
            buffer += cluster
        else:
            # flush buffer before whitespace
            if buffer:
                result.append(buffer)
                buffer = ""
    if buffer:
        result.append(buffer)

    return result


def clean_split(s):
    # Get tokens
    tokens = extract_emojis_and_words(s)

    # Strip whitespace tokens and remove empty ones
    return [t for t in tokens if not t.isspace() and t != '']


dictation_rules = (
    "You are a simple input output machine. \
    The user will feed you a chat message. If you feel strongly about the message, \
    reply with a single or multiple emojis. Otherwise, respond with \"No reaction\". \
    You do not have to respond, you can just give \"No reaction\". \
    You are only allowed to speak with emoji or only \"No reaction\". \
    Try to keep the max amount emojis in a response to 3 at most."
)

custom_emojis = """
Along with the normal emojis, you may also respond with any of the names of an special emoji in the following list:
- 'sqrbt_angry' Description: image of a minecraft character being angry,
- 'gms' Description: the logo of the company YoYo Games,
- 'roy' Description: an image of an early internet meme known as "awesome face",
- 'spam' Description: an image of a can of SPAM,
- 'lenny' Description: an all black image of '( ͡° ͜ʖ ͡°)', 
- 'clown_click' Description: image of the face of a clown,
- 'lenny2' Description: an all black with white outline image of '( ͡° ͜ʖ ͡°)', 
- 'lenny3' Description: an all white image of '( ͡° ͜ʖ ͡°)', 
- 'chronicon' Description: a pixel art image of an fantasy knight,
- 'homestead' Description: a image of a turnip,
- 'helsmeme' Description: a image of a anime girl with underwear on her head,
- 'kousenai' Description: a image of a japanese letter,
- 'tsukastupid' Description: a image of a anime girl looking bewildered,
- 'gm' Description: a image of a the notorious gamemaker smily cog logo,
- 'lukasmah' Description: a image of a the soviet union logo,
- 'pacha5' Description: a image of the pacha 'just right' meme from emperor's new groove,
- 'pacha4' Description: a split image of the pacha 'just right' meme from emperor's new groove this is the bottom right peice,
- 'pacha3' Description: a split image of the pacha 'just right' meme from emperor's new groove this is the bottom left peice,
- 'pacha1' Description: a split image of the pacha 'just right' meme from emperor's new groove this is the top left peice,
- 'pacha2' Description: a split image of the pacha 'just right' meme from emperor's new groove this is the top right peice,
- 'flutist' Description: a pixel art image of a jazz player,
- 'yok' Description: a ms paint image of a face,
- 'bunker' Description: a pixel art image of an man,
- 'heynow' Description: a image of a persons face looking concerned,
- 'bean' Description: a image of a bean,
- 'kepons' Description: a image of a pear,
- 'tyrion' Description: a image of Tyrion Lannister from game of thrones looking angry,
- 'trump' Description: a image of donald trump making a funny face,
- 'barvhoodie' Description: a ms paint image of guy in a hoodie looking disinterested,
- 'plaxus' Description: a image of a squid,
- 'downvote' Description: a image of red down arrow,
- 'upvote' Description: a image of green up arrow,
- 'misu' Description: a image of a cat making a happy face,
- 'stopthat' Description: a image of velma from scooby-doo saying 'stop that',
- 'fingerguns' Description: a image of a smirk emoji with finger guns',
- 'thisisfine' Description: a image of the 'this is fine' meme,
- 'vsauce' Description: a image of vsauce michael's face,
- 'stopclowning' Description: a image of an annoyed clown,
- 'russiagm' Description: a image of a the notorious gamemaker smily cog logo wearing a cowboy outfit,
- 'bothvote' Description: a image of split in half with a green up vote arrow and a red down vote arrow,
- 'enragementcat' Description: a ms paint image of a cat looking excited,
- 'idkimjustacat' Description: a image of a cat face with its tongue out,
- 'summface' Description: a horribly drawn image of a smile face,
- 'NN' Description: a image of super mario's face,
- 'bonk1' Description: a image of a shiba inu sitting funny,
- 'bonk2' Description: a image of a shiba inu sitting funny with a baseball bat the 'bonk' meme,
- 'gmscog' Description: a image of the green gamemaker cog logo,
- 'gmhammer' Description: a image of the red gamemaker hammer logo,
- 'gms2' Description: a image of the gamemaker studio logo,
- 'emoji_50' Description: a image of the gamemaker cog logo that looks like a green snake,
- 'dancing_raccoon' Description: a image of a dancing raccoon,
- 'bongo_raccoon' Description: a image of a raccoon waving their hands
"""

reconfirmation = """
To use one of these special emoji's instead simply respond with the name of the emoji in the list.
or just respond with a normal emoji or \"No reaction\".
So your response should be only emojis, the name of a special emoji, or \"No reaction\".
"""

emoji_llm = 'llama3.2'

system_prompt = f"""{dictation_rules}
{custom_emojis}
{reconfirmation}"""


async def llm_emoji_react_to_message(content, emote_dict):
    client = AsyncClient()
    response = await client.chat(
        model=emoji_llm,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ],
        options={'temperature': 0.2},  # Make responses less or more deterministic
    )

    output = response.message.content
    output = output.replace("'", "").strip()

    # print(content)
    # print(output)

    if output.lower() == "no reaction":
        output = ""

    # print(output)

    # split response into an array
    emoji_list = clean_split(output)
    # print(emoji_list)

    reaction_list = []
    for emote in emoji_list:

        # check if it's a normal emoji
        if is_emoji(emote):
            reaction_list.append(emote)
            continue

        # if it's not check if it's a special emoji
        custom_emoji = emote_dict.get(emote)
        if custom_emoji is not None:
            custom_emote = f'<a:{emote}:{custom_emoji}>'
            reaction_list.append(custom_emote)
            continue

        # finally just do no reaction as its garbage
        reaction_list.append("no reaction")
    return reaction_list


def gather_server_emotes(client, bot_server_id, test_server_id):
    emote_dict = {}
    guild = client.get_guild(int(bot_server_id))
    if guild is not None:
        for emote in guild.emojis:
            emote_dict[emote.name] = emote.id

    # hack for another server list of emojis
    guild = client.get_guild(int(test_server_id))
    if guild is not None:
        for emote in guild.emojis:
            emote_dict[emote.name] = emote.id

    # print(emote_dict)
    return emote_dict
