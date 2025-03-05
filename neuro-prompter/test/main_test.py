import speech_recognition as sr

recognizer = sr.Recognizer()

# Функция для записи звука с микрофона
def record_audio():
    with sr.Microphone() as source:
        print("Говорите...")
        try:
            recognizer.adjust_for_ambient_noise(source)  # Настроим на шум
            # Попробуем слушать, используя автоматическое управление
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=20)  # Здесь увеличено время ожидания
            return audio
        except sr.WaitTimeoutError:
            print("Время ожидания истекло. Попробуйте снова.")
            return None
        except Exception as e:
            print(f"Произошла ошибка при записи: {e}")
            return None

# Функция для распознавания речи
def recognize_speech():
    while True:
        audio = record_audio()
        if audio is not None:
            try:
                # Пробуем распознать текст
                text = recognizer.recognize_google(audio, language="ru-RU")
                print("Вы сказали:", text)  # Выводим распознанный текст
            except sr.UnknownValueError:
                print("Не удалось распознать речь")
            except sr.RequestError:
                print("Ошибка сервиса распознавания")

recognize_speech()
