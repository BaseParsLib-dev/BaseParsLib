from unittest.mock import MagicMock, patch

from requests.auth import HTTPProxyAuth

from base_pars_lib.core._requests_digest_proxy import HTTPProxyDigestAuth
from base_pars_lib.utils import rotating_proxy_auth


@patch("requests.session")
def test_rotating_proxy_auth(mock_session: MagicMock) -> None:
    # Настройка
    mock_session_instance = MagicMock()
    mock_session.return_value = mock_session_instance

    http_url = "http://example.com:8080"
    https_url = "https://example.com:8443"
    login = "user"
    password = "pass"

    session = rotating_proxy_auth(http_url, https_url, login, password)

    # Проверка, что сессия была создана
    mock_session.assert_called_once()
    assert session == mock_session_instance

    # Проверка, что прокси настроены правильно
    assert session.proxies["http"] == http_url
    assert session.proxies["https"] == https_url

    # Проверка, что авторизация настроена правильно
    assert isinstance(session.auth, HTTPProxyAuth)
    assert session.auth.username == login
    assert session.auth.password == password

    # Проверка, что авторизация HTTPProxyDigestAuth не используется
    assert not isinstance(session.auth, HTTPProxyDigestAuth)


# pytest tests/utils/test_working_with_proxy.py
