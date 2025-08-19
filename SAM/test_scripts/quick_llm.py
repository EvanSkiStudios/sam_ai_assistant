from ollama import Client, chat, ChatResponse, AsyncClient


async def quick_LLM(system, prompt):
    client = AsyncClient()

    response = await client.chat(
        model='llama3.2',
        messages=[
           {"role": "system", "content": system},
           {"role": "user", "content": prompt}
        ],
        # options={'temperature': 0},  # Make responses more deterministic
    )

    output = response.message.content
    output = output.replace("'", "").strip()
    print(output)
    return output
