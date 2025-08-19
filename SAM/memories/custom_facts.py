import os
import json

# get location of memories
running_dir = os.path.dirname(os.path.realpath(__file__))


def random_factoids():
    # get location of facts
    facts_location = os.path.join(running_dir, "__things_you_know.json")

    if not os.path.exists(facts_location):
        print("❌❌❌ Can not find Facts file!!")
        return ""

        # Load the existing data
    with open(facts_location, 'r') as file:
        data = json.load(file)

    result = ''.join(line .strip() for line in data)

    factoids = "Here is a few random facts you know: " + result
    return factoids
