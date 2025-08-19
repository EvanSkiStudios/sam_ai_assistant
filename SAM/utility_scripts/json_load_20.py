import os
from pathlib import Path

import ijson
from collections import deque


def json_get_last_n(filename, n=20):
    dq = deque(maxlen=n)
    with open(filename, "r") as f:
        for obj in ijson.items(f, "item"):
            dq.append(obj)
    return list(dq)


def main():
    user_name = 'evanski_'
    parent_dir = Path(__file__).resolve().parent.parent
    memories_dir = os.path.join(parent_dir, 'memories')
    users_dir = os.path.join(memories_dir, 'users')
    user_folder = os.path.join(users_dir, user_name)

    user_file = os.path.join(user_folder, f'{user_name}.json')

    last_20 = json_get_last_n(user_file, 20)
    print(last_20)


if __name__ == "__main__":
    main()
