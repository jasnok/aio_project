"""관리자 계정을 admins 테이블에 등록하는 스크립트입니다.

관리자 계정은 회원가입 API가 없고 중앙에서 부여하므로, 이 스크립트로 직접 생성합니다.

사용법:
    python scripts/create_admin.py admin01
"""

import sys
from getpass import getpass
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.password import hash_password
from app.core.supabase_config import get_supabase


def create_admin(username: str, password: str) -> None:
    supabase = get_supabase()
    result = (
        supabase.table("admins")
        .insert(
            {
                "username": username,
                "password": hash_password(password),
            }
        )
        .execute()
    )
    if not result.data:
        print("관리자 계정 생성에 실패했습니다.")
        return
    print(f"관리자 계정이 생성되었습니다: {username}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용법: python scripts/create_admin.py <username> (비밀번호는 다음 화면에서 입력)")
        sys.exit(1)

    password = getpass("비밀번호 (입력 내용은 표시되지 않습니다): ")
    confirmation = getpass("비밀번호 다시 입력: ")
    if not password or password != confirmation:
        print("비밀번호가 비어 있거나 서로 다릅니다. 계정을 만들지 않았습니다.")
        sys.exit(1)
    create_admin(sys.argv[1], password)
