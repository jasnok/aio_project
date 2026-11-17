from tman.parser import Example, parse_page


MARKDOWN = """# tar

> 압축 파일을 만듭니다.
> 더 많은 정보: <https://example.com>.

- 파일을 압축합니다:

`tar  -cf {{archive.tar}}  {{path/to/file}}`

- 파일을 풉니다:

`  tar -xf {{archive.tar}}  `
"""


def test_parse_fixed_korean_markdown():
    page = parse_page(MARKDOWN)
    assert page.title == "tar"
    assert page.description == "압축 파일을 만듭니다.\n더 많은 정보: <https://example.com>."
    assert page.examples == (
        Example("파일을 압축합니다:", "tar  -cf {{archive.tar}}  {{path/to/file}}"),
        Example("파일을 풉니다:", "  tar -xf {{archive.tar}}  "),
    )


def test_empty_page():
    page = parse_page("")
    assert (page.title, page.description, page.examples) == ("", "", ())


def test_crlf_and_unrelated_lines():
    page = parse_page("# test\r\n\r\n- Example:\r\n\r\n`echo {{value}}`\r\nignored\r\n")
    assert page.examples == (Example("Example:", "echo {{value}}"),)
