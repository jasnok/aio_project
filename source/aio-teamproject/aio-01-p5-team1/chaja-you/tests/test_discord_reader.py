import contextlib
import io
import json
import sys
import unittest
from unittest.mock import patch

from tools import discord_reader as reader


def msg(n, content="내용"):
    return {"id": str(n), "timestamp": "2026-11-13T00:00:00+00:00", "content": content}


class DiscordReaderTests(unittest.TestCase):
    def test_empty_channel_is_complete(self):
        with patch.object(reader, "get", return_value=[]):
            self.assertEqual(reader.search_channel({"id": "1", "name": "empty"}, "", None, None, None, None), ([], 0, False))

    def test_all_messages_across_pages_without_keyword(self):
        pages = [[msg(n) for n in range(201, 101, -1)], [msg(n) for n in range(101, 51, -1)]]
        with patch.object(reader, "get", side_effect=pages) as get:
            result, scanned, limited = reader.search_channel({"id": "1", "name": "general"}, "", None, None, None, None)
        self.assertEqual((len(result), scanned, limited), (150, 150, False))
        self.assertEqual(get.call_args_list[1].kwargs["before"], "102")

    def test_keyword_and_result_limit(self):
        with patch.object(reader, "get", return_value=[msg(3, "기획 회의"), msg(2, "다른 내용"), msg(1, "기획 정리")]):
            result, scanned, limited = reader.search_channel({"id": "1", "name": "general"}, "기획", None, None, None, 1)
        self.assertEqual((len(result), scanned, limited), (1, 1, True))

    def test_date_boundaries(self):
        before = reader.parse_date("2026-11-13T09:00:00+09:00", end=True)
        with patch.object(reader, "get", return_value=[msg(2), {**msg(1), "timestamp": "2026-11-12T23:59:59+00:00"}]):
            result, _, _ = reader.search_channel({"id": "1", "name": "general"}, "", None, before, None, None)
        self.assertEqual([m["id"] for m in result], ["1"])
        self.assertEqual(reader.parse_date("2026-11-13", end=True) - reader.parse_date("2026-11-13"), reader.parse_date("2026-11-14") - reader.parse_date("2026-11-13"))

    def test_all_channels_continue_after_forbidden(self):
        channels = [{"id": "1", "name": "금지", "type": 0}, {"id": "2", "name": "일반", "type": 0}]
        def fetch(path, **kwargs):
            if path.endswith("/1/messages"):
                raise SystemExit("Discord API HTTP 403: 권한이 없습니다")
            return [msg(1)]
        output = io.StringIO()
        with patch.object(sys, "argv", ["reader", "--guild", "server", "--json"]), patch.object(reader, "resolve_guild", return_value={"id": "g", "name": "server"}), patch.object(reader, "channel_list", return_value=channels), patch.object(reader, "searchable_channels", side_effect=lambda g, c, e: c), patch.object(reader, "get", side_effect=fetch), contextlib.redirect_stdout(output):
            reader.main()
        data = json.loads(output.getvalue())
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(len(data["errors"]), 1)
        self.assertFalse(data["truncated"])

    def test_unfiltered_server_reads_each_channel(self):
        channels = [{"id": "1", "name": "첫째", "type": 0}, {"id": "2", "name": "둘째", "type": 0}]
        output = io.StringIO()
        with patch.object(sys, "argv", ["reader", "--guild", "server", "--json"]), patch.object(reader, "resolve_guild", return_value={"id": "g", "name": "server"}), patch.object(reader, "channel_list", return_value=channels), patch.object(reader, "searchable_channels", side_effect=lambda g, c, e: c), patch.object(reader, "get", side_effect=lambda path, **kwargs: [msg(1)]), contextlib.redirect_stdout(output):
            reader.main()
        data = json.loads(output.getvalue())
        self.assertEqual({m["channel"] for m in data["results"]}, {"첫째", "둘째"})
        self.assertFalse(data["truncated"])


if __name__ == "__main__":
    unittest.main()
