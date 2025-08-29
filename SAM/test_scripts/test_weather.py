import ollama
import json


# Define a fake tool
def get_weather(city: str):
    return f"The weather in {city} is sunny and 25°C."


# Step 1: Ask the model to decide
response = ollama.chat(
    model="llama3.2",
    messages=[
        {"role": "system",
         "content": "You can call tools by outputting JSON in the format {\"tool\": ..., \"args\": {...}}."},
        {"role": "user", "content": "What’s the weather in Paris?"}
    ],
    tools=[get_weather]
)

message = response["message"]["content"]
print("Model said:", message)

# Step 2: Try to parse JSON for a tool call
try:
    tool_request = json.loads(message)
    if "tool" in tool_request:
        if tool_request["tool"] == "get_weather":
            result = get_weather(**tool_request["args"])

            # Step 3: Return the tool’s result back to the model
            followup = ollama.chat(
                model="llama3.2",
                messages=[
                    {"role": "system", "content": "You are assisting with tool outputs."},
                    {"role": "user", "content": f"Tool result: {result}"}
                ]
            )
            print("Final answer:", followup["message"]["content"])
except json.JSONDecodeError:
    print("No tool call detected.")