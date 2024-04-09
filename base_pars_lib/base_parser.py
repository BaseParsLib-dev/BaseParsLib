from threading import Thread
import time
import random
import logging
from http import HTTPStatus

import requests
from fake_useragent import UserAgent
import urllib3

from base_pars_lib import _requests_digest_proxy


class BaseParser:
    def __init__(self, requests_session=None, debug: bool = False):
        self.requests_session = requests_session

        self.user_agent = UserAgent()

        self.ignore_exceptions = (
            requests.exceptions.ProxyError,
            _requests_digest_proxy.ProxyError,
            urllib3.exceptions.ProxyError,
            requests.exceptions.ConnectionError
        )

        self.debug = debug

    def _make_request(
            self,
            url: str,
            method: str = 'GET',
            verify: bool = True,
            with_random_useragent: bool = True,
            from_one_session=True,
            proxies: dict = None,
            headers: dict | list = None,
            cookies: dict | list = None,
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
        :param headers: dict | list = None
            Заголовки запроса, возможно передать в виде списка,
            тогда выбирутся рандомно
        :param cookies: dict | list = None
            Куки запроса, возможно передать в виде списка,
            тогда выбирутся рандомно
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
            return requests.request(**params)

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
            headers: dict | list = None,
            cookies: dict | list = None,
            json: dict = None,
            data: dict = None,
            ignore_exceptions: tuple = 'default',
            ignore_404: bool = False,
            long_wait_for_50x: bool = False
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
        :param headers: dict | list = None
            Заголовки запроса, возможно передать в виде списка,
            тогда выбирутся рандомно
        :param cookies: dict | list = None
            Куки запроса, возможно передать в виде списка,
            тогда выбирутся рандомно
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
        :param ignore_404: bool = False
            Позволяет не применять backoff к респонзам со статус-кодом 404.
            Если такой страницы нет, backoff может не понадобиться
            Если значение = True и передан url на несуществующую страницу,
            метод вернёт response после первой попытки


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
            except ignore_exceptions as Ex:
                if self.debug:
                    logging.debug(f'{Ex}: iter {i}')
                time.sleep(i * increase_by_seconds)
                continue
            if response.status_code == HTTPStatus.OK or i == iter_count:
                return response
            elif response.status_code == HTTPStatus.NOT_FOUND and ignore_404:
                return response
            elif 599 >= response.status_code >= 500 and long_wait_for_50x:
                time.sleep(i * increase_by_seconds * 10)
                if self.debug:
                    logging.debug(f'{response.status_code}: iter {i}: url {url}')
                continue
            if self.debug:
                logging.debug(f'{response.status_code}: iter {i}: url {url}')
            time.sleep(i * increase_by_seconds)

        return None

    def _get_request_params(
            self,
            url: str,
            headers: dict | list = None,
            cookies: dict | list = None,
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
        :param headers: dict | list = None
            Заголовки запроса, возможно передать в виде списка,
            тогда выбирутся рандомно
        :param cookies: dict | list = None
            Куки запроса, возможно передать в виде списка,
            тогда выбирутся рандомно
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

        random_index = random.randint(0, min(len(cookies), len(headers)) - 1)
        if type(headers) == list:
            headers = headers[random_index]
            if self.debug:
                logging.debug(f'Headers index: {random_index}')
        if type(cookies) == list:
            cookies = cookies[random_index]
            if self.debug:
                logging.debug(f'Cookies index: {random_index}')

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
