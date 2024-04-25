from http import HTTPStatus
import random
from threading import Thread
import time

import requests
from fake_useragent import UserAgent
import urllib3

from base_pars_lib import _requests_digest_proxy
from base_pars_lib.config import logger


class BaseParser:
    def __init__(self, requests_session=None, debug: bool = False, print_logs: bool = False):
        """
        :param requests_session: = None
            объект requests.session()
        :param debug:
            Дебаг - вывод в консоль параметров отправляемых запросов и ответов
        :param print_logs:
            Если False - логи выводятся модулем logging, что не отображается на сервере в journalctl
            Если True - логи выводятся принтами
        """

        self.requests_session = requests_session

        self.user_agent = UserAgent()

        self.ignore_exceptions = (
            requests.exceptions.ProxyError,
            _requests_digest_proxy.ProxyError,
            urllib3.exceptions.ProxyError,
            requests.exceptions.ConnectionError
        )

        self.debug = debug
        self.print_logs = print_logs

    def _make_request(self, params: dict, from_one_session=True):
        """
        Отправляет реквест через requests_session

        :param params: dict
            Параметры запроса, поступающие из _make_backoff_request
        :param from_one_session: bool = True
            Использование одной сессии

        :return:
            response
        """

        if from_one_session:
            response = self.requests_session.request(**params)
        else:
            response = requests.request(**params)
        if self.debug:
            logger.info_log(f'_make_request status code: {response.status_code}', self.print_logs)
        return response

    def _make_backoff_request(
            self,
            url: str,
            method: str = 'GET',
            iter_count: int = 10,
            iter_count_for_50x_errors: int = 3,
            increase_by_seconds: int = 10,
            increase_by_minutes_for_50x_errors: int = 20,
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
        :param iter_count_for_50x_errors: int = 3
            Количество попыток отправки запроса для 500-х ошибок
        :param increase_by_seconds: int = 10
            Значение, на которое увеличивается время ожидания
            на каждой итерации
        :param increase_by_minutes_for_50x_errors: int = 20
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
        :param long_wait_for_50x: bool = False
            Если True, применяет increase_by_minutes_for_50x_errors

        :return:
            На последней итерации возвращает response с
            любым кодом ответа или, если произошла ошибка Proxy - возвращает None
        """

        if ignore_exceptions == 'default':
            ignore_exceptions = self.ignore_exceptions

        params = self._get_request_params(
            url, headers, cookies, with_random_useragent,
            method, verify, json, data, proxies
        )

        iteration_for_50x = 1
        for i in range(1, iter_count + 1):
            try:
                response = self._make_request(
                    from_one_session=from_one_session, params=params
                )
            except ignore_exceptions as Ex:
                if self.debug:
                    logger.backoff_exception(Ex, i, self.print_logs)
                time.sleep(i * increase_by_seconds)
                continue

            if response.status_code == HTTPStatus.OK or i == iter_count:
                return response
            elif response.status_code == HTTPStatus.NOT_FOUND and ignore_404:
                return response
            elif 599 >= response.status_code >= 500 and long_wait_for_50x:
                if iteration_for_50x > iter_count_for_50x_errors:
                    return response
                iteration_for_50x += 1
                if self.debug:
                    logger.backoff_status_code(response.status_code, i, url, self.print_logs)
                time.sleep(i * increase_by_minutes_for_50x_errors * 60)
                continue

            if self.debug:
                logger.backoff_status_code(response.status_code, i, url, self.print_logs)
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
            json: dict | str = None,
            data: dict | str = None,
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

        random_index = self._calculate_random_cookies_headers_index(
            cookies=cookies, headers=headers
        )
        headers = self._get_by_random_index(headers, random_index, 'Headers')
        cookies = self._get_by_random_index(cookies, random_index, 'Cookies')

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

    def _get_by_random_index(
            self,
            item: list[dict] | dict,
            random_index: int,
            item_name: str
    ) -> dict:
        if type(item) == list:
            item = item[random_index]
            if self.debug:
                logger.info_log(f'{item_name} index: {random_index}', self.print_logs)
        return item

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

    @staticmethod
    def _calculate_random_cookies_headers_index(
            cookies: list[dict] | dict,
            headers: list[dict] | dict
    ) -> int:
        upper_index = min(len(cookies), len(headers))
        if not upper_index:
            upper_index = max(len(cookies), len(headers))
        try:
            return random.randint(0, upper_index - 1)
        except ValueError:
            return 0
