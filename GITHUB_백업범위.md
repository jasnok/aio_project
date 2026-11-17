# GitHub 백업 범위

기준: 2026-11-17. 맥의 `/Users/rola/aio_project`를 기준으로 [공개 GitHub 저장소](https://github.com/jasnok/aio_project)의 `main`에 팀 프로젝트와 학습 자료를 보관합니다. 저장소의 `source`는 `aio-teamproject`와 `aio_LearningMaterials`로 구성됩니다.

## 포함 범위와 제외 사항

2026-11-17 소스 동기화는 로컬 작업본을 별도 임시 폴더에 복사한 뒤 수행했습니다. 그때 중첩 `.git`, 실제 `.env` 및 일부 로컬 환경설정, `.venv`, `node_modules`, 캐시, `.runtime`, 인증서·키, SQLite/DB 파일, `.DS_Store`, 실행 로그를 제외했습니다. 프로젝트별 Git 무시 규칙도 적용되므로 GitHub는 로컬 폴더와 완전히 동일하지 않습니다.

여러 `.env.example`은 포함되어 있습니다. 단, `source/aio_LearningMaterials/aidevs/02_supabase-ai-backend/.env.example`은 자격증명으로 쓰일 수 있는 값의 성격이 확인되지 않아 GitHub 업로드에서 제외했습니다. 실제 비밀값은 문서에 옮기지 말고 별도로 안전하게 관리하세요.

진행 중인 5차 프로젝트 `chaja-you`는 `/Users/rola/chaja-you`의 별도 작업본과 [팀 GitHub 저장소](https://github.com/ik-e/chaja-you)에서 관리합니다. 포트폴리오의 현재 트리에는 안내 링크만 두며, 이전에 보관한 소스 스냅샷은 포트폴리오의 과거 커밋 이력에 남아 있습니다. 이 GitHub 저장소 자체의 이력은 존재하지만 각 원본 프로젝트의 전체 브랜치·미커밋 상태·Git 설정을 대체하지 않습니다.

과거 Windows 백업에서 만든 Git bundle과 패치는 과거 이력의 민감정보 가능성 때문에 GitHub에 올리지 않았습니다. 이 맥의 현재 `/Users/rola/aio_project`에는 `git-history` 폴더가 없으므로 이전 bundle의 현재 보관 위치와 복구 가능성은 별도 확인이 필요합니다. [Git 및 플랫폼 점검](Git_플랫폼_점검.md)은 당시 기록입니다.

2026-11-17에 `aio-wt`와 `lawpath-campus-submission`을 현재 트리에서 정리하고 `/Users/rola/aio_project_backup/정리보관_2026-11-17`에 옮겨 보관했습니다. 이 로컬 보관 폴더는 현재 GitHub 트리에 포함되지 않지만, 정리 전 스냅샷은 GitHub 과거 커밋에서 확인할 수 있습니다. 날씨 MCP 배포 프로젝트는 `source/aio_LearningMaterials/05_weather-mcp-deployment-project`로 이동했습니다.

## 운영 시 주의

2026-11-17에 로컬 루트 브랜치와 인덱스를 GitHub에 맞추면서 작업 중인 파일과 중첩 Git 저장소는 보존했습니다. 로컬 전용 파일이나 중첩 프로젝트의 변경은 Git 상태에 표시될 수 있습니다. 루트 `.gitignore`만으로 모든 비밀값과 중첩 Git 저장소가 제외되는 것은 아니므로, 파일을 일괄 추가하기 전에 업로드 범위를 확인하세요.

텍스트 패턴 검사는 모든 종류의 비밀값이나 개인정보, 바이너리 내용을 보장하지 않습니다. 외부 공유 전에는 접근 권한과 자료를 별도로 검토하세요.
