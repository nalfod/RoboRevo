import speech_recognition as sr

r = sr.Recognizer()
with sr.Microphone() as source:
    print("say something")
    audio = r.listen(source)

    try:
        print(f"you said {r.recognize_amazon(audio)}")
    except sr.UnknownValueError:
        print("fos")
    except sr.RequestError as e:
        print(f"error: {e}")
