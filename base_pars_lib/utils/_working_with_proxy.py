import requests
from requests.auth import HTTPProxyAuth

from base_pars_lib.core._requests_digest_proxy import HTTPProxyDigestAuth


def rotating_proxy_auth(
        http_url: str,
        https_url: str,
        login: str,
        password: str
) -> requests.Session:
    """
    Правильная авторизация в ротационном прокси

    :param http_url: str
        url ротационного прокси http
    :param https_url: str
        url ротационного прокси https
    :param login: str
        login ротационного прокси
    :param password: str
        пароль ротационного прокси
    :return:
        requests-сессию, через которую отправляются запросы
    """

    session_proxy = requests.session()
    session_proxy.proxies = {
        'http': http_url,
        'https': https_url
    }
    session_proxy.auth = HTTPProxyDigestAuth(login, password)
    session_proxy.auth = HTTPProxyAuth(login, password)
    return session_proxy
