import argparse
import queue
import json
import time
import logging
import os
import sounddevice as sd
import paho.mqtt.client as mqtt
from vosk import Model, KaldiRecognizer
import threading
import subprocess

# Load settings from environment variables
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
DEVICE_ID = os.getenv("DEVICE_ID", "wb-vosk-local")
MQTT_TOPIC_DEVICE = f"/devices/{DEVICE_ID}"
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", 16000))
BLOCK_SIZE = int(os.getenv("BLOCK_SIZE", 8000))
CHANNELS = int(os.getenv("CHANNELS", 1))
ACTIVATION_WORD = os.getenv("ACTIVATION_WORD", "контроллер").lower()
MIN_WORD_LENGTH = int(os.getenv("MIN_WORD_LENGTH", 3))
VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH", "/opt/vosk-model-ru/model")
MULTI_MIC_MODE = os.getenv("MULTI_MIC_MODE", "false").lower() == "true"

# Logging configuration
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

q = queue.Queue()
recognizer_enabled = True
created_topics = []

# Initialize MQTT
mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

def list_audio_devices():
    """List available USB audio input devices"""
    devices = sd.query_devices()
    input_devices = {idx: device["name"] for idx, device in enumerate(devices) if device['max_input_channels'] > 0}
    logging.info("Available USB audio devices:")
    for idx, name in input_devices.items():
        logging.info(f"{idx}: {name}")
    return input_devices

def list_pulseaudio_sources():
    """List available PulseAudio sources (Bluetooth mics)"""
    result = subprocess.run(["pactl", "list", "sources"], stdout=subprocess.PIPE, text=True)
    sources = {line.split(": ")[1]: line.split(".")[1] for line in result.stdout.split("\n") if "Name:" in line and "bluez" in line}
    logging.info(f"Available Bluetooth sources: {sources}")
    return sources

def filter_text(text):
    words = text.split()
    filtered_words = [word for word in words if len(word) >= MIN_WORD_LENGTH]
    return " ".join(filtered_words)

def process_text(text, mic_name):
    text = text.strip().lower()
    if ACTIVATION_WORD in text:
        filtered_text = text.split(ACTIVATION_WORD, 1)[1].strip()
        filtered_text = filter_text(filtered_text)
        if filtered_text:
            publish_text(filtered_text, mic_name)

def publish_text(text, mic_name):
    payload = json.dumps({"timestamp": int(time.time()), "text": text, "mic": mic_name}, ensure_ascii=False)
    mqtt_client.publish(f"{MQTT_TOPIC_DEVICE}/controls/text", payload, retain=True)

def recognize_from_microphone(mic_index, mic_name):
    """Process audio from a single microphone"""
    try:
        model = Model(VOSK_MODEL_PATH)
        recognizer = KaldiRecognizer(model, SAMPLE_RATE)
        with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE, dtype="int16", channels=CHANNELS, device=mic_index):
            while True:
                if recognizer.AcceptWaveform(q.get()):
                    process_text(json.loads(recognizer.Result())["text"], mic_name)
    except Exception as e:
        logging.error(f"Error with microphone {mic_name}: {e}")

def recognize_from_pulseaudio(mic_name):
    """Recognize from a specific Bluetooth mic via PulseAudio"""
    try:
        model = Model(VOSK_MODEL_PATH)
        recognizer = KaldiRecognizer(model, SAMPLE_RATE)
        with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE, dtype="int16", channels=CHANNELS, device=mic_name):
            while True:
                if recognizer.AcceptWaveform(q.get()):
                    process_text(json.loads(recognizer.Result())["text"], mic_name)
    except Exception as e:
        logging.error(f"Error with Bluetooth mic {mic_name}: {e}")

def main():
    available_usb_mics = list_audio_devices()
    available_bt_mics = list_pulseaudio_sources()

    threads = []

    if MULTI_MIC_MODE:
        logging.info(f"Starting multi-mic mode with {len(available_usb_mics)} USB mics and {len(available_bt_mics)} Bluetooth mics.")

        for mic_index, mic_name in available_usb_mics.items():
            thread = threading.Thread(target=recognize_from_microphone, args=(mic_index, mic_name), daemon=True)
            threads.append(thread)
            thread.start()

        for mic_name, bt_source in available_bt_mics.items():
            thread_bt = threading.Thread(target=recognize_from_pulseaudio, args=(bt_source,), daemon=True)
            threads.append(thread_bt)
            thread_bt.start()
    else:
        if available_usb_mics:
            mic_index, mic_name = next(iter(available_usb_mics.items()))
            logging.info(f"Using single USB microphone: {mic_name}")
            recognize_from_microphone(mic_index, mic_name)
        elif available_bt_mics:
            mic_name, bt_source = next(iter(available_bt_mics.items()))
            logging.info(f"Using single Bluetooth microphone: {mic_name}")
            recognize_from_pulseaudio(bt_source)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
