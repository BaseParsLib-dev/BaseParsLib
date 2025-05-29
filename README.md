# Библиотека BaseParsLib

Реализует:
* Асинхронные классы и классы, работающие с потоками. Backoff-запросы
* Асинхронные классы, работающие с различными браузерами
* Методы для работы с прокси
* Методы для работы с данными

# Навигация
 - [Окружение, установка и примеры использования](#окружение_установка_и_примеры_использования)
 - [Авторизация в ротационном прокси](#авторизация_в_ротационном_прокси)
 - [Класс BaseParser](#класс_baseparser)
 - [Применение методов BaseParser](#применение_методов_baseparser)
 - [Класс AsyncBaseParser](#класс_asyncbaseparser)
 - [Применение методов AsyncBaseParser](#применение_методов_asyncbaseparser)
 - [Класс AsyncPlaywrightBaseParser](#класс_asyncplaywrightbaseparser)
 - [Класс WebDriverBaseParser](#класс_webdriverbaseparser)
 - [Класс AsyncNodriverBaseParser](#класс_asyncnodriverbaseparser)
 - [Класс AsyncBaseCurlCffiParser](#класс_asyncbasecurlcffiparser)
 - [Класс AsyncCamoufoxBaseParser](#класс_asynccamoufoxbaseparser)
 - [Дополнительные методы библиотеки](#дополнительные_методы_библиотеки)
<br /> <br />

<a name="окружение_установка_и_примеры_использования"></a>
# Окружение, установка и примеры использования

### Версия Python
3.11

### Установка
```shell
pip install git+https://github.com/BaseParsLib-dev/BaseParsLib.git
```

<a name="авторизация_в_ротационном_прокси"></a>
### Авторизация в ротационном прокси
Ротация для прокси от webshare, может не работать с другими

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

<a name="класс_baseparser"></a>
# BaseParser
#### ```__init__```
    :param requests_session: = None
        объект requests.session()
    :param debug:
        Дебаг - вывод в консоль параметров отправляемых запросов и ответов
    :param print_logs:
        Если False - логи выводятся модулем logging, что не отображается на сервере в journalctl
        Если True - логи выводятся принтами
    :param check_exceptions: bool = False
        Позволяет посмотреть внутренние ошибки библиотеки, отключает все try/except конструкции,
        кроме тех, на которых завязана логика (например _calculate_random_cookies_headers_index)

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
    :param compare_headers_and_cookies_indexes: bool = True
        Если True, индекс для списков хедеров и куков будет одинаков:
            (если требуется, чтобы пары были обязательно вместе)
            Например:
            headers = [header1, header2, header3]
            cookies = [cookie1, cookie2, cookie3, cookie4]
            Случайно может выбраться 3 варианта - 1 и 1, 2 и 2, 3 и 3 (cookie4 выбран не будет)
        Если False, индексы будут случайны для каждого списка
    :param params: dict = False
        Словарь параметров запроса
    :param timeout: int | None = None
        Ограничение запроса по времени

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

<a name="применение_методов_baseparser"></a>
### Применение методов BaseParser

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

<a name="класс_asyncbaseparser"></a>
# AsyncBaseParser
#### ```__init__```
    :param debug: bool = False
        Дебаг - вывод в консоль параметров отправляемых запросов и ответов
    :param print_logs: bool = False
        Если False - логи выводятся модулем logging, что не отображается на сервере в journalctl
        Если True - логи выводятся принтами
    :param check_exceptions: bool = False
        Позволяет посмотреть внутренние ошибки библиотеки, отключает все try/except конструкции,
        кроме тех, на которых завязана логика (например __calculate_random_cookies_headers_index)

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
    :param data: list[dict] | dict | None = None,
        Список данных для отправки в теле запроса или один общий словарь
    :param json: list[dict] | dict | None = None,
        Список JSON-данных для отправки в теле запроса или один общий JSON
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
    :param timeout : int = 30
        Время максимального ожидания ответа
    :param random_sleep_time_every_request: list = False
        Список из 2-х чисел, рандомное между которыми - случайная задержка для каждого запроса
    :param params: dict | bool | None = None,
        Словарь параметров запроса
    :param get_raw_aiohttp_response_content: bool = False
        При True возвращает не модель AiohttpResponse, а просто контент из response.read()
    :param check_page: Callable = None
        Можно передать асинхронную функцию, в которой будут дополнительные проверки страницы
        (например на то, страница с капчей ли это)
        Функция обязательно должна принимать объект Response и возвращать
        True или False, где True - вернуть страницу, False - попытаться открыть заново
    :param check_page_args: dict | None = None
        Дополнительные параметры для check_page, если требуются

    :return:
        Возвращает список ответов от сайта.
        Какие-то из ответов могут быть None, если произошла ошибка из ignore_exceptions

        Класс ответа обладает следующими атрибутами:
            text: str
            json: dict | None
            url: str
            status: int

#### ```_method_in_series```
    Выполняет метод method для каждого чанка последовательно

    :param chunked_array: list | tuple
        Массив из чанков с url-ами или другими данными для запроса
    :param async_method:
        Асинхронный етод, который работает с чанком из переданного массива
        и сохраняет результаты во внешний массив
    :param sleep_time: int = 0
            Задержка между чанками запросов

    :return:
        None

<a name="применение_методов_asyncbaseparser"></a>
### Применение методов AsyncBaseParser

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

<a name="класс_asyncplaywrightbaseparser"></a>
# AsyncPlaywrightBaseParser
#### ```_method_in_series```
    Выполняет метод method для каждого чанка последовательно

    :param chunked_array: list | tuple
        Массив из чанков с url-ами или другими данными для запроса
    :param async_method:
        Асинхронный етод, который работает с чанком из переданного массива
        и сохраняет результаты во внешний массив
    :param sleep_time: int = 0
            Задержка между чанками запросов

    :return:
        None

#### ```_async_pages```
    :param pages_urls:
        Страницы, которые будут обрабатываться асинхронно
    :param page_method:
        Метод, который будет применяться для каждой странице
        (например, сбор каких-то данных)
        Обязательно должен принимать url в качестве аргумента

#### ```_backoff_open_new_page_on_context```
    Открывает страницу по переданному url,
    в случае ошибки открывает повторно через время

    !!! Для работы требуются созданный объект self.playwright: Playwright
    Также, если объекты self.browser: Browser и self.context: BrowserContext
    не созданы, автоматически примется with_new_context, и они создадутся

    :param url: str
        Ссылка на страницу
    :param check_page: Callable = None
        Можно передать асинхронную функцию, в которой будут дополнительные проверки страницы
        (например на то, страница с капчей ли это)
        Функция обязательно должна принимать объект страницы плейрайт (Page) и возвращать
        True или False, где True - вернуть страницу, False - попытаться открыть заново
    :param check_page_args: dict = None
        Дополнительные параметры для check_page
    :param load_timeout: int = 30
        Таймаут для загрузки страницы
    :param increase_by_seconds: int = 10
        Кол-во секунд, на которое увеличивается задержка между попытками
    :param iter_count: int = 10
        Кол-во попыток
    :param with_new_context: bool = False
        Создать новый контекст для открытия страницы
        (новый браузер с новым плейрайт-контекстом)
    :param load_img_mp4_mp3: bool = False
        Загружать картинки, видео, аудио
    :param headless_browser: bool = False
        Режим отображения браузера
    :param load_for_state: str = "networkidle"
        Загружать страницу до:
        networkidle - прекращения сетевой активности
        load - полной загрузки страницы
        domcontentloaded - загрузки dom
        None - сразу отдаёт страницу
    :param load_by_time: int = 0
        Количество секунд, сколько нужно ждать при переходе по ссылке
    :param catch_requests_handler: Callable = None
        Если передать метод, он будет срабатывать при каждом запросе от страницы.
        В качестве аргумента принимает request
    :param viewport_size: dict | None = None
        Размер окна в формате {"width": 1920, "height": 1080}

    :return:
        Объект страницы или None в случае, если за все попытки не удалось открыть

#### ```_scroll_to```
    Прокручивает страницу вниз на указанное количество пикселов или полностью

    :param page: Page
        Объект страницы
    :param from_: int = 0
        Старт, откуда начинаем прокрутку
    :param to: int | None = None:
        Количество пикселей, на которые скроллим
    :param full_page: bool = False
        Если True, страница прокрутится до конца
    :custom_js_code: str | None = None
        Есть возможность написать собственную логику скроллинга
    :return:
        None

#### ```_generate_new_context```
    Создаёт playwright-контекст - открывает браузер с начальной страницей поиска гугл
    (может быть полезно для некоторых сайтов, которые смотрят,
    откуда пользователь перешёл на их сайт)
    :param headless_browser: bool
        Булево значение, в скрытом ли режиме работает браузер
    :param user_agent:
        Можно передать собственный юзер-агент, в противном случае выберится случайный
        юзер-агент для пользователя на ПК
    :return:
        None

<a name="класс_webdriverbaseparser"></a>
# WebDriverBaseParser
#### ```__init__```
    param driver: WebDriver
        Драйвер селениума или аппиума
    :param timeout:
        Таймаут, который можно использовать в коде,
        чтобы дожидаться появления каких-то объектов
#### ```_get_element_with_wait```
    Получает элемент по какому-либо селениум-тегу (ID, название и т.д.)
    :param by:
        Селениум-тег. Можно передать, например AppiumBy.ID из
        from appium.webdriver.common.appiumby import AppiumBy
    :param element:
        Сам тег
    :return:
        WebElement

<a name="класс_asyncnodriverbaseparser"></a>
# AsyncNodriverBaseParser
#### ```backoff_open_new_page```
    Открывает страницу по переданному url,
    в случае ошибки открывает повторно через время

    !!! Для работы требуются созданный объект self.browser: Browser
    Если не создан, будет получена ошибка BrowserIsNotInitException

    :param url: str
        Ссылка на страницу
    :param check_page: Callable = None
        Можно передать асинхронную функцию, в которой будут дополнительные проверки страницы
        (например на то, страница с капчей ли это)
        Функция обязательно должна принимать объект страницы плейрайт (Page) и возвращать
        True или False, где True - вернуть страницу, False - попытаться открыть заново
    :param check_page_args: dict = None
        Дополнительные параметры для check_page
    :param load_timeout: int = 30
        Таймаут для загрузки страницы
    :param increase_by_seconds: int = 10
        Кол-во секунд, на которое увеличивается задержка между попытками
    :param iter_count: int = 10
        Кол-во попыток
    :param is_page_loaded_check: Callable = None
        Можно передать функцию проверки того, что страница загружена.
        В качестве первого параметра функция обязательно должна принимать объект страницы: Tab
    :param catch_requests_handler: Callable = None
        Если передать метод, он будет срабатывать при каждом запросе от страницы.
        В качестве аргумента принимает request.
        По дефолту запросы перехватывает cdp.network.RequestWillBeSent, но можно
        поменять на другой через параметр self.cdp_network_handler
    :param new_tab: bool = True
        Открыть в новой вкладке
    :param new_window: bool = False
        Открыть в новом окне браузера

    :return:
        Объект страницы или None в случае, если за все попытки не удалось открыть

#### ```__make_chrome_proxy_extension```

    Создаёт расширение с прокси для Nodriver

    :param host: str
        IP-адрес прокси
    :param port: int
        Порт прокси
    :param login: str
        Логин прокси
    :param password: str
        Пароль прокси
    :return:
        возвращает путь к папке с расширением, который
        после нужно зарегистрировать при старте браузера:
        browser_args=['--load-extension=<<PATH>>']

#### ```_make_request_from_page```
    Выполняет запрос через JS со страницы

    :param page: Tab
        Объект страницы
    :param url: str | list[str]
        Ссылка
        Если передан список ссылок, запросы отправятся асинхронно
    :param method: str
        HTTP-метод
    :param request_body: str | dict | None = None
        Тело запроса
    :return:
        Текст с запрашиваемой страницы

<a name="класс_asyncbasecurlcffiparser"></a>
# AsyncBaseCurlCffiParser
#### ```__init__```
    :param debug: bool = False
        Дебаг - вывод в консоль параметров отправляемых запросов и ответов
    :param print_logs: bool = False
        Если False - логи выводятся модулем logging, что не отображается на сервере в journalctl
        Если True - логи выводятся принтами
    :param check_exceptions: bool = False
        Позволяет посмотреть внутренние ошибки библиотеки, отключает все try/except конструкции,
        кроме тех, на которых завязана логика
        (например _calculate_random_cookies_headers_index)
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
    :param proxies: dict | None = None
        Прокси
    :param headers: dict | list = None
        Заголовки запроса, возможно передать в виде списка,
        тогда выбирутся рандомно
    :param cookies: dict | list = None
        Куки запроса, возможно передать в виде списка,
        тогда выбирутся рандомно
    :param data: list[dict] | dict | None = None,
        Список данных для отправки в теле запроса или один общий словарь
    :param json: list[dict] | dict | None = None,
        Список JSON-данных для отправки в теле запроса или один общий JSON
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
    :param params: dict | bool | None = None,
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
    :param check_page: Callable = Nonw
        Можно передать асинхронную функцию, в которой будут дополнительные проверки страницы
        (например на то, страница с капчей ли это)
        Функция обязательно должна принимать объект Response и возвращать
        True или False, где True - вернуть страницу, False - попытаться открыть заново
    :param check_page_args: dict | None = None
        Дополнительные параметры для check_page, если требуются

    :return:
        Возвращает список ответов от сайта.
        Какие-то из ответов могут быть None, если произошла ошибка из ignore_exceptions

<a name="класс_asynccamoufoxbaseparser"></a>
### AsyncCamoufoxBaseParser
#### Метод ```_backoff_create_browser```
    Создаёт браузер-менеджер и браузер

    :param proxy: dict[str, str] | None
        Прокси в формате:
        {
            "server": f"http://<host>:<port>",
            "username": <login>,
            "password": <password>,
        }
    :param headless: bool | str = "virtual"
        Показывать или не показывать окно браузера, значение
        virtual (поддерживается только в linux)
        создаёт виртуальный дисплей, что позволяет эмулировать экран в системе
    :param os: str = "linux"
        Возможность подменить ОС
    :param geoip: bool = True
        Браузер будет использовать долготу, ширину, часовой пояс, страну,
        локаль переданного прокси
    :param increase_by_seconds: int = 10
        Кол-во секунд, на которое увеличивается задержка между попытками
    :param iter_count: int = 10
        Кол-во попыток
    :return: Объект браузера

#### Метод ```_close_browser```
    Закрывает браузер, если он создан

#### Метод ```_backoff_open_new_page```
    Открывает страницу по переданному url,
    в случае ошибки открывает повторно через время

    !!! Для работы требуются созданный объект self.browser: Browser
    Если не создан, будет получена ошибка BrowserIsNotInitException

    :param url: str
        Ссылка на страницу
    :param check_page: Callable = None
        Можно передать асинхронную функцию, в которой будут дополнительные проверки страницы
        (например на то, страница с капчей ли это)
        Функция обязательно должна принимать объект страницы плейрайт (Page) и возвращать
        True или False, где True - вернуть страницу, False - попытаться открыть заново
    :param check_page_args: dict = None
        Дополнительные параметры для check_page
    :param load_timeout: int = 30
        Таймаут для загрузки страницы
    :param increase_by_seconds: int = 10
        Кол-во секунд, на которое увеличивается задержка между попытками
    :param iter_count: int = 10
        Кол-во попыток
    :param is_page_loaded_check: Callable = None
        Можно передать функцию проверки того, что страница загружена.
        В качестве первого параметра функция обязательно должна принимать объект страницы: Tab
    :param new_page_kwargs:
        Дополнительные аргументы для new_page()
    :return:
        Объект страницы или None в случае, если за все попытки не удалось открыть

#### Метод ```_make_request_from_page```
    Выполняет запрос через JS со страницы

    :param page: Tab
        Объект страницы
    :param url: str | list[str]
        Ссылка
        Если передан список ссылок, запросы отправятся асинхронно
    :param method: str
        HTTP-метод
    :param request_body: str | dict | None = None
        Тело запроса
    :return:
        Текст с запрашиваемой страницы

<a name="дополнительные_методы_библиотеки"></a>
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

#### Метод ```get_data_from_text```
    Функция вырезает нужную подстроку из строки

    :param text: str
        Основной текст
    :param start_row: str
        Левая граница, по которой вырезать
    :param end_row: str
        Правая граница, по которой вырезать
    :param cut_start_row: bool = True
        Обрезать левую границу
    :param cut_end_row: bool = True
        Обрезать правую границу
    :return: str

#### Метод ```split_dict_on_chunks_by_chunk_len```
    Делит словарь на чанки в зависимости от переданой длины чанка

    :param dictionary: dict
        Словарь, который нужно разделить на чанки
    :param chunk_len: int
        Размер чанка