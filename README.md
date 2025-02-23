# wb-vosk-local

## Описание
Это сервис для **автономного голосового управления** с использованием **Vosk Speech Recognition**, работающий на **Wiren Board 8**.
Он получает аудиопоток с **USB и Bluetooth микрофонов**, распознает команды и отправляет результат в **MQTT**.

### Функции
- ✅ Поддержка нескольких USB и Bluetooth микрофонов одновременно
- ✅ Различение источника команды (в MQTT передается имя микрофона)
- ✅ Фильтрация коротких слов (исключает обрывки, "а", "ов" и т.п.)
- ✅ Работа как с одним, так и с несколькими микрофонами
- ✅ Полностью локальная работа, без облачных сервисов


## 1. Установка на Wiren Board 8
Перед установкой убедитесь, что **ваш контроллер поддерживает работу с USB и Bluetooth аудиоустройствами**. Для докер-контейнера и модели понадобятся около 13 Гбайт в разделе /mnt/data.

### 1.1 Переключите контроллер на testing

В тестинг есть ядро с поддержкой аудиоустройств, команда:
```bash
wb-release -t testing -y
```

### 1.2. Установите необходимые пакеты
```bash
apt update
apt install -y pulseaudio pulseaudio-utils bluez bluez-tools alsa-utils
```

### 1.3. Включите и запустите PulseAudio
```bash
systemctl --user enable pulseaudio
systemctl --user start pulseaudio
```

### 1.4. Проверка звуковых устройств
**Список всех микрофонов (USB и Bluetooth):**
```bash
pactl list sources | grep Name
```
Пример вывода:
```
Name: bluez_source.94_DB_56_A7_F5_38.a2dp_source
Name: bluez_source.80_AB_30_C2_15_10.a2dp_source
```
Если здесь есть устройства с `bluez_source`, значит, Bluetooth-микрофоны подключены.

**Для USB-микрофонов:**
```bash
arecord -l
```
Если микрофон есть в списке — он работает.


## 2. Запуск контейнера
### 2.1. Клонируйте репозиторий
```bash
apt update && apt install -y git
git clone https://github.com/aadegtyarev/wb-vosk-local.git
cd wb-vosk-local/docker
```

### 2.2 Установите Docker
Если Docker еще не установлен, установите. Для этого запустите на контроллере скрипт:

```bash
chmod +x ./install_docker_to_wb.sh
./install_docker_to_wb.sh
```

Скрипт написан по инструкции https://wirenboard.com/wiki/Docker, если что-то не работает — смотрите туда.

### 2.3 Соберите контейнер
```bash
docker compose build --no-cache
```

### 2.4 Запустите контейнер
```bash
docker compose up -d
```


## 3. Конфигурация
Файл `docker-compose.yml` позволяет **настраивать параметры распознавания**.

### 3.1. Выбор режима работы с микрофонами
Если вы хотите использовать **несколько микрофонов (USB и Bluetooth)**, включите `MULTI_MIC_MODE`:
```yaml
environment:
  - MULTI_MIC_MODE=true
```
Если микрофон **один**, установите `MULTI_MIC_MODE=false` или удалите переменную.

### 3.2. Выбор конкретного микрофона
1. **Получите список устройств**:
   ```bash
   docker exec -it wb-vosk-container python3 -c "import sounddevice as sd; print(sd.query_devices())"
   ```
2. **Пропишите нужный микрофон в `docker-compose.yml`**:
   ```yaml
   environment:
     - ALSA_DEVICE=hw:1,0  # USB-микрофон
   ```
   Для **Bluetooth-микрофона**:
   ```yaml
   environment:
     - ALSA_DEVICE=pulse
   ```


## 4. Проверка работы
### 4.1. Подписка на MQTT
```bash
mosquitto_sub -h localhost -t "/devices/wb-vosk-local/controls/text"
```
Пример выходных данных:
```json
{"timestamp": 1740231544, "text": "включи свет", "mic": "USB Audio Device (hw:1,0)"}
{"timestamp": 1740231550, "text": "выключи свет", "mic": "Bluetooth Mic - Sony WH-1000XM4"}
```

### 4.2. Тестовая запись
Запишите звук и прослушайте:
```bash
arecord -D hw:1,0 -f cd test.wav
aplay test.wav
```


## 5. Остановка контейнера
```bash
docker compose down
```

## 6. Удаление контейнера
```bash
docker compose rm -f wb-vosk-container
```

## 7. Обновление
```bash
git pull
docker compose build --no-cache
docker compose up -d
```
