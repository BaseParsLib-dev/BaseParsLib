# type: ignore

"""
Переопределяет методы библиотеки requests,
реализует правильную работу ротационного прокси
"""


import sys
import re

if sys.version_info[0] == 2:
    import httplib
    import urlparse
else:
    import http.client as httplib
    import urllib.parse as urlparse

import requests
from requests.packages import urllib3


def dbg_print(fmt, *args):
    if False:
        sys.stderr.write(fmt % args)
        sys.stderr.write("\n")


class HTTPProxyDigestAuth(requests.auth.HTTPDigestAuth):
    def __init__(self, username, password, auth=None):
        super(HTTPProxyDigestAuth, self).__init__(username, password)

        self.auth = auth

    def build_digest_header(self, method, url):
        url_parsed = urlparse.urlparse(url)
        if url_parsed.scheme.lower() == 'https':
            if url_parsed.port is None:
                url = url_parsed.netloc + ':443'
            else:
                url = url_parsed.netloc
            method = 'CONNECT'

        return super(HTTPProxyDigestAuth, self).build_digest_header(method, url)

    def handle_401(self, r, **kwargs):
        if r.status_code != 407:
            self._thread_local.num_401_calls = 1
            return r

        dbg_print("handle_407")

        if self._thread_local.pos is not None:
            r.request.body.seek(self._thread_local.pos)
        s_auth = r.headers.get('proxy-authenticate', '')

        if 'digest' in s_auth.lower() and self._thread_local.num_401_calls < 2:
            self._thread_local.num_401_calls += 1
            pat = re.compile(r'digest ', flags=re.IGNORECASE)
            self._thread_local.chal = requests.utils.parse_dict_header(
                pat.sub('', s_auth, count=1))
            r.content
            r.close()
            prep = r.request.copy()
            requests.cookies.extract_cookies_to_jar(prep._cookies, r.request, r.raw)
            prep.prepare_cookies(prep._cookies)

            prep.headers['Proxy-Authorization'] = self.build_digest_header(prep.method, prep.url)
            _r = r.connection.send(prep, **kwargs)
            _r.history.append(r)
            _r.request = prep

            return _r

        self._thread_local.num_401_calls = 1
        return r

    def __call__(self, r):
        self.init_per_thread_state()
        if self._thread_local.last_nonce:
            r.headers['Proxy-Authorization'] = self.build_digest_header(r.method, r.url)
        try:
            self._thread_local.pos = r.body.tell()
        except AttributeError:
            self._thread_local.pos = None
        r.register_hook('response', self.handle_401)
        r.register_hook('response', self.handle_redirect)
        self._thread_local.num_401_calls = 1

        if self.auth is not None:
            r = self.auth(r)

        return r


def hook(cls, name=None):
    def decorator(func):
        import functools

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(original, *args, **kwargs)

        if name is None:
            g = globals()
            original = g[cls]
            g[cls] = wrapper
        else:
            def dummy(*args, **kwargs):
                pass

            original = getattr(cls, name, dummy)
            setattr(cls, name, wrapper)

        return wrapper

    return decorator


def hook_trace(cls, name=None):
    path = cls if name is None else (cls.__name__ + '.' + name)

    def print_trace(original, *args, **kwargs):
        dbg_print('TRACE<%s>', path)
        return original(*args, **kwargs)

    hook(cls, name)(print_trace)


class ProxyError(RuntimeError):
    pass


class HTTPProxyResponse(httplib.HTTPResponse):
    _status_line = None

    def __init__(self, sock, *args, **kwargs):
        httplib.HTTPResponse.__init__(self, sock, *args, **kwargs)
        if sys.version_info[0] == 2:
            self.fp = sock.makefile('rb', 0)
        else:
            self.fp = sock.makefile("rb", buffering=0)

    def _read_status(self):
        (version, status, reason) = httplib.HTTPResponse._read_status(self)
        dbg_print(str((version, status, reason)))

        if status == 407:
            self._status_line = (version, status, reason)
            raise ProxyError()

        return (version, status, reason)


class BufferedHTTPResponse(httplib.HTTPResponse):
    _status_line = None

    def _read_status(self):
        dbg_print('%s', self.fp)
        return self._status_line

    def _check_close(self):
        res = httplib.HTTPResponse._check_close(self)
        dbg_print("_check_close => %s", res)
        return True


@hook(httplib.HTTPConnection, '_tunnel')
def HTTPConnection__tunnel_hook(original, self, *args, **kwargs):
    resp = [None]

    def resp_builder(*args, **kwargs):
        dbg_print('HTTPProxyResponse.__init__')
        resp[0] = r = HTTPProxyResponse(*args, **kwargs)
        return r

    response_class = self.response_class
    self.response_class = resp_builder

    try:
        original(self, *args, **kwargs)
    finally:
        resp = resp[0]
        if resp is not None and resp._status_line is not None:
            self._status_line = resp._status_line

        self.response_class = response_class


@hook(urllib3.connection.HTTPSConnection, 'connect')
def urllib3_connection_HTTPSConnection_connect_hook(original, self, *args, **kwargs):
    # Reset
    self._status_line = None

    try:
        original(self, *args, **kwargs)
    except ProxyError as e:
        dbg_print("ProxyError")
        self.is_verified = True

        def resp_builder(*args, **kwargs):
            dbg_print('BufferedHTTPResponse.__init__')
            r = BufferedHTTPResponse(*args, **kwargs)
            r._status_line = self._status_line
            self.response_class = response_class
            return r

        response_class = self.response_class
        self.response_class = resp_builder


@hook(urllib3.connection.HTTPConnection, 'send')
def urllib3_connection_HTTPConnection_send_hook(original, self, *args, **kwargs):
    if self._status_line is not None:
        dbg_print("send(%d)", len(args[0]))
        pass
    else:
        return original(self, *args, **kwargs)


@hook(urllib3.connection.HTTPConnection, '__init__')
def urllib3_connection_HTTPConnection___init___hook(original, self, *args, **kwargs):
    self._status_line = None
    return original(self, *args, **kwargs)


@hook(urllib3.connectionpool.HTTPConnectionPool, 'urlopen')
def urllib3_connectionpool_HTTPConnectionPool_urlopen_hook(original, self, *args, **kwargs):
    headers = kwargs.get('headers', self.headers)
    for (name, value) in list(headers.items()):
        if name.lower() == 'proxy-authorization':
            del headers[name]
            self.proxy_headers[name] = value
            dbg_print("<PROXY> %s: %s", name, value)

    return original(self, *args, **kwargs)
