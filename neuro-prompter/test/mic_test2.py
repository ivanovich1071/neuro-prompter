import speech_recognition as sr

recognizer = sr.Recognizer()
mic = sr.Microphone(device_index=1)  # Попробуй заменить 0 на другой индекс

with mic as source:
    recognizer.adjust_for_ambient_noise(source)
    print("Говорите...")
    audio = recognizer.listen(source)

print("Распознано:", recognizer.recognize_google(audio, language="ru-RU"))
