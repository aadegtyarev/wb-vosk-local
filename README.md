# wb-vosk-local: Локальное голосовое управление для Wiren Board

Этот проект интегрирует **Vosk** с **MQTT на контроллере Wiren Board**.
Голосовые команды передаются в **виртуальное устройство** WB через MQTT.

⚠ **Ограничение:** Проект поддерживает **только один USB микрофон**. Если у вас несколько аудиоустройств, укажите нужный `hw:0,0` при пробросе в Dockerfile: в разделе environment добавьте `- ALSA_DEVICE=hw:0,0`.

## 1. Установка на Wiren Board

### 1.1 Установите alsa-utils
```bash
apt install alsa-utils
```

### 1.2 Проверьте, что есть микрофоны
Эта команда выведет все USB-микрофоны, в том числе и подключенные через USB-звуковую карту.
```console
# aplay -l
**** List of PLAYBACK Hardware Devices ****
card 0: ME6S [ME6S], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0

```

### 1.3 Клонируйте репозиторий
```bash
apt update && apt install -y git
git clone https://github.com/aadegtyarev/wb-vosk-local.git
cd wb-vosk-local/docker
```

### 1.4 Переключите контроллер на testing

В тестинг есть ядро с поддержкой аудиоустройств, команда:
```bash
wb-release -t testing -y
```

### 1.5 Установите Docker
Если Docker еще не установлен, установите. Для этого запустите на контроллере скрипт:

```bash
chmod +x ./install_docker_to_wb.sh
./install_docker_to_wb.sh
```

Скрипт написан по инструкции https://wirenboard.com/wiki/Docker, если что-то не работает — смотрите туда.

## 2. Запуск Docker-контейнера

### 2.1 Соберите образ
```bash
docker compose build --no-cache
```

### 2.2 Запустите контейнер
```bash
docker compose up -d
```

### 2.3 Проверьте логи
```bash
docker logs wb-vosk-container --tail 50
```

## 3. Проверка работы
### 3.1 Подписаться на MQTT-топик с текстом
```bash
mosquitto_sub -h localhost -t "/devices/wb-vosk-local/controls/text"
```
Если все работает, голосовые команды будут появляться в этом топике.

### 3.2 Проверить, работает ли микрофон в контейнере
```bash
docker exec -it wb-vosk-container arecord -l
```
Если устройство отображается — **значит, микрофон работает**.

## 4. Настройка MQTT и WB-Rules
### 4.1 Скопируйте скрипт в контроллер
Скрипт из папки **`wb-rules-script/`** нужно скопировать на Wiren Board:
```bash
scp wb-rules-script/wb-vosk-rules.js root@wirenboard:/etc/wb-rules/
```
Затем **перезапустите WB-Rules**:
```bash
systemctl restart wb-rules
```

## 5. Остановка и удаление контейнера
### Остановить контейнер
```bash
docker compose down
```
### Удалить образ
```bash
docker rmi wb-vosk:latest
```

## 6. Переменные окружения (настраиваемые параметры)
Все настройки передаются через **переменные среды** в `docker-compose.yml`:

| Параметр          | Описание                           | Значение по умолчанию |
|-------------------|---------------------------------|-----------------------|
| `MQTT_BROKER`    | Адрес MQTT-брокера             | `localhost`          |
| `MQTT_PORT`      | Порт MQTT                      | `1883`               |
| `DEVICE_ID`      | Имя виртуального устройства    | `wb-vosk-local`      |
| `SAMPLE_RATE`    | Частота дискретизации звука    | `16000`              |
| `BLOCK_SIZE`     | Размер блока звука             | `8000`               |
| `CHANNELS`       | Количество каналов             | `1`                  |
| `ACTIVATION_WORD`| Слово-активатор                | `"Контроллер"`       |
| `MIN_WORD_LENGTH`| Минимальная длина слова       | `3`                  |
| `VOSK_MODEL_PATH`| Путь к модели Vosk            | `/opt/vosk-model-ru/model` |

Если нужно изменить параметры, **редактируйте `docker-compose.yml`** перед запуском.

## 7. Подключение к Home Assistant (опционально)
Если MQTT подключен к **Home Assistant**, можно **автоматически распознавать команды** и выполнять действия через автоматизации.

```yaml
mqtt:
  sensor:
    - name: "Vosk Recognized Text"
      state_topic: "/devices/wb-vosk-local/controls/text"
```

## 8. Обновление
```bash
cd wb-vosk-local
git pull
docker compose build --no-cache
docker compose up -d
```

### Поддержка и участие в проекте
Поддержки нет, за риски отвечаете сами перед собой. Пуллреквесты приветствуются.


