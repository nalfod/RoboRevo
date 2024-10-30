from pathlib import Path

import speech_recognition as sr


class Listener:
    def __init__(self, key_loc: str | Path, mic_idx=0) -> None:
        self.key = self._load_key(key_loc)
        self.recognizer = sr.Recognizer()
        self.mic_idx = mic_idx
        with sr.Microphone(self.mic_idx) as source:
            self.recognizer.adjust_for_ambient_noise( source )
    
    def _load_key(self, key_loc: str) -> str:
        try:
            with Path(key_loc).open("r", encoding="utf-8") as key_file:
                key = key_file.readline()
            return key
        except FileNotFoundError as e: # TODO: this could be improved
            raise e("The location of the key file does not exist")
    
    def listen(self) -> str:
        with sr.Microphone(self.mic_idx) as source:
            print("say something")
            try:
                audio = self.recognizer.listen(source, timeout=7)
                print("Audio capturing is done!")
            except sr.WaitTimeoutError:
                print("Time out occured")
                return "Do nothing"
        
            try:
                result = self.recognizer.recognize_whisper_api(audio, api_key=self.key)
                print(f"You said {result}")
                return result
            except sr.UnknownValueError:
                print("Unknown error")
            except sr.RequestError as e:
                print(f"error: {e}")



if __name__ == "__main__":
    audio_recorder = Listener("../GPT/key.txt", 1)

    message = audio_recorder.listen()

    print(f"The message: {message}")