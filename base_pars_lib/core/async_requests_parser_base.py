import asyncio
import random
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Callable

from curl_cffi.requests.models import Response

from base_pars_lib.config import logger


@dataclass
class AiohttpResponse:
    text: str
    json: dict | None
    url: str
    status_code: int


class AsyncRequestsParserBase:
    def __init__(self) -> None:
        self.debug: bool = False

        self.print_logs: bool = False

        self.bad_urls: list[Any] = []

    # TODO: Переписать под паттерн цепочка обязанностей
    #  (https://refactoring.guru/ru/design-patterns/chain-of-responsibility)
    #  очень запутаный код
    async def _check_response(
        self,
        response: None | AiohttpResponse | Response,
        iteration: int,
        url: str,
        increase_by_seconds: int,
        iter_count: int,
        save_bad_urls: bool,
        ignore_404: bool,
        long_wait_for_50x: bool,
        iteration_for_50x: int,
        iter_count_for_50x_errors: int,
        increase_by_minutes_for_50x_errors: int,
        check_page: Callable,
        check_page_args: dict | None,
    ) -> tuple[bool, None | AiohttpResponse | Response]:
        """
        Метод выполняется в теле цикла и проверяет респонз. Позвращает кортеж, в котором:
            bool - завершать цикл или нет (валидный респонз или нет)
            AiohttpResponse | Response - сам респонз
        """

        if iteration == iter_count:
            return True, response

        if response is None:
            if self.debug:
                logger.info_log(f"response is None, iter: {iteration}, {url}", self.print_logs)
            await asyncio.sleep(iteration * increase_by_seconds)
            return False, None

        if response.status_code == HTTPStatus.OK:
            if check_page is not None:
                if check_page_args is not None:
                    check_page_status = await check_page(response, **check_page_args)
                else:
                    check_page_status = await check_page(response)
                if check_page_status:
                    if save_bad_urls:
                        await self._delete_from_bad_urls(url)
                    return True, response
                else:
                    if self.debug:
                        logger.info_log(
                            "check_page returned False, iter: {iteration}, {url}", self.print_logs
                        )
                        await asyncio.sleep(iteration * increase_by_seconds)
                    return False, response
            else:
                if save_bad_urls:
                    await self._delete_from_bad_urls(url)
                return True, response
        if save_bad_urls and response.status_code != HTTPStatus.NOT_FOUND:
            await self._append_to_bad_urls(url)
        if response.status_code == HTTPStatus.NOT_FOUND and ignore_404:
            return True, response

        if 599 >= response.status_code >= 500 and long_wait_for_50x:
            if iteration_for_50x == iter_count_for_50x_errors:
                return True, response
            iteration_for_50x += 1
            if self.debug:
                logger.backoff_status_code(response.status_code, iteration, url, self.print_logs)
            await asyncio.sleep(iteration * increase_by_minutes_for_50x_errors * 60)
            return False, None

        if response.status_code != HTTPStatus.OK:
            if self.debug:
                logger.backoff_status_code(response.status_code, iteration, url, self.print_logs)
            await asyncio.sleep(iteration * increase_by_seconds)

        return False, None

    async def _append_to_bad_urls(self, url: Any) -> None:
        if url not in self.bad_urls:
            self.bad_urls.append(url)

    async def _delete_from_bad_urls(self, url: Any) -> None:
        if url in self.bad_urls:
            self.bad_urls.remove(url)

    async def _get_by_random_index(
        self, item: list[dict] | dict, random_index: int, item_name: str
    ) -> dict:
        if isinstance(item, list):
            item = item[random_index]
            if self.debug:
                logger.info_log(f"{item_name} index: {random_index}", self.print_logs)
        return item  # type: ignore[return-value]

    @staticmethod
    async def _method_in_series(
        chunked_array: list | tuple, async_method: Callable, sleep_time: int = 0
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

    @staticmethod
    async def _calculate_random_cookies_headers_index(
        cookies: list[dict] | dict, headers: list[dict] | dict
    ) -> int:
        upper_index = min(len(cookies), len(headers))
        if not upper_index:
            upper_index = max(len(cookies), len(headers))
        try:
            return random.randint(0, upper_index - 1)
        except ValueError:
            return 0

    @staticmethod
    def _select_value(
        value: dict | list | None, match_to_urls: bool, index: int, urls_length: int
    ) -> Any:
        """
        Выбирает значение (headers/cookies) для запроса.

        :param value: dict | list | None - headers или cookies.
        :param match_to_urls: bool - Нужно ли привязывать к URL.
        :param index: int - Текущий индекс URL.
        :param urls_length: int - Длина списка URL.
        :return: dict | None - Выбранное значение headers или cookies.
        """
        if isinstance(value, list):
            if match_to_urls and len(value) == urls_length:
                return value[index]
            return random.choice(value)
        return value

    @staticmethod
    async def _prepare_request_data(
        urls: list, data: list[dict | None] | dict | None, json: list[dict | None] | dict | None
    ) -> tuple[int, int, list[dict | None], list[dict | None]]:
        """
        Подготавливает данные для запросов, нормализуя их в соответствии с количеством url |
        data | json.

        :param urls:
            Список ссылок.
        :param data:
            Список данных для отправки в теле запроса или один общий словарь.
        :param json:
            Список JSON-данных для отправки в теле запроса или один общий словарь.
        :return:
             Кортеж из четырёх элементов:
            - url_count: Количество URL в переданном списке.
            - max_requests: Максимальное количество запросов, определяемое как наибольшее из:
                - количества URL,
                - количества элементов в data (если data является списком),
                - количества элементов в json (если json является списком).
            - data_list: Список данных для data. Если data не был списком, он дублируется
              до длины max_requests.
            - json_list: Список данных для JSON. Если json не был списком, он дублируется
              до длины max_requests.
        """

        url_count = len(urls)
        max_requests = max(
            len(data) if isinstance(data, list) else 0,
            len(json) if isinstance(json, list) else 0,
            url_count,
        )

        data_list = data if isinstance(data, list) else [data] * max_requests
        json_list = json if isinstance(json, list) else [json] * max_requests

        return url_count, max_requests, data_list, json_list
