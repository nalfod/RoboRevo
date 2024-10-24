from pathlib import Path

import speech_recognition as sr


class Listener:
    def __init__(self, key_loc: str | Path) -> None:
        self.key = self._load_key(key_loc)
        self.recognizer = sr.Recognizer()
    
    def _load_key(self, key_loc: str) -> str:
        try:
            with Path(key_loc).open("r", encoding="utf-8") as key_file:
                key = key_file.readline()
            return key
        except FileNotFoundError as e: # TODO: this could be improved
            raise e("The location of the key file does not exist")
    
    def listen(self) -> str:
        with sr.Microphone() as source:
            print("say something")
            audio = self.recognizer.listen(source)
        
            try:
                result = self.recognizer.recognize_whisper_api(audio, api_key=self.key)
                print(f"You said {result}")
                return result
            except sr.UnknownValueError:
                print("fos")
            except sr.RequestError as e:
                print(f"error: {e}")
