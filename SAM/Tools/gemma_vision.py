import asyncio
import os
import requests

from ollama import Client, chat, ChatResponse, AsyncClient
from pathlib import Path
from urllib.parse import urlparse

# set image directory
parent_dir = Path(__file__).resolve().parent.parent
image_dir_path = parent_dir / 'images' / ''


def image_cleanup(image):
    parent_dir = Path(__file__).resolve().parent.parent
    path = parent_dir / 'images' / image

    if os.path.exists(path):
        os.remove(path)


def download_image(url):
    dest_folder = image_dir_path

    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)  # create folder if it does not exist

    # extract filename safely without query params
    path = urlparse(url).path
    filename = os.path.basename(path).replace(" ", "_")
    file_path = os.path.join(dest_folder, filename)

    r = requests.get(url, stream=True)
    if r.ok:
        output_path = os.path.abspath(file_path)
        print("saving to", output_path)
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
        return filename
    else:  # HTTP status code 4XX/5XX
        print("Download failed: status code {}\n{}".format(r.status_code, r.text))
        return None


async def gemma3_image_recognition(image_file_name):
    # Go one directory up
    parent_dir = Path(__file__).resolve().parent.parent
    path = parent_dir / 'images' / image_file_name

    client = AsyncClient()

    print(f'Analyzing image ({image_file_name})...')
    response = await client.chat(
        model='gemma3',
        messages=[
            {"role": "system", "content": 'The user will provide you with an image. You will analyze the image and return a detailed description of the image.'},
            {
               "role": "user",
               "content": 'Analyze this image and return a detailed description of the image. Give only the description as your response.',
               'images': [path],
            }
        ],
        options={'temperature': 0},  # Make responses more deterministic
    )

    output = response.message.content
    output = output.replace("'", "").strip()
    # print(output)
    return output


async def image_recognition(url):
    mypath = download_image(url)
    if mypath == -1:
        print('Image Error')
        return -1
    else:
        text = await gemma3_image_recognition(mypath)
        print(f'Finished Image Vision!')
        image_cleanup(mypath)
        return text

