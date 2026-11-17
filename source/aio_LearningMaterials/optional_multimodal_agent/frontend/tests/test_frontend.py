from frontend.core.sse_client import parse_events


def test_parse_events_reads_id_event_and_json_data():
    lines = [
        "id: 10-0",
        "event: progress",
        'data: {"status":"running"}',
        "",
    ]
    assert list(parse_events(lines)) == [
        {"id": "10-0", "event": "progress", "data": {"status": "running"}}
    ]


def test_parse_events_can_expose_heartbeat():
    assert list(parse_events([": keep-alive"], include_heartbeat=True)) == [
        {"event": "heartbeat", "data": {}}
    ]
