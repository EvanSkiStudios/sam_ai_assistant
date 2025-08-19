import asyncio

from ollama import Client, chat, ChatResponse, AsyncClient
from pathlib import Path


async def main():
    # Go one directory up
    parent_dir = Path(__file__).resolve().parent.parent
    path = parent_dir / 'images' / 'mercanski.jpg'

    client = AsyncClient()

    response = await client.chat(
        model='gemma3',
        messages=[
            {"role": "system", "content": 'The user will provide you with an image. You will analyze the image and return a detailed description.'},
            {
               "role": "user",
               "content": 'Analyze this image and return a detailed description.',
               'images': [path],
            }
        ],
        options={'temperature': 0},  # Make responses more deterministic
    )

    output = response.message.content
    output = output.replace("'", "").strip()
    print(output)
    return output


if __name__ == "__main__":
    asyncio.run(main())
