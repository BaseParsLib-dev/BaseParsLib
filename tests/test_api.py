import requests

# Базовый URL API
BASE_URL = "https://example.com"


# Тест GET-запроса для проверки доступности API
def test_api_availability() -> None:
    response = requests.get(BASE_URL)
    assert response.status_code == 200, "API недоступен"


# Тест GET-запроса для проверки заголовков ответа
def test_response_headers() -> None:
    response = requests.get(BASE_URL)
    assert "content-type" in response.headers, "Заголовок content-type отсутствует"
    assert response.headers["content-type"].startswith("text/html"), "Неверный content-type"


# Тест GET-запроса для проверки содержимого ответа
def test_response_content() -> None:
    response = requests.get(BASE_URL)
    assert response.text is not None, "Тело ответа пустое"
    assert "Example Domain" in response.text, "Ожидаемый текст отсутствует в ответе"


# pytest tests/test_api.py
