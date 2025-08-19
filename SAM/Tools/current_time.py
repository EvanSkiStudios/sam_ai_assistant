import ollama
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Callable

def get_current_time() -> str:
    now = datetime.now()
    time = now.strftime("%I:%M %p")
    return str(time)


def get_current_date() -> str:
    now = datetime.now()
    date = now.strftime("%B %d, %Y")
    return str(date)


def get_future_datetime(days=0, hours=0, minutes=0, seconds=0, base_time=None) -> str:
    """
    Returns a datetime object representing the time offset from a given base_time (default is now).

    Parameters:
        days (int): Number of days to add.
        hours (int): Number of hours to add.
        minutes (int): Number of minutes to add.
        seconds (int): Number of seconds to add.
        base_time (datetime, optional): Starting point for the calculation. Defaults to now.

    Returns:
        datetime: The future datetime after applying the offset.
    """
    if base_time is None:
        base_time = datetime.now()

    offset = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    return str(base_time + offset)


async def main():
    client = ollama.AsyncClient()

    prompt = 'What is the current date?'

    available_functions: Dict[str, Callable] = {
        'get_current_time': get_current_time,
        'get_current_date': get_current_date,
    }

    response = await client.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}],
        tools=[get_current_time]
    )

    print(response.message)

    if response.message.tool_calls:
        for tool in response.message.tool_calls:
            if function_to_call := available_functions.get(tool.function.name):
                print('Calling function:', tool.function.name)
                print('Arguments:', tool.function.arguments)
                function_output = function_to_call(**tool.function.arguments)
                print('Function output:', function_output)
            else:
                print('Function', tool.function.name, 'not found')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\nGoodbye!')
