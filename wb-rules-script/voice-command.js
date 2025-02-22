var commands = {
    "включи свет": function() { log("Свет включен!"); },
    "выключи свет": function() { log("Свет выключен!"); },
    "включи зуммер": function() { turnOnZummer(); },
    "выключи зуммер": function() { turnOffZummer() },
    "я закончил": function() { log("Завершаем работу!"); }
};

function turnOffZummer(){
  dev['buzzer/enabled'] = false
}

function turnOnZummer(){
  dev['buzzer/enabled'] = true
}

// Функция для вычисления расстояния Левенштейна
function levenshteinDistance(a, b) {
    var m = a.length;
    var n = b.length;
    var dp = [];

    for (var i = 0; i <= m; i++) {
        dp[i] = [];
        for (var j = 0; j <= n; j++) {
            if (i === 0) {
                dp[i][j] = j;
            } else if (j === 0) {
                dp[i][j] = i;
            } else {
                var cost = a[i - 1] === b[j - 1] ? 0 : 1;
                dp[i][j] = Math.min(
                    dp[i - 1][j] + 1,
                    dp[i][j - 1] + 1,
                    dp[i - 1][j - 1] + cost
                );
            }
        }
    }
    return dp[m][n];
}

// Функция нечёткого поиска
function findBestMatch(input) {
    var threshold = 2;
    var bestMatch = null;
    var bestDistance = threshold + 1;

    for (var cmd in commands) {
        var distance = levenshteinDistance(input, cmd);
        if (distance <= threshold && distance < bestDistance) {
            bestMatch = cmd;
            bestDistance = distance;
        }
    }
    return bestMatch;
}

// Подписка на изменения контрола
defineRule("voice_command", {
    whenChanged: "wb-vosk-local/text",
    then: function(newValue) {
        var parsed;
        try {
            parsed = JSON.parse(newValue);
        } catch (e) {
            log("Ошибка разбора JSON: " + newValue);
            return;
        }

        if (!parsed.text) {
            log("Нет текстового поля в JSON: " + newValue);
            return;
        }

        var command = findBestMatch(parsed.text.toLowerCase());
        if (command) {
            log("Распознана команда: " + command);
            commands[command]();
        } else {
            log("Команда не найдена: " + parsed.text);
        }
    }
});

