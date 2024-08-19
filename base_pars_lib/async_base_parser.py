import asyncio
import random
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Callable

import aiohttp
import urllib3
from fake_useragent import UserAgent

from base_pars_lib.config import logger


@dataclass
class AiohttpResponse:
    text: str
    json: dict | None
    url: str
    status_code: int


class AsyncBaseParser:
    def __init__(
        self,
        debug: bool = False,
        print_logs: bool = False,
        check_exceptions: bool = False
    ) -> None:
        """
        :param debug: bool = False
            Дебаг - вывод в консоль параметров отправляемых запросов и ответов
        :param print_logs: bool = False
            Если False - логи выводятся модулем logging, что не отображается на сервере в journalctl
            Если True - логи выводятся принтами
        :param check_exceptions: bool = False
            Позволяет посмотреть внутренние ошибки библиотеки, отключает все try/except конструкции,
            кроме тех, на которых завязана логика
            (например __calculate_random_cookies_headers_index)
        """

        self.user_agent = UserAgent()

        self.ignore_exceptions = (
            urllib3.exceptions.ProxyError,
            aiohttp.client_exceptions.ClientConnectorError,
            aiohttp.client_exceptions.ServerDisconnectedError,
            aiohttp.client_exceptions.ClientOSError,
            aiohttp.client_exceptions.ClientHttpProxyError,
            asyncio.TimeoutError
        )

        self.check_exceptions = check_exceptions

        self.debug = debug
        self.print_logs = print_logs

        self.bad_urls: list = []

    async def __fetch(  # type: ignore[return]
            self,
            url: str,
            session: aiohttp.ClientSession,
            params: dict,
            ignore_exceptions: tuple | str = 'default',
            iter_count: int = 10,
            iter_count_for_50x_errors: int = 3,
            increase_by_seconds: int = 10,
            increase_by_minutes_for_50x_errors: int = 20,
            ignore_404: bool = False,
            long_wait_for_50x: bool = False,
            save_bad_urls: bool = False,
            random_sleep_time_every_request: list[float | int] | bool = False
    ) -> AiohttpResponse | None:
        """
        Отправляет запрос с настройками из _make_backoff_request

        :param url: str
            Ссылка на страницу
        :param session:
            Сессия aiohttp
        :param params:
            Параметры запроса из _make_backoff_request
        :param ignore_exceptions:
            Возможность передать ошибки, которые будут обрабатываться в backoff.
            Если ничего не передано, обрабатываются дефолтные:
                urllib3.exceptions.ProxyError
        :param iter_count:
            Количество попыток для запроса
        :param iter_count_for_50x_errors:
            Количество попыток, если сайт возвращает ошибку сервера
        :param increase_by_seconds:
            Разница в секундах между задержками
        :param increase_by_minutes_for_50x_errors:
            Разница в секундах между задержками, если сайт возвращает ошибку сервера
        :param ignore_404:
            Позволяет не применять backoff к респонзам со статус-кодом 404.
            Если такой страницы нет, backoff может не понадобиться
            Если значение = True и передан url на несуществующую страницу,
            метод вернёт response после первой попытки
        :param long_wait_for_50x:
            Если True, применяет increase_by_minutes_for_50x_errors
        :param save_bad_urls: bool = False
            Собирает ссылки, по которым ошибка или код не 200 в список self.bad_urls
        :param random_sleep_time_every_request: list = False
            Список из 2-х чисел, рандомное между которыми - случайная задержка для каждого запроса

        :return:
            Ответ от сайта. Если на протяжении всех попыток запросов сайт не отдавал код 200,
            на последней итерации вернёт последний ответ или None,
            если произошла ошибка из ignore_exceptions

            Класс ответа обладает следующими атрибутами:
                text: str
                json: dict | None
                url: str
                status: int
        """

        if random_sleep_time_every_request:
            await asyncio.sleep(
                random.uniform(
                    random_sleep_time_every_request[0],  # type: ignore[index]
                    random_sleep_time_every_request[1]  # type: ignore[index]
                )
            )

        iteration_for_50x = 1
        for i in range(1, iter_count + 1):
            try:
                async with session.request(url=url, **params) as response:
                    aiohttp_response = await self.__forming_aiohttp_response(response)

                    if aiohttp_response is None:
                        if self.debug:
                            logger.info_log(f'response is None, iter: {i}, {url}', self.print_logs)
                        await asyncio.sleep(i * increase_by_seconds)
                        continue

                    if aiohttp_response.status_code == HTTPStatus.OK or i == iter_count:
                        if save_bad_urls and aiohttp_response.status_code == HTTPStatus.OK:
                            await self._delete_from_bad_urls(url)
                        return aiohttp_response
                    if save_bad_urls and aiohttp_response.status_code != HTTPStatus.NOT_FOUND:
                        await self._append_to_bad_urls(url)
                    if aiohttp_response.status_code == HTTPStatus.NOT_FOUND and ignore_404:
                        return aiohttp_response

                    if 599 >= aiohttp_response.status_code >= 500 and long_wait_for_50x:
                        if iteration_for_50x > iter_count_for_50x_errors:
                            return aiohttp_response
                        iteration_for_50x += 1
                        if self.debug:
                            logger.backoff_status_code(
                                aiohttp_response.status_code, i, url, self.print_logs
                            )
                        await asyncio.sleep(i * increase_by_minutes_for_50x_errors * 60)
                        continue

                    if aiohttp_response.status_code != HTTPStatus.OK:
                        if self.debug:
                            logger.backoff_status_code(
                                aiohttp_response.status_code, i, url, self.print_logs
                            )
                        await asyncio.sleep(i * increase_by_seconds)
            except ignore_exceptions if not self.check_exceptions else () as Ex:
                if self.debug:
                    logger.backoff_exception(Ex, i, self.print_logs, url)
                if save_bad_urls:
                    await self._append_to_bad_urls(url)
                await asyncio.sleep(i * increase_by_seconds)
                continue

    async def _make_backoff_request(
            self,
            urls: list,
            method: str = 'GET',
            iter_count: int = 10,
            iter_count_for_50x_errors: int = 3,
            increase_by_seconds: int = 10,
            increase_by_minutes_for_50x_errors: int = 20,
            verify: bool = True,
            with_random_useragent: bool = True,
            proxies: str | None = None,
            headers: dict | list | None = None,
            cookies: dict | list | None = None,
            data: dict | None = None,
            json: dict | None = None,
            ignore_exceptions: tuple | str = 'default',
            ignore_404: bool = False,
            long_wait_for_50x: bool = False,
            save_bad_urls: bool = False,
            timeout: int = 30,
            random_sleep_time_every_request: list | bool = False,
            params: dict | bool = False
    ) -> tuple[AiohttpResponse | None]:
        """
        Если код ответа не 200 или произошла ошибка из ignore_exceptions, отправляет запрос повторно
        Задержка между каждым запросом увеличивается

        :param urls: list
            Список ссылок для запросов. Все ссылки обабатываются асинхронно одновременно
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
        :param proxies: str = None
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
                urllib3.exceptions.ProxyError
        :param ignore_404: bool = False
            Позволяет не применять backoff к респонзам со статус-кодом 404.
            Если такой страницы нет, backoff может не понадобиться
            Если значение = True и передан url на несуществующую страницу,
            метод вернёт response после первой попытки
        :param long_wait_for_50x: bool = False
            Если True, применяет increase_by_minutes_for_50x_errors
        :param save_bad_urls: bool = False
            Собирает ссылки, по которым ошибка или код не 200 в список self.bad_urls
        :param timeout : int = 30
            Время максимального ожидания ответа
        :param random_sleep_time_every_request: list = False
            Список из 2-х чисел, рандомное между которыми - случайная задержка для каждого запроса
        :param params: dict = False
            Словарь параметров запроса

        :return:
            Возвращает список ответов от сайта.
            Какие-то из ответов могут быть None, если произошла ошибка из ignore_exceptions

            Класс ответа обладает следующими атрибутами:
                text: str
                json: dict | None
                url: str
                status: int
        """

        if ignore_exceptions == 'default':
            ignore_exceptions = self.ignore_exceptions

        request_params = await self.__get_request_params(
            method, verify, with_random_useragent, proxies, headers, cookies, data, json,
            params
        )

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            tasks = [
                self.__fetch(
                    session=session,
                    url=url,
                    params=request_params,
                    ignore_exceptions=ignore_exceptions,
                    iter_count=iter_count,
                    iter_count_for_50x_errors=iter_count_for_50x_errors,
                    increase_by_seconds=increase_by_seconds,
                    increase_by_minutes_for_50x_errors=increase_by_minutes_for_50x_errors,
                    ignore_404=ignore_404,
                    long_wait_for_50x=long_wait_for_50x,
                    save_bad_urls=save_bad_urls,
                    random_sleep_time_every_request=random_sleep_time_every_request
                ) for url in urls
            ]
            return await asyncio.gather(*tasks)  # type: ignore[return-value]

    async def __get_request_params(
            self,
            method: str,
            verify: bool,
            with_random_useragent: bool,
            proxies: str | None,
            headers: dict | list | None,
            cookies: dict | list | None,
            data: dict | None,
            json: dict | None,
            params: dict | bool | None = None
    ) -> dict:
        """
        Возвращает словарь параметров для запроса через requests

        :param method: str
            requests-метод
        :param verify: bool
            Проверка безопасности сайта
        :param with_random_useragent: bool
            Использование рандомного юзерагента
        :param proxies: str
            Прокси
        :param headers: dict | list
            Заголовки запроса, возможно передать в виде списка,
            тогда выбирутся рандомно
        :param cookies: dict | list = None
            Куки запроса, возможно передать в виде списка,
            тогда выбирутся рандомно
        :param data: dict | None
            Данные запроса
        :param json: dict | None
            Данные запроса
        :param params: dict = False
            Словарь параметров запроса
        :return:
        """

        headers = {} if headers is None else headers
        cookies = {} if cookies is None else cookies

        random_index = await self.__calculate_random_cookies_headers_index(
            cookies=cookies, headers=headers
        )
        headers = await self.__get_by_random_index(headers, random_index, 'Headers')
        cookies = await self.__get_by_random_index(cookies, random_index, 'Cookies')

        if with_random_useragent:
            headers['User-Agent'] = self.user_agent.random

        request_params: dict = {
            'method': method.upper(),
            'headers': headers,
            'cookies': cookies,
            'ssl': verify,
            'data': data,
            'json': json
        }

        if proxies is not None:
            request_params['proxy'] = proxies
        if params:
            request_params['params'] = params

        return request_params

    async def __get_by_random_index(
            self,
            item: list[dict] | dict,
            random_index: int,
            item_name: str
    ) -> dict:
        if type(item) is list:
            item = item[random_index]
            if self.debug:
                logger.info_log(f'{item_name} index: {random_index}', self.print_logs)
        return item  # type: ignore[return-value]

    async def _append_to_bad_urls(self, url: Any) -> None:
        if url not in self.bad_urls:
            self.bad_urls.append(url)

    async def _delete_from_bad_urls(self, url: Any) -> None:
        if url in self.bad_urls:
            self.bad_urls.remove(url)

    @staticmethod
    async def __calculate_random_cookies_headers_index(
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

    async def __forming_aiohttp_response(self, response: Any) -> AiohttpResponse | None:
        try:
            text = await response.text()
            try:
                json = await response.json()
            except aiohttp.client_exceptions.ContentTypeError:
                json = None
            response_url = str(response.url)
            status = response.status
            return AiohttpResponse(text=text, json=json, url=response_url, status_code=status)
        except Exception if not self.check_exceptions else () as Ex:
            logger.info_log(f'forming AiohttpResponse error {Ex}', self.print_logs)
            return None

    @staticmethod
    async def _method_in_series(
            chunked_array: list | tuple,
            async_method: Callable,
            sleep_time: int = 0
    ) -> None:
        """
        Выполняет метод method для каждого чанка последовательно

        :param chunked_array: list | tuple
            Массив из чанков с url-ами или другими данными для запроса
            Чанки созданы для того, чтобы не отправлять слишком много запросов одновременно,
            чанки обрабатываются последовательно, запросы по ссылкам внутри них - одновременно
        :param async_method:
            Асинхронный метод, который работает с чанком из переданного массива
            и сохраняет результаты во внешний массив
        :param sleep_time: int = 0
            Задержка между чанками запросов

        :return:
            None
        """

        for chunk in chunked_array:
            await async_method(chunk)
            await asyncio.sleep(sleep_time)
