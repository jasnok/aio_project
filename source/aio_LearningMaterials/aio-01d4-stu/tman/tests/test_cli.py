from unittest.mock import patch

import pytest

from tman.cli import main
from tman.network import NetworkError, PageNotFound, RequestTimeout


def test_success(capsys):
    with patch("sys.argv", ["tman", "tar"]), patch(
        "tman.cli.fetch_page", return_value="# tar\n> 설명\n\n- 예시:\n`tar  {{file}}`"
    ):
        assert main() == 0
    captured = capsys.readouterr()
    assert captured.out == "tar\n\n설명\n\n- 예시:\n  tar  {{file}}\n"
    assert captured.err == ""


@pytest.mark.parametrize("error, code, label", [
    (PageNotFound("missing"), 1, "Page not found:"),
    (NetworkError("offline"), 2, "Network error:"),
    (RequestTimeout("slow"), 3, "Timeout:"),
])
def test_errors(capsys, error, code, label):
    with patch("sys.argv", ["tman", "tar"]), patch("tman.cli.fetch_page", side_effect=error):
        assert main() == code
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith(label)
