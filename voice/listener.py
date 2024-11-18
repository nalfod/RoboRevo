from pathlib import Path
import threading
import speech_recognition as sr
import time


class Listener:
    def __init__(self, key_loc: str | Path, mic_idx=0) -> None:
        self.key = self._load_key(key_loc)
        self.recognizer = sr.Recognizer()
        self.mic_idx = mic_idx
        self.recognizer.dynamic_energy_threshold = False
        # print(f"My dynamic energy threshold value is= {self.recognizer.dynamic_energy_threshold}")         
    
    def _load_key(self, key_loc: str) -> str:
        try:
            with Path(key_loc).open("r", encoding="utf-8") as key_file:
                key = key_file.readline()
            return key
        except FileNotFoundError as e: # TODO: this could be improved
            raise e("The location of the key file does not exist")
    
    def listen(self) -> str:
        with sr.Microphone(self.mic_idx) as source:
            is_there_an_error = False
            self.recognizer.adjust_for_ambient_noise( source, duration= 0.2 )
            # magic number, almost completly randomly determined.....
            self.recognizer.energy_threshold *= 3
            print(f"say something, current adjusted energy threshold limit= {self.recognizer.energy_threshold}")
            try:
                print("Starting audio capturing")
                audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=20)
                # audio = self.call_with_timeout(self.recognizer.listen, 1, source)
                # audio = self.call_with_timeout(Listener._print_on_console, 3, source)
                print("Audio capturing is done!")
            except RuntimeError as e:
                print(f"RuntimeError occured: {e}")
                is_there_an_error = True
            except Exception as e:
                print(f"Other kind of error occured: {e}")
                is_there_an_error = True
        
            if not is_there_an_error:
                try:
                    result = self.recognizer.recognize_whisper_api(audio, api_key=self.key)
                    print(f"You said {result}")
                    return result
                except sr.UnknownValueError:
                    print("Unknown error")
                    is_there_an_error = True
                except sr.RequestError as e:
                    print(f"error: {e}")
                    is_there_an_error = True

            if not is_there_an_error:
                return result
            else:
                raise RuntimeError()

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
                print("Starting listening in the wrapper function")
                result["status"] = func(*args, **kwargs)
                print("Listening is succesful!")
            except Exception as e:
                print(f"Function raised an excpetion: {e}")
                result["status"] = "Function raised an exception"
            print("Wrapper ends!")

        # Run the function in a separate thread
        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()

        # Wait for the thread to finish or timeout
        thread.join(timeout)

        if thread.is_alive():
            print("Timeout reached! Moving forward with error...")
            thread.join(0)
            raise RuntimeError("Timeout!!")
        else:
            thread.join(0)
            if result["status"] == "Function raised an exception":
                raise RuntimeError("Other error")
            else:
                return result["status"]

    # ONLY FOR DEBUGGING        
    @staticmethod
    def _print_on_console(*args, **kwargs):
        while True:
            print(f"     I am a mock function and I am running...")
            time.sleep(1)

if __name__ == "__main__":
    audio_recorder = Listener("../GPT/key.txt", 0)

    try:
        message = audio_recorder.listen()
        print(f"listener.main - The message: {message}")
    except:
        print("listener.main - An error happened, sorry.")