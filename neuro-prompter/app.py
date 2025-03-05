import logging
import io
import speech_recognition as sr
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

# Настройка логирования: вывод в консоль и в файл speech_log.txt
logging.basicConfig(
    level=logging.DEBUG,  # В продакшене можно сменить уровень на INFO
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("speech_log.txt", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
# В продакшене отладочный режим отключен (debug=False) и reloader не используется
socketio = SocketIO(app, logger=True, engineio_logger=True)

recognizer = sr.Recognizer()
audio_buffer = []  # Буфер для накопления аудио-чанков

@app.route('/')
def index():
    app.logger.info("Отрисовка index.html")
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    app.logger.info("Socket.IO: Client connected.")

@socketio.on('disconnect')
def handle_disconnect():
    app.logger.info("Socket.IO: Client disconnected.")

@socketio.on('start_audio')
def start_audio():
    app.logger.info("Запись аудио началась (start_audio вызван).")
    global audio_buffer
    audio_buffer.clear()
    emit('status', {'status': 'start_audio'})

@socketio.on('send_audio_chunk')
def handle_audio_chunk(audio_data):
    app.logger.info("Функция handle_audio_chunk начата.")
    try:
        app.logger.info(f"Получен чанк аудио: {len(audio_data)} байт.")
        audio_buffer.append(audio_data)

        # Объединяем накопленные аудио-чанки
        combined_data = b''.join(audio_buffer)
        app.logger.info(f"Собран аудио-файл размером: {len(combined_data)} байт.")

        # Проверка корректности формата аудио-данных: для WAV файла должен присутствовать заголовок RIFF
        if not combined_data.startswith(b'RIFF'):
            app.logger.error("Некорректный формат аудио-данных: отсутствует RIFF заголовок.")
            emit('status', {'status': 'error', 'message': 'Некорректный формат аудио-данных.'})
            audio_buffer.clear()
            return

        audio_bytes = io.BytesIO(combined_data)

        app.logger.info("Попытка создать AudioFile из полученных данных.")
        with sr.AudioFile(audio_bytes) as source:
            app.logger.info("AudioFile успешно создан. Начинается считывание аудио...")
            audio = recognizer.record(source)
            app.logger.info("Аудио успешно считано. Начинается распознавание речи...")
            try:
                text = recognizer.recognize_google(audio, language='ru-RU')
            except sr.RequestError as req_err:
                app.logger.error(f"Ошибка SpeechRecognition API: {req_err}")
                emit('status', {'status': 'error', 'message': 'SpeechRecognition API недоступен или лимит исчерпан.'})
                audio_buffer.clear()
                return
            except sr.UnknownValueError:
                app.logger.error("Не удалось распознать речь: неизвестная ошибка.")
                emit('status', {'status': 'error', 'message': 'Не удалось распознать речь.'})
                audio_buffer.clear()
                return
            app.logger.info(f"Распознано: {text}")
            emit('transcription', {'text': text})

        # После успешной обработки очищаем буфер
        audio_buffer.clear()
        app.logger.info("Буфер аудио очищен после успешной обработки.")

    except Exception as e:
        app.logger.error(f"Ошибка при обработке аудио: {e}")
        emit('status', {'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    # Запуск в продакшн-режиме (debug=False) – отключаются авто-перезапуски и выводятся только нужные логи
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
