FROM python:3.9

WORKDIR /app

# Копируем файлы
COPY files/wb-vosk-local.py /app/

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y \
    libasound2-dev \
    portaudio19-dev  # <-- Устанавливаем PortAudio для sounddevice

RUN pip install --no-cache-dir vosk sounddevice numpy paho-mqtt

# Скачиваем и устанавливаем модель Vosk
RUN wget https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip \
    && unzip vosk-model-small-ru-0.22.zip \
    && mkdir -p /opt/vosk-model-ru/ \
    && mv vosk-model-small-ru-0.22 /opt/vosk-model-ru/model \
    && rm vosk-model-small-ru-0.22.zip

# Запускаем скрипт напрямую
CMD ["python3", "/app/wb-vosk-local.py"]
