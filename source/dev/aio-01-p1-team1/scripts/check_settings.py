"""Read-only configuration checks; never print keys, URL credentials or response bodies."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit, quote

from housing_config import ConfigurationError, Settings, is_placeholder, read_secrets_files

ROOT = Path(__file__).resolve().parents[1]
TABLES = ("profiles", "admins", "listings", "favorites", "listing_images", "logs", "chat_summaries")


def app_settings(app: str) -> Settings:
    secrets = {}
    if app != "BE":
        secrets = read_secrets_files(
            Path.home() / ".streamlit/secrets.toml",
            ROOT / app / ".streamlit/secrets.toml",
        )
    return Settings(ROOT / app / ".env", secrets.get)


def inspect_settings(online: bool = False) -> list[dict]:
    results = []

    def record(check, status, detail, required=False):
        results.append(dict(check=check, status=status, detail=detail, required=required))

    configs = {}
    for app in ("BE", "FE_Admin", "FE_User"):
        try:
            configs[app] = app_settings(app)
            configs[app].file_values()
        except ConfigurationError:
            record(app, "FAIL", "설정 파일 형식을 확인하세요.", True)
    if len(configs) != 3:
        return results
    be, admin, user = (configs[name] for name in ("BE", "FE_Admin", "FE_User"))
    valid = {}
    fields = (
        ("BE", "SUPABASE_URL", True, ""),
        ("BE", "SUPABASE_SERVICE_ROLE_KEY", True, ""),
        ("BE", "ADMIN_TOKEN_SECRET", True, ""),
        ("FE_User", "SUPABASE_URL", True, ""),
        ("FE_User", "SUPABASE_ANON_KEY", True, ""),
        ("FE_Admin", "BACKEND_URL", True, "http://127.0.0.1:8000"),
        ("FE_User", "BACKEND_URL", True, "http://127.0.0.1:8000"),
        ("BE", "KAKAO_REST_API_KEY", False, ""),
        ("FE_Admin", "GEMINI_API_KEY", False, ""),
        ("BE", "GEMINI_API_KEY", False, ""),
        ("BE", "REDIS_URL", False, ""),
    )
    for app, field, required, default in fields:
        s = configs[app]
        value, source = s.resolve(field, default)
        okay = bool(value) and not is_placeholder(value)
        if okay and field == "ADMIN_TOKEN_SECRET":
            okay = len(value.encode("utf-8")) >= 32
        if okay and field in {"SUPABASE_URL", "BACKEND_URL"}:
            try:
                s.http_url(field, default)
            except ConfigurationError:
                okay = False
        if okay and field == "REDIS_URL":
            try:
                parsed = urlsplit(value)
                _ = parsed.port
                okay = parsed.scheme in {"redis", "rediss"} and bool(parsed.hostname)
            except ValueError:
                okay = False
        valid[app, field] = okay
        record(f"{app}/{field}", "PASS" if okay else ("FAIL" if required else "WARN"),
               f"설정 읽기 성공 ({source}); 연결 확인은 별도입니다." if okay else "없거나 예시/형식 오류입니다.", required)

    if valid["BE", "SUPABASE_URL"] and valid["FE_User", "SUPABASE_URL"]:
        match = be.http_url("SUPABASE_URL") == user.http_url("SUPABASE_URL")
        record("Supabase project", "PASS" if match else "FAIL", "서버와 사용자 화면의 프로젝트 일치" if match else "서버와 사용자 화면의 SUPABASE_URL이 다릅니다.", True)

    mode = be.get("CHAT_GEMINI_MODE", "mock").lower()
    if mode not in {"mock", "gemini"}:
        record("Chat mode", "WARN", "CHAT_GEMINI_MODE는 mock 또는 gemini여야 합니다.")
    elif mode == "mock":
        record("Chat mode", "INFO", "mock: 실제 AI가 아닌 연습용 응답입니다. 현재 Redis는 별도로 필요합니다.")
    elif not valid["BE", "GEMINI_API_KEY"]:
        record("Chat mode", "WARN", "실제 AI 모드이지만 BE/GEMINI_API_KEY가 없습니다.")
    else:
        record("Chat mode", "PASS", "실제 Gemini 모드 설정. 생성 응답은 별도 확인이 필요합니다.")
    if be.get("CHAT_SUMMARY_STORAGE", "preview").lower() not in {"preview", "supabase"}:
        record("Chat summary", "WARN", "CHAT_SUMMARY_STORAGE는 preview 또는 supabase여야 합니다.")
    for name, default in (("CHAT_HISTORY_LIMIT", "10"), ("CHAT_HISTORY_TTL_SECONDS", "3600"), ("CHAT_HISTORY_MAX_MESSAGES", "30")):
        try:
            int(be.get(name, default))
        except ValueError:
            record(f"BE/{name}", "WARN", "정수를 입력하세요.")

    if not online:
        return results
    import httpx

    with httpx.Client(timeout=15, follow_redirects=False) as client:
        def probe(label, url, headers, required=False, **kwargs):
            try:
                response = client.get(url, headers=headers, **kwargs)
            except httpx.HTTPError:
                record(label, "FAIL" if required else "WARN", "접속 실패: 네트워크/서비스 상태를 확인하세요.", required)
                return None
            status = response.status_code
            record(label, "PASS" if status == 200 else ("FAIL" if required else "WARN"), f"HTTP {status}", required)
            return response

        if valid["BE", "SUPABASE_URL"] and valid["BE", "SUPABASE_SERVICE_ROLE_KEY"]:
            base = be.http_url("SUPABASE_URL")
            key = be.get("SUPABASE_SERVICE_ROLE_KEY")
            headers = {"apikey": key, "Authorization": f"Bearer {key}"}
            for table in TABLES:
                probe(f"Supabase table/{table}", f"{base}/rest/v1/{table}", headers, True, params={"select": "id", "limit": "0"})
            response = probe("Supabase storage/listing-images", f"{base}/storage/v1/bucket/listing-images", headers, True)
            if response is not None and response.status_code == 200:
                bucket = response.json()
                expected = bucket.get("public") is True and bucket.get("file_size_limit") == 5242880 and set(bucket.get("allowed_mime_types") or []) == {"image/jpeg", "image/png", "image/webp"}
                record("Image bucket policy", "PASS" if expected else "WARN", "공개 공고 이미지 / 5MB / JPEG·PNG·WebP" if expected else "저장소의 공개 여부/파일 제한을 확인하세요.")
        if valid["FE_User", "SUPABASE_URL"] and valid["FE_User", "SUPABASE_ANON_KEY"]:
            probe("Supabase Auth", user.http_url("SUPABASE_URL") + "/auth/v1/settings", {"apikey": user.get("SUPABASE_ANON_KEY")}, True)
        if valid["BE", "KAKAO_REST_API_KEY"]:
            response = probe("Kakao Local", "https://dapi.kakao.com/v2/local/search/address.json", {"Authorization": "KakaoAK " + be.get("KAKAO_REST_API_KEY")}, params={"query": "서울 중구 세종대로 110"})
            if response is not None and response.status_code == 403:
                record("Kakao activation", "WARN", "카카오 개발자 콘솔에서 카카오맵 사용 설정을 확인하세요.")
        for name, s, default in (("FE_Admin", admin, "gemini-2.5-flash"), ("BE", be, "gemini-2.5-flash-lite")):
            if valid[name, "GEMINI_API_KEY"]:
                model = s.get("GEMINI_MODEL", default).removeprefix("models/")
                probe(name + "/Gemini model access", "https://generativelanguage.googleapis.com/v1beta/models/" + quote(model, safe=""), {"x-goog-api-key": s.get("GEMINI_API_KEY")})
        if valid["BE", "REDIS_URL"]:
            import redis
            try:
                with redis.Redis.from_url(be.get("REDIS_URL"), socket_connect_timeout=5, socket_timeout=5) as connection:
                    connection.ping()
                record("Redis PING", "PASS", "연결 성공 (데이터 저장 안 함).")
            except (redis.RedisError, ValueError):
                record("Redis PING", "WARN", "접속 실패: 주소/비밀번호/서버 상태를 확인하세요.")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true", help="외부 서비스 읽기 연결 확인. AI 생성/데이터 쓰기는 하지 않습니다.")
    parser.add_argument("--json", type=Path, help="값이 제외된 결과 JSON 저장 경로")
    args = parser.parse_args()
    results = inspect_settings(args.online)
    for item in results:
        print(f"[{item['status']}] {item['check']}: {item['detail']}")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return int(any(item["required"] and item["status"] == "FAIL" for item in results))


if __name__ == "__main__":
    raise SystemExit(main())
