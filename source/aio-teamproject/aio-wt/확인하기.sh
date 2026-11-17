#!/usr/bin/env bash
# 야간 작업 결과를 1번부터 순서대로 확인하는 스크립트입니다.
# 사용법:  bash /c/dev/aio-wt/확인하기.sh 1     <- 1번 항목 실행
#          bash /c/dev/aio-wt/확인하기.sh stop  <- 확인용 서버 모두 종료
#
# 기존 8000(BE) / 8501(관리자) / 8502(사용자) 서버는 건드리지 않습니다.

set -u
REPO=/c/dev/aio-01-p1-team1
WT=/c/dev/aio-wt
ADMIN_PY="$REPO/FE_Admin/.venv/Scripts/python.exe"
USER_PY="$REPO/FE_User/.venv/Scripts/python.exe"

case "${1:-}" in
  1) DIR=$WT/01-form-retain/FE_Admin;   PY=$ADMIN_PY; PORT=8531; WHAT="관리자 · 청약정보 등록(수동) 화면" ;;
  2) DIR=$WT/02-area-pyeong/FE_User;    PY=$USER_PY;  PORT=8532; WHAT="사용자 · 청약정보 조회 (관리자 목록도 적용됨)" ;;
  3) DIR=$WT/03-dday-sort/FE_User;      PY=$USER_PY;  PORT=8533; WHAT="사용자 · 청약정보 조회 (BE 재시작 필요, 아래 설명 참고)" ;;
  4) DIR=$WT/04-amount-format/FE_Admin; PY=$ADMIN_PY; PORT=8534; WHAT="관리자 · 청약정보 등록 화면" ;;
  5) DIR=$WT/05-readability/FE_User;    PY=$USER_PY;  PORT=8535; WHAT="사용자 · 청약정보 조회" ;;
  6) DIR=$WT/06-gemini-auto/FE_Admin;   PY=$ADMIN_PY; PORT=8536; WHAT="관리자 · 사이드바와 청약정보 등록(자동)" ;;
  7) DIR=$WT/07-sort-options/FE_User;   PY=$USER_PY;  PORT=8537; WHAT="사용자 · 청약정보 조회 정렬" ;;
  stop)
    for p in 8531 8532 8533 8534 8535 8536 8537; do
      pid=$(netstat -ano 2>/dev/null | grep ":$p " | grep LISTENING | awk '{print $5}' | head -1)
      if [ -n "${pid:-}" ]; then powershell -NoProfile -Command "Stop-Process -Id $pid -Force" 2>/dev/null && echo "종료: 포트 $p"; fi
    done
    echo "확인용 서버를 모두 종료했습니다. 기존 8000/8501/8502는 그대로입니다."
    exit 0 ;;
  *)
    echo "사용법: bash $0 <1~7 | stop>"
    exit 1 ;;
esac

echo "[$1번] $WHAT"
echo "주소: http://localhost:$PORT"
echo "폴더: $DIR"
echo "종료하려면 Ctrl+C 또는  bash $0 stop"
echo
cd "$DIR" && PYTHONIOENCODING=utf-8 "$PY" -m streamlit run app.py --server.port "$PORT"
