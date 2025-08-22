import os
import json

# get location of memories
running_dir = os.path.dirname(os.path.realpath(__file__))

# todo -- make these tool calls


def random_factoids():
    # get location of facts
    facts_location = os.path.join(running_dir, "__things_you_know.json")

    if not os.path.exists(facts_location):
        print("❌❌❌ Can not find Facts file!!")
        return ""

    # Load the existing data
    with open(facts_location, 'rb') as file:
        raw = file.read()

    # Decode properly, handling surrogates
    text = raw.decode("utf-8", "surrogatepass")

    # Now load JSON from string
    data = json.loads(text)

    # Join lines safely
    result = ' '.join(data)

    factoids = f"""Here is a few random facts you know: {result}"""
    return factoids


"""
NOTE: Handling emojis in JSON files

Problem:
- Some emojis, especially compound emojis like the trans pride flag 🏳️‍⚧️, are stored as
  UTF-16 surrogate pairs in JSON (e.g., '\uD83C\uDFF3\uFE0F\u200D⚧\uFE0F').
- Python's json.load() assumes UTF-8 and may not correctly combine these surrogate pairs,
  leading to mojibake like '🏳️‍âš§️' when printing.

Solution:
1. Read the JSON file as raw bytes to avoid early decoding issues.
2. Decode the bytes with 'utf-8' using the 'surrogatepass' error handler to preserve
   surrogate pairs.
3. Load the JSON from the decoded string using json.loads().
4. Joining or printing the resulting strings will now correctly display emojis.

Example:
with open("facts.json", "rb") as f:
    raw = f.read()
text = raw.decode("utf-8", "surrogatepass")
data = json.loads(text)
result = ' '.join(data)
print(result)  # Emojis print correctly, including compound ones
"""