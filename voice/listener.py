from pathlib import Path
import threading
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
                print("Starting audio capturing")
                # audio = self.recognizer.listen(source, timeout=7)
                audio = self.call_with_timeout(self.recognizer.listen, 10, source)
                print("Audio capturing is done!")
            except RuntimeError:
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

    def call_with_timeout(self, func, timeout, *args, **kwargs):
        """
        Calls a function and enforces a timeout.
        
        Args:
            func: The function to call.
            timeout: Maximum time (in seconds) to wait for the function.
            *args, **kwargs: Arguments to pass to the function.
        
        Returns:
            str: Result or error message if timed out.
        """
        result = {"status": None}  # Use a mutable type to store results across threads.

        def wrapper():
            try:
                result["status"] = func(*args, **kwargs)
            except Exception as e:
                result["status"] = "Function raised an exception"

        # Run the function in a separate thread
        thread = threading.Thread(target=wrapper)
        thread.start()

        # Wait for the thread to finish or timeout
        thread.join(timeout)

        if thread.is_alive():
            print("Timeout reached! Moving forward with error...")
            thread.join(0)
            raise RuntimeError("Timeout!!")
        else:
            if result["status"] == "Function raised an exception":
                raise RuntimeError("Other error")
            else:
                return result["status"]



if __name__ == "__main__":
    audio_recorder = Listener("../GPT/key.txt", 0)

    message = audio_recorder.listen()

    print(f"The message: {message}")