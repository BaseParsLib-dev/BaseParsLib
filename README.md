# Библиотека BaseParsLib

Реализует:
* Класс BaseParser, работающий с потоками и отправляющий backoff-запросы
* Класс AsyncBaseParser, работающий асинхронно и отправляющий backoff-запросы
* Метод rotating_proxy_auth, авторизующийся в ротационном прокси
* Методы для работы с данными

# Установка и примеры использования

```shell
pip install git+https://github.com/BaseParsLib-dev/BaseParsLib.git
```

### Авторизация в ротационном прокси

```python
from base_pars_lib.utils import rotating_proxy_auth

proxy_session = rotating_proxy_auth(
    http_url='http_url',
    https_url='https_url',
    login='login',
    password='password'
)
```
Реализует правильную авторизацию в ротационном прокси в файле ```base_pars_lib._requests_digest_proxy```, который 
переопределяет некоторые методы библиотеки requests

# BaseParser
#### ```__init__```
    :param requests_session: = None
        объект requests.session()
    :param debug: 
        Дебаг - вывод в консоль параметров отправляемых запросов и ответов
    :param print_logs: 
        Если False - логи выводятся модулем logging, что не отображается на сервере в journalctl
        Если True - логи выводятся принтами

#### Метод ```_threading_method```
    Создаёт столько потоков, сколько чанков передано в chunked_array, выполняет метод method 
    для каждого чанка в отдельном потоке

        :param chunked_array: list | tuple 
            Массив из чанков с url-ами или другими данными для запроса
        :param method:
            Метод, который работает с чанком из переданного массива и сохраняет результаты 
            во внешний массив

        :return:
            None

#### Метод ```_make_backoff_request```
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
        :param save_bad_urls: bool = False
            Собирает ссылки, по которым ошибка или код не 200 и не 404 в список self.bad_urls.
            Если по ссылке код 200, удаляет её из списка (это позволяет использовать этот список повторно несколько раз)

        :return:
            На последней итерации возвращает response с
            любым кодом ответа или, если произошла ошибка Proxy - возвращает None

#### Метод ```_make_request```
    Отправляет реквест через requests_session

    :param params: dict
        Параметры запроса, поступающие из _make_backoff_request
    :param from_one_session: bool = True
        Использование одной сессии

    :return:
        response

### Дополнительные методы библиотеки
#### Метод ```split_on_chunks_by_chunk_len```
    Делит массив на чанки в зависимости от переданой длины чанка
    
    :param array: list | tuple
        Массив, который нужно разделить на чанки
    :param chunk_len: int
        Размер чанка

#### Метод ```split_on_chunks_by_count_chunks```
    Делит массив на чанки в зависимости от переданого количества чанков

    :param array: list | tuple
        Массив, который нужно разделить на чанки
    :param count_chunks: int
        Количество чанков    

### Применение методов библиотеки

```python
from base_pars_lib import BaseParser
from base_pars_lib.utils import split_on_chunks_by_chunk_len


class MyParser(BaseParser):
    """Пользовательский класс парсера"""

    def __init__(self, requests_session):
        super().__init__(requests_session)

        self.my_responses = []

    def my_method_get_all_data(self, urls: list | tuple):
        """Пользовательский метод, получающий данные с сайта"""

        chunked_urls = split_on_chunks_by_chunk_len(
            array=urls,
            chunk_len=10
        )

        self._threading_method(
            chunked_array=chunked_urls,
            method=self._my_method_get_responses
        )

    def _my_method_get_responses(self, urls: list | tuple) -> None:
        for url in urls:
            response = self._make_backoff_request(
                method='GET',
                url=url,
                iter_count=10,
                increase_by_seconds=10,
                verify=True,
                with_random_useragent=True
            )

            if response is None:
                # response None в том случае, если Proxy-сервис отдаёт ошибку
                # пользовательская логика обработки таких респонзов
                continue
            elif response.status_code != 200:
                # Пользовательская логика обработки таких респонзов
                continue
            else:
                self.my_responses.append(response)
```

#### Передача proxy в запрос вручную
```python
from base_pars_lib import BaseParser


class MyParser(BaseParser):
    
    proxies = {
        'http': f'http://username:password@proxy_dns'
    }
    
    def get_my_ip(self):
        return self._make_backoff_request(
            url='http://api.ipify.org/?format=json',
            from_one_session=False,
            proxies=self.proxies
        )
```

# AsyncBaseParser
#### ```__init__```
    :param debug:
        Дебаг - вывод в консоль параметров отправляемых запросов и ответов
    :param print_logs:
        Если False - логи выводятся модулем logging, что не отображается на сервере в journalctl
        Если True - логи выводятся принтами

#### ```_make_backoff_request```
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
        Собирает ссылки, по которым ошибка или код не 200 и не 404 в список self.bad_urls.
        Если по ссылке код 200, удаляет её из списка (это позволяет использовать этот список повторно несколько раз)

    :return:
        Возвращает список ответов от сайта.
        Какие-то из ответов могут быть None, если произошла ошибка из ignore_exceptions

        Класс ответа обладает следующими атрибутами:
            text: str
            json: dict | None
            url: str
            status: int

#### ```_coroutines_method```
    Создаёт столько корутин, сколько чанков передано в chunked_array,
    выполняет метод method для каждого чанка в отдельной корутине

    :param chunked_array: list | tuple
        Массив из чанков с url-ами или другими данными для запроса
    :param async_method:
        Асинхронный етод, который работает с чанком из переданного массива
        и сохраняет результаты во внешний массив

    :return:
        None

### Применение методов библиотеки
100 запросов отправляются асинхронно, но по чанкам по 10 штук (как указано в пользовательском методе run)
```python
import asyncio
import time

from base_pars_lib import AsyncBaseParser
from base_pars_lib.utils import split_on_chunks_by_count_chunks


class MyParser(AsyncBaseParser):
    responses = []

    async def run(self, urls: list) -> list:
        chunked_urls = split_on_chunks_by_count_chunks(urls, 10)
        await self._method_in_series(chunked_urls, self.make_requests)

        return self.responses

    async def make_requests(self, chunk):
        print(chunk)
        self.responses += await self._make_backoff_request(
            urls=chunk,
            proxies='http://login:password@proxy_dns'
        )


if __name__ == '__main__':
    start = time.time()
    responses = asyncio.run(
        MyParser().run(urls=['http://api.ipify.org/?format=json'] * 100)
    )
    print(time.time() - start)
    print(responses)
```
