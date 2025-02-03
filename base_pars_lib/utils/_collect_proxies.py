import time
import requests


def _collect_proxies_for_countries(token: str,
                                  countries_list: list[str],
                                  max_retries: int = 10,
                                  list_of_dict: bool = False) -> list:
    """
    Получение списка прокси с webshare.io для выбранных стран.
    При статус коде не 200 повторная отправка запроса с экспоненциальной задержкой.
    За одну страницу отдаётся максимум 100 прокси.

    :param token: токен авторизации на webshare.io
    :param countries_list: список стран формата ['AE', 'EG']
    :param max_retries: максимальное число попыток отправки запроса
    :param list_of_dict: возвращать прокси в виде списка словарей
                        [{'https': 'http://username:password@proxy_address:port'}, ]
                        вместо списка строк
                        ['http://username:password@proxy_address:port', ]
    :return: список прокси
    """
    all_proxies = []
    session = requests.Session()
    session.headers.update({"Authorization": f"Token {token}"})

    base_url = "https://proxy.webshare.io/api/v2/proxy/list/"
    params = {
        "mode": "direct",
        "page_size": 100,
        "country_code__in": ",".join(countries_list),
    }

    page = 1

    while True:
        retries = 0
        params["page"] = page

        while retries < max_retries:
            try:
                response = session.get(base_url, params=params, timeout=10)
                print(response.status_code)
                if response.status_code == 200:
                    data_proxies = response.json()
                    proxies = [
                        {
                            'https': f'http://{data["username"]}:{data["password"]}@{data["proxy_address"]}:{data["port"]}'}
                        if list_of_dict else
                        f'http://{data["username"]}:{data["password"]}@{data["proxy_address"]}:{data["port"]}'
                        for data in data_proxies.get('results', [])
                    ]

                    if not proxies:
                        return all_proxies  # Прерываем основной цикл, если прокси больше нет

                    all_proxies.extend(proxies)
                    page += 1
                    break  # Переход к следующей странице

                time.sleep(2 * retries)
                retries += 1

            except requests.RequestException:
                time.sleep(2 * retries)
                retries += 1

        if retries == max_retries:
            break  # Прерываем основной цикл, если достигнут предел попыток

    return all_proxies

