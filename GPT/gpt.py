from openai import OpenAI
from pathlib import Path


class GPT:
    def __init__(self, key_loc: str, ) -> None:
        self.key = self._load_key(key_loc)
        self.client = OpenAI(api_key=self.key)

    def _load_key(self, key_loc) -> str:
        try:
            with Path(key_loc).open("r", encoding="utf-8") as key_file:
                key = key_file.readline()
            return key
        except FileNotFoundError as e: # TODO: this could be improved
            raise e("The location of the key file does not exist")

    def request(self, message: str) -> str:
        session = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages = [
                {
                    "role": "user",
                    "content": f"{message}. Don't give any explanation, just the code section for the request."
                }
            ],
            stream=False
        )

        response = session.choices[0].message.content

        return response