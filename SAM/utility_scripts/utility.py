import datetime


def split_response(response, max_len=2000):
    if len(response) < 2000:
        return [response]

    chunks = []
    while len(response) > max_len:
        # Find the last space or line break within the first max_len characters
        split_index = max(response.rfind(' ', 0, max_len), response.rfind('\n', 0, max_len))
        if split_index == -1:
            # If no space or newline is found, just split at max_len
            split_index = max_len
        chunks.append(response[:split_index].rstrip())
        response = response[split_index:].lstrip()
    if response:
        chunks.append(response)
    return chunks


# Get current date and time
def current_date_time():
    now = datetime.datetime.now()
    date = now.strftime("%B %d, %Y")
    time = now.strftime("%I:%M %p")

    return f"The current date is {date}. The current time is {time}."
