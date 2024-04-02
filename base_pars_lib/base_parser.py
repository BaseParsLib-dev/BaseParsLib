from threading import Thread
import time

import requests
from fake_useragent import UserAgent
import urllib3

from base_pars_lib import _requests_digest_proxy


class BaseParser:
    def __init__(self, requests_session):
        self.requests_session = requests_session

        self.user_agent = UserAgent()

    def _make_request(
            self,
            url: str,
            verify: bool = True,
            with_random_useragent: bool = True,
            headers: dict = None,
            cookies: dict = None
    ):
        """
        Отправляет реквест через requests_session

        :param url: str
            Ссылка на страницу для запроса
        :param verify: bool = True
            Проверка безопасности сайта
        :param with_random_useragent: bool = True
            Случайный юзер-агент
        :param headers: dict = None
            Заголовки запроса
        :param cookies: dict = None
            Куки

        :return:
            response
        """

        headers = {} if headers is None else headers
        cookies = {} if cookies is None else cookies

        if with_random_useragent:
            headers['User-Agent'] = self.user_agent.random
        return self.requests_session.get(
            url, headers=headers, cookies=cookies, verify=verify
        )

    def _make_backoff_request(
            self,
            url: str,
            iter_count: int = 10,
            increase_by_seconds: int = 10,
            verify: bool = True,
            with_random_useragent: bool = True,
            headers: dict = None,
            cookies: dict = None
    ):
        """
        Если код ответа не 200 или произошла ошибка прокси, отправляет запрос повторно
        Задержка между каждым запросом увеличивается

        :param iter_count: int = 10
            Количество попыток отправки запроса
        :param increase_by_seconds: int = 10
            Значение, на которое увеличивается время ожидания
            на каждой итерации
        :param verify: bool = True
            Проверка безопасности сайта
        :param with_random_useragent: bool = True
            Случайный юзер-агент
        :param headers: dict = None
            Заголовки запроса
        :param cookies: dict = None
            Куки

        :return:
            На последней итерации возвращает response с
            любым кодом ответа или, если произошла ошибка Proxy - возвращает None
        """

        for i in range(1, iter_count + 1):
            try:
                response = self._make_request(
                    url, verify, with_random_useragent, headers, cookies
                )
            except (
                    requests.exceptions.ProxyError,
                    _requests_digest_proxy.ProxyError,
                    urllib3.exceptions.ProxyError
            ):
                time.sleep(i * increase_by_seconds)
                continue
            if response.status_code == 200 or i == iter_count:
                return response
            time.sleep(i * increase_by_seconds)

        return None

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
