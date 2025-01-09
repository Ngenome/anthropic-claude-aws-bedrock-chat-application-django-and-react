from openai import OpenAI
client = OpenAI()


def call_llm(system_message, messages):
    # the messages passed in the function are an array of strings,format the messages to be in the object that GPT-3.5-turbo API expects
    # format the messages to be in the object that GPT-3.5-turbo API expects
    formatted_messages = []
    for message in messages:
        formatted_messages.append({"role": "user", "content": message})

    # concatenate the system message to the messages,the system message is the first message in the array
    final_messages = [{"role": "system", "content": system_message}] + formatted_messages


    response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=final_messages,)
    return response.choices[0].message.content