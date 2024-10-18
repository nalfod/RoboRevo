from openai import OpenAI

client = OpenAI(api_key)

session = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {
            "role": "user",
            "content": "Write me a for loop that interates through a list of integers from 1 to 10 in python."
        }
    ]
)

response = session.choices[0].message.content

print(response)
