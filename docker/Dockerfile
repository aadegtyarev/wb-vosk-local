FROM python:3.9

WORKDIR /app

# Copy script
COPY files/wb-vosk-local.py /app/

# Install dependencies
RUN apt-get update && apt-get install -y \
    libasound2-dev \
    portaudio19-dev \
    pulseaudio \
    pulseaudio-utils \
    alsa-utils \
    bluez \
    bluez-tools \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir vosk sounddevice numpy paho-mqtt

# Download and install Vosk model
RUN wget https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip \
    && unzip vosk-model-small-ru-0.22.zip \
    && mkdir -p /opt/vosk-model-ru/ \
    && mv vosk-model-small-ru-0.22 /opt/vosk-model-ru/model \
    && rm vosk-model-small-ru-0.22.zip

# Set environment for PulseAudio
ENV PULSE_SERVER=unix:/tmp/pulse/native

# Run script
CMD ["bash", "-c", "pulseaudio --start && python3 /app/wb-vosk-local.py"]
