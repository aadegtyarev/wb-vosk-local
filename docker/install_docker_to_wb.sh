 
#!/bin/bash

# Обновление списка пакетов
apt update -y

# Установка зависимостей
apt install -y ca-certificates curl gnupg lsb-release

# Добавление официального ключа Docker
curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -

# Добавление репозитория Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

apt install -y iptables
update-alternatives --set iptables /usr/sbin/iptables-legacy
update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy

mkdir /mnt/data/etc/docker && ln -s /mnt/data/etc/docker /etc/docker

mkdir /mnt/data/.docker


# Создание конфигурационного файла daemon.json с настройками
echo '{
  "data-root": "/mnt/data/.docker",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}' > /etc/docker/daemon.json


# Обновление списка пакетов с учётом нового репозитория
apt update -y

# Установка Docker
apt install -y docker-ce docker-ce-cli containerd.io

# Запуск и включение Docker на старте системы
systemctl enable --now docker

# Запуск проверки
docker run hello-world

echo "End Script."
