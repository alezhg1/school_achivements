import requests
import time

TUNA_URL = "https://2m1fvg-5-228-82-228.ru.tuna.am"

while True:
    try:
        response = requests.get(TUNA_URL, timeout=10)
        print(f"Пинг успешен: {response.status_code} в {time.strftime('%H:%M:%S')}")
    except Exception as e:
        print(f"Ошибка пинга: {e}")
    time.sleep(150)  # 2.5 минуты
