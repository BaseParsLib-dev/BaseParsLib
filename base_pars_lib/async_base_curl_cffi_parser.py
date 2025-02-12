import asyncio
import random

import curl_cffi
import urllib3
from curl_cffi.requests import AsyncSession
from curl_cffi.requests.models import Response
from fake_useragent import UserAgent

from base_pars_lib.config import logger
from base_pars_lib.core.async_requests_parser_base import AsyncRequestsParserBase


class AsyncBaseCurlCffiParser(AsyncRequestsParserBase):
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
            (например _calculate_random_cookies_headers_index)
        """

        super().__init__()
        self.user_agent = UserAgent()

        self.ignore_exceptions = (
            urllib3.exceptions.ProxyError,
            asyncio.TimeoutError,
            curl_cffi.requests.exceptions.ConnectionError
        )

        self.check_exceptions = check_exceptions

        self.debug = debug
        self.print_logs = print_logs

    async def __fetch(
            self,
            url: str,
            session: AsyncSession,
            params: dict,
            ignore_exceptions: tuple | str = 'default',
            iter_count: int = 10,
            iter_count_for_50x_errors: int = 3,
            increase_by_seconds: int = 10,
            increase_by_minutes_for_50x_errors: int = 20,
            ignore_404: bool = False,
            long_wait_for_50x: bool = False,
            save_bad_urls: bool = False,
            random_sleep_time_every_request: list[float | int] | bool = False,
            impersonate: str | None = None,
    ) -> Response | None:
        """
        Отправляет запрос с настройками из _make_backoff_request

        :param url: str
            Ссылка на страницу
        :param session:
            Сессия curl-cffi
        :param params:
            Параметры запроса из _make_backoff_request
        :param ignore_exceptions:
            Возможность передать ошибки, которые будут обрабатываться в backoff.
            Если ничего не передано, обрабатываются дефолтные
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
        :param impersonate: str | None = None
            Имитируемый браузер, если None, выбирается рандомно для каждого запроса из:
                "chrome",
                "edge",
                "safari",
                "safari_ios",
                "chrome_android"
            Можно передать свой. Можно так же передать название с версией - "chrome107",
            но не рекоммендуется. Если не использовать версию, ставится автоматически последняя

        :return:
            Ответ от сайта. Если на протяжении всех попыток запросов сайт не отдавал код 200,
            на последней итерации вернёт последний ответ или None,
            если произошла ошибка из ignore_exceptions
        """

        if random_sleep_time_every_request:
            await asyncio.sleep(
                random.uniform(
                    random_sleep_time_every_request[0],  # type: ignore[index]
                    random_sleep_time_every_request[1]  # type: ignore[index]
                )
            )
        if impersonate is None:
            impersonate = await self.__get_random_impersonate()
            if self.debug:
                logger.info_log(
                    f'impersonate: {impersonate}',
                    print_logs=self.print_logs
                )

        iteration_for_50x = 1
        for i in range(1, iter_count + 1):
            try:
                response = await session.request(url=url, impersonate=impersonate, **params)  # type: ignore[arg-type]
                is_cycle_end, response_ = await self._check_response(
                    response=response,
                    iteration=i,
                    url=url,
                    increase_by_seconds=i,
                    iter_count=iter_count,
                    save_bad_urls=save_bad_urls,
                    ignore_404=ignore_404,
                    long_wait_for_50x=long_wait_for_50x,
                    iteration_for_50x=iteration_for_50x,
                    iter_count_for_50x_errors=iter_count_for_50x_errors,
                    increase_by_minutes_for_50x_errors=increase_by_minutes_for_50x_errors
                )
                if is_cycle_end:
                    return response_  # type: ignore[return-value]
            except ignore_exceptions if not self.check_exceptions else () as Ex:
                if self.debug:
                    logger.backoff_exception(Ex, i, self.print_logs, url)
                if save_bad_urls:
                    await self._append_to_bad_urls(url)
                await asyncio.sleep(i * increase_by_seconds)
                continue

        return None

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
            proxies: dict | None = None,
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
            params: dict | bool = False,
            impersonate: str | None = None,
            debug_curl_cffi: bool = False,
            match_headers_to_urls: bool = False,
            match_cookies_to_urls: bool = False
    ) -> tuple[Response | None]:
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
        :param proxies: dict | None = None
            Прокси
        :param headers: dict | list = None
            Заголовки запроса, возможно передать в виде списка,
            тогда выберутся рандомно
        :param cookies: dict | list = None
            Куки запроса, возможно передать в виде списка,
            тогда выберутся рандомно
        :param data: dict = None
            Передаваемые данные
        :param json: dict = None
            Передаваемые данные
        :param ignore_exceptions: tuple = 'default'
            Возможность передать ошибки, которые будут обрабатываться в backoff.
            Если ничего не передано, обрабатываются дефолтные
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
        :param impersonate: str | None = None
            Имитируемый браузер, если None, выбирается рандомно для каждого запроса из:
                "chrome",
                "edge",
                "safari",
                "safari_ios",
                "chrome_android"
            Можно передать свой. Можно так же передать название с версией - "chrome107",
            но не рекоммендуется. Если не использовать версию, ставится автоматически последняя
        :param debug_curl_cffi: bool = False
            Дебаг от curl-cffi, выводит подробную информацию о каждом запросе.
            Не зависит от debug, передаваемый при инициализации класса
        :param match_headers_to_urls: bool = False
            Если True, каждому URL из списка будет соответствовать свой header (по порядку).
            Если False, header выбирается рандомно.
        :param match_cookies_to_urls: bool = False
            Если True, каждому URL из списка будет соответствовать свой cookie (по порядку).
            Если False, cookie выбирается рандомно.

        :return:
            Возвращает список ответов от сайта.
            Какие-то из ответов могут быть None, если произошла ошибка из ignore_exceptions
        """

        if ignore_exceptions == 'default':
            ignore_exceptions = self.ignore_exceptions

        async with AsyncSession(
                max_clients=len(urls),
                timeout=timeout,
                debug=debug_curl_cffi
        ) as session:
            tasks = []

            for i, url in enumerate(urls):

                # Выбор хэдеров: соответствие URL или случайный
                if isinstance(headers, list):
                    if match_headers_to_urls and len(headers) == len(urls):
                        current_headers = headers[i]
                    else:
                        current_headers = random.choice(headers)
                else:
                    current_headers = headers

                # Выбор куков: соответствие URL или случайный
                if isinstance(cookies, list):
                    if match_cookies_to_urls and len(cookies) == len(urls):
                        current_cookies = cookies[i]
                    else:
                        current_cookies = random.choice(cookies)
                else:
                    current_cookies = cookies

                request_params = await self.__get_request_params(
                    method, verify, with_random_useragent, proxies, current_headers, current_cookies, data, json, params
                )

            tasks.append(self.__fetch(
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
                    random_sleep_time_every_request=random_sleep_time_every_request,
                    impersonate=impersonate
                ))

            return await asyncio.gather(*tasks)  # type: ignore[return-value]

    async def __get_request_params(
            self,
            method: str,
            verify: bool,
            with_random_useragent: bool,
            proxies: dict | None,
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
        :param proxies: dict
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

        random_index = await self._calculate_random_cookies_headers_index(
            cookies=cookies, headers=headers
        )
        headers = await self._get_by_random_index(headers, random_index, 'Headers')
        cookies = await self._get_by_random_index(cookies, random_index, 'Cookies')

        if with_random_useragent:
            headers['User-Agent'] = self.user_agent.random

        request_params: dict = {
            'method': method.upper(),
            'headers': headers,
            'cookies': cookies,
            'verify': verify,
            'data': data,
            'json': json
        }

        if proxies is not None:
            request_params['proxies'] = proxies
        if params:
            request_params['params'] = params

        return request_params

    @staticmethod
    async def __get_random_impersonate() -> str:
        return random.choice(['chrome', 'edge', 'safari', 'safari_ios', 'chrome_android'])
