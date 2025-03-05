const socket = io.connect('http://' + document.domain + ':' + location.port);

let mediaRecorder;
let audioChunks = [];

// Начинаем запись
function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);

            // Когда появляются данные
            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
                if (audioChunks.length > 0) {
                    // Отправляем пакеты аудио в реальном времени
                    const audioBlob = new Blob([event.data], { type: 'audio/webm' });
                    audioBlob.arrayBuffer().then(buffer => {
                        // Конвертируем WebM в WAV перед отправкой на сервер
                        convertWebMToWav(buffer).then(wavBuffer => {
                            socket.emit('send_audio_chunk', wavBuffer);
                        });
                    });
                }
            };

            mediaRecorder.onstop = () => {
                console.log('Запись завершена');
            };

            socket.emit('start_audio');
            mediaRecorder.start(1000); // Старт записи с периодичностью 1 секунда
            console.log('Запись началась...');
        })
        .catch(error => {
            console.error('Ошибка доступа к микрофону:', error);
        });
}

// Конвертируем WebM в WAV с использованием AudioContext
function convertWebMToWav(webmBuffer) {
    return new Promise((resolve, reject) => {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const blob = new Blob([webmBuffer], { type: 'audio/webm' });

        const reader = new FileReader();
        reader.onloadend = () => {
            const buffer = reader.result;

            audioContext.decodeAudioData(buffer, audioBuffer => {
                const wavData = encodeWAV(audioBuffer, audioContext.sampleRate);
                resolve(wavData);
            }, reject);
        };
        reader.readAsArrayBuffer(blob);
    });
}

// Функция для кодирования в WAV
function encodeWAV(audioBuffer, sampleRate) {
    const numChannels = audioBuffer.numberOfChannels;
    const bufferLength = audioBuffer.length;
    const buffer = new ArrayBuffer(44 + bufferLength * numChannels * 2);
    const view = new DataView(buffer);
    const channelData = [];
    const offset = 0;

    // Заголовок WAV
    writeString(view, offset, 'RIFF');
    view.setUint32(offset + 4, 36 + bufferLength * numChannels * 2, true);
    writeString(view, offset + 8, 'WAVE');
    writeString(view, offset + 12, 'fmt ');
    view.setUint32(offset + 16, 16, true);
    view.setUint16(offset + 20, 1, true);
    view.setUint16(offset + 22, numChannels, true);
    view.setUint32(offset + 24, sampleRate, true);
    view.setUint32(offset + 28, sampleRate * numChannels * 2, true);
    view.setUint16(offset + 32, numChannels * 2, true);
    view.setUint16(offset + 34, 16, true);
    writeString(view, offset + 36, 'data');
    view.setUint32(offset + 40, bufferLength * numChannels * 2, true);

    // Запись аудио данных
    for (let channel = 0; channel < numChannels; channel++) {
        channelData.push(audioBuffer.getChannelData(channel));
    }

    let offsetData = 44;
    for (let i = 0; i < bufferLength; i++) {
        for (let channel = 0; channel < numChannels; channel++) {
            const sample = Math.max(-1, Math.min(1, channelData[channel][i]));
            view.setInt16(offsetData, sample * 0x7FFF, true);
            offsetData += 2;
        }
    }

    return buffer;
}

// Функция записи строки в DataView
function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
    }
}

// Получаем транскрибированный текст от сервера
socket.on('transcription', function(data) {
    console.log('Транскрипция получена:', data.text);
    document.getElementById('transcribedText').textContent = data.text;
});
