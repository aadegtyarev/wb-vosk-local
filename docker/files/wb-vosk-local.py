import argparse
import queue
import json
import time
import logging
import os
import sounddevice as sd
import paho.mqtt.client as mqtt
from vosk import Model, KaldiRecognizer

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
ALSA_DEVICE = os.getenv("ALSA_DEVICE", None)  # Явное указание устройства, если задано

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

q = queue.Queue()
recognizer_enabled = True
created_topics = []

# Initialize MQTT
mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

def publish_mqtt_meta(topic, meta):
    mqtt_client.publish(f"{topic}/meta", json.dumps(meta, ensure_ascii=False), retain=True)
    created_topics.append(f"{topic}/meta")

def create_virtual_device():
    global recognizer_enabled
    device_meta = {
        "driver": "vosk-asr",
        "title": {"en": "Vosk Speech Recognition", "ru": "Голосовое распознавание Vosk"}
    }
    publish_mqtt_meta(MQTT_TOPIC_DEVICE, device_meta)

    controls = {
        "text": {"type": "text", "readonly": True, "order": 1, "title": {"en": "Recognized Text", "ru": "Распознанный текст"}},
        "recognition_enabled": {"type": "switch", "order": 2, "title": {"en": "Enable Recognition", "ru": "Включить распознавание"}},
        "activation_word": {"type": "text", "readonly": True, "order": 3, "title": {"en": "Activation Word", "ru": "Слово активации"}}
    }

    for control, meta in controls.items():
        topic = f"{MQTT_TOPIC_DEVICE}/controls/{control}"
        publish_mqtt_meta(topic, meta)
        created_topics.append(topic)

    mqtt_client.publish(f"{MQTT_TOPIC_DEVICE}/controls/text", json.dumps({"timestamp": int(time.time()), "text": ""}, ensure_ascii=False), retain=True)
    mqtt_client.publish(f"{MQTT_TOPIC_DEVICE}/controls/recognition_enabled", "1", retain=True)
    mqtt_client.publish(f"{MQTT_TOPIC_DEVICE}/controls/activation_word", ACTIVATION_WORD, retain=True)
    created_topics.extend([
        f"{MQTT_TOPIC_DEVICE}/controls/text",
        f"{MQTT_TOPIC_DEVICE}/controls/recognition_enabled",
        f"{MQTT_TOPIC_DEVICE}/controls/activation_word"
    ])

def delete_virtual_device():
    logging.info("Removing virtual device...")
    for topic in created_topics:
        mqtt_client.publish(topic, "", retain=True)
    mqtt_client.publish(MQTT_TOPIC_DEVICE, "", retain=True)
    logging.info("Virtual device removed.")

def subscribe_mqtt_topics():
    mqtt_client.subscribe(f"{MQTT_TOPIC_DEVICE}/controls/recognition_enabled/on")

def filter_text(text):
    words = text.split()
    filtered_words = [word for word in words if len(word) >= MIN_WORD_LENGTH]
    return " ".join(filtered_words)

def process_text(text):
    text = text.strip()
    if ACTIVATION_WORD in text:
        filtered_text = text.split(ACTIVATION_WORD, 1)[1].strip()
        filtered_text = filter_text(filtered_text)
        if filtered_text:
            publish_text(filtered_text)

def publish_text(text):
    payload = json.dumps({"timestamp": int(time.time()), "text": text}, ensure_ascii=False)
    mqtt_client.publish(f"{MQTT_TOPIC_DEVICE}/controls/text", payload, retain=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model", type=str, default=VOSK_MODEL_PATH, help="Path to Vosk model")
    args = parser.parse_args()

    try:
        model = Model(args.model)
    except Exception:
        logging.exception("Error loading the model")
        return

    recognizer = KaldiRecognizer(model, SAMPLE_RATE)
    create_virtual_device()
    subscribe_mqtt_topics()
    mqtt_client.loop_start()
    logging.info("Service started.")

    try:
        with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE, dtype="int16", channels=CHANNELS, device=ALSA_DEVICE, callback=lambda i, f, t, s: q.put(bytes(i))):
            while True:
                if recognizer.AcceptWaveform(q.get()):
                    process_text(json.loads(recognizer.Result())["text"])
    except KeyboardInterrupt:
        logging.info("Service stopping...")
        delete_virtual_device()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        logging.info("Service stopped.")

if __name__ == "__main__":
    main()
