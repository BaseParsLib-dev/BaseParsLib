import json
import os

import requests

# URL для проверки IP
IPIFY_URL = "https://api.ipify.org"


# Тесты для проверки IP через прокси
def test_proxy() -> None:
    with open(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "../parser_data.json")
    ) as f:
        data = json.loads(f.read())

    proxy_info = data.get("proxy", {})
    proxy_url = proxy_info.get("url")
    proxy_login = proxy_info.get("login")
    proxy_password = proxy_info.get("password")

    proxies = {
        "http": f"http://{proxy_login}:{proxy_password}@{proxy_url}",
        "https": f"http://{proxy_login}:{proxy_password}@{proxy_url}",
    }

    response = requests.get(IPIFY_URL, proxies=proxies)
    assert response.status_code == 200, "Не удалось получить IP через прокси"
    assert response.text, "Ответ пустой"


# pytest tests/test_proxy.py
