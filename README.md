# Библиотека BaseParsLib

Реализует:
* Класс BaseParser, работающий с потоками и отправляющий backoff-запросы
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

### Методы BaseParser
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

#### Метод ```_make_request```
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
