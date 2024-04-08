from threading import Thread
import time

import requests
from fake_useragent import UserAgent
import urllib3

# from base_pars_lib import _requests_digest_proxy


class BaseParser:
    def __init__(self, requests_session=None):
        self.requests_session = requests_session

        self.user_agent = UserAgent()

        self.ignore_exceptions = (
            requests.exceptions.ProxyError,
            # _requests_digest_proxy.ProxyError,
            urllib3.exceptions.ProxyError,
            requests.exceptions.ConnectionError
        )

    def _make_request(
            self,
            url: str,
            method: str = 'GET',
            verify: bool = True,
            with_random_useragent: bool = True,
            from_one_session=True,
            proxies: dict = None,
            headers: dict = None,
            cookies: dict = None,
            json: dict = None,
            data: dict = None
    ):
        """
        Отправляет реквест через requests_session

        :param url: str
            Ссылка на страницу для запроса
        :param method: str = 'GET'
            HTTP-метод
        :param verify: bool = True
            Проверка безопасности сайта
        :param with_random_useragent: bool = True
            Случайный юзер-агент
        :param from_one_session: bool = True
            Использование одной сессии
        :param proxies: dict = None
            Прокси
        :param headers: dict = None
            Заголовки запроса
        :param cookies: dict = None
            Куки
        :param data: dict = None
            Передаваемые данные
        :param json: dict = None
            Передаваемые данные

        :return:
            response
        """

        params = self._get_request_params(
            url, headers, cookies, with_random_useragent,
            method, verify, json, data, proxies
        )

        if from_one_session:
            return self.requests_session.request(**params)
        else:
            with requests.request(**params) as response:
                return response

    def _make_backoff_request(
            self,
            url: str,
            method: str = 'GET',
            iter_count: int = 10,
            increase_by_seconds: int = 10,
            verify: bool = True,
            with_random_useragent: bool = True,
            from_one_session=True,
            proxies: dict = None,
            headers: dict = None,
            cookies: dict = None,
            json: dict = None,
            data: dict = None,
            ignore_exceptions: tuple = 'default'
    ):
        """
        Если код ответа не 200 или произошла ошибка прокси, отправляет запрос повторно
        Задержка между каждым запросом увеличивается

        :param url: str
            Ссылка на страницу для запроса
        :param method: str = 'GET'
            HTTP-метод
        :param iter_count: int = 10
            Количество попыток отправки запроса
        :param increase_by_seconds: int = 10
            Значение, на которое увеличивается время ожидания
            на каждой итерации
        :param verify: bool = True
            Проверка безопасности сайта
        :param with_random_useragent: bool = True
            Случайный юзер-агент
        :param from_one_session: bool = True
            Использование одной сессии
        :param proxies: dict = None
            Прокси
        :param headers: dict = None
            Заголовки запроса
        :param cookies: dict = None
            Куки
        :param data: dict = None
            Передаваемые данные
        :param json: dict = None
            Передаваемые данные
        :param ignore_exceptions: tuple = 'default'
            Возможность передать ошибки, которые будут обрабатываться в backoff.
            Если ничего не передано, обрабатываются дефолтные:
                requests.exceptions.ProxyError,
                _requests_digest_proxy.ProxyError,
                urllib3.exceptions.ProxyError,
                requests.exceptions.ConnectionError

        :return:
            На последней итерации возвращает response с
            любым кодом ответа или, если произошла ошибка Proxy - возвращает None
        """

        if ignore_exceptions == 'default':
            ignore_exceptions = self.ignore_exceptions

        for i in range(1, iter_count + 1):
            try:
                response = self._make_request(
                    url=url, verify=verify, with_random_useragent=with_random_useragent,
                    headers=headers, cookies=cookies, data=data, json=json, method=method,
                    from_one_session=from_one_session, proxies=proxies
                )
            except ignore_exceptions:
                time.sleep(i * increase_by_seconds)
                continue
            if response.status_code == 200 or i == iter_count:
                return response
            time.sleep(i * increase_by_seconds)

        return None

    def _get_request_params(
            self,
            url: str,
            headers: dict = None,
            cookies: dict = None,
            with_random_useragent: bool = True,
            method: str = 'GET',
            verify: bool = True,
            json: dict = None,
            data: dict = None,
            proxies: dict = None
    ) -> dict:
        """
        Возвращает словарь параметров для запроса через requests

        :param url: str
            Ссылка на сайт
        :param headers: dict = None
            Заголовки
        :param cookies: dict = None
            Куки
        :param with_random_useragent: bool = True
            Использование рандомного юзерагента
        :param method: str = 'GET'
            requests-метод
        :param verify: bool = True
            Проверка безопасности сайта
        :param json: dict = None
            json-данные
        :param data: dict = None
            Данные запроса
        :param proxies: dict = None
            Прокси
        :return:
        """

        headers = {} if headers is None else headers
        cookies = {} if cookies is None else cookies

        if with_random_useragent:
            headers['User-Agent'] = self.user_agent.random

        params: dict = {
            'method': method.upper(),
            'url': url,
            'headers': headers,
            'cookies': cookies,
            'verify': verify,
            'json': json,
            'data': data
        }

        if proxies is not None:
            params['proxies'] = proxies

        return params

    @staticmethod
    def _threading_method(
            chunked_array: list | tuple,
            method
    ) -> None:
        """
        Создаёт столько потоков, сколько чанков передано в chunked_array,
        выполняет метод method для каждого чанка в отдельном потоке

        :param chunked_array: list | tuple
            Массив из чанков с url-ами или другими данными для запроса
        :param method:
            Метод, который работает с чанком из переданного массива
            и сохраняет результаты во внешний массив

        :return:
            None
        """

        threads = []
        for chunk in chunked_array:
            chunk_thread = Thread(
                target=method,
                args=(chunk,)
            )
            chunk_thread.start()
            threads.append(chunk_thread)
        for thread in threads:
            thread.join()
