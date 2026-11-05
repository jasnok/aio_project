from io import BytesIO
from unittest.mock import call, patch
from urllib.error import HTTPError, URLError

import pytest

from tman.network import BASE_URL, NetworkError, PageNotFound, RequestTimeout, fetch_page


def missing():
    return HTTPError("https://example.com", 404, "Not Found", {}, None)


def test_common_success():
    with patch("tman.network.urlopen", return_value=BytesIO("# tar\n> 설명".encode())) as get:
        assert fetch_page("tar") == "# tar\n> 설명"
    get.assert_called_once_with(f"{BASE_URL}/common/tar.md", timeout=10.0)


def test_linux_fallback():
    with patch("tman.network.urlopen", side_effect=[missing(), BytesIO(b"# tar")]) as get:
        assert fetch_page("tar") == "# tar"
    assert get.call_args_list == [
        call(f"{BASE_URL}/common/tar.md", timeout=10.0),
        call(f"{BASE_URL}/linux/tar.md", timeout=10.0),
    ]


def test_both_pages_missing():
    with patch("tman.network.urlopen", side_effect=[missing(), missing()]) as get:
        with pytest.raises(PageNotFound):
            fetch_page("unknown")
    assert get.call_count == 2


@pytest.mark.parametrize("error, expected", [
    (TimeoutError(), RequestTimeout),
    (URLError(TimeoutError()), RequestTimeout),
    (URLError("DNS failed"), NetworkError),
    (HTTPError("https://example.com", 500, "Server error", {}, None), NetworkError),
    (OSError("Connection interrupted"), NetworkError),
])
def test_failures_do_not_fall_back(error, expected):
    with patch("tman.network.urlopen", side_effect=error) as get:
        with pytest.raises(expected):
            fetch_page("tar")
    assert get.call_count == 1


@pytest.mark.parametrize("command", ["../tar", "", "tar/foo", "tar?x=1"])
def test_invalid_names_do_not_make_requests(command):
    with patch("tman.network.urlopen") as get:
        with pytest.raises(ValueError):
            fetch_page(command)
    get.assert_not_called()
