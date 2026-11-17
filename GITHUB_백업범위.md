# GitHub 백업 범위

기준: 2026-11-17. 맥의 `/Users/rola/aio_project`를 기준으로 [비공개 GitHub 저장소](https://github.com/jasnok/aio_project_backup)의 `main`에 팀 프로젝트와 학습 자료를 보관합니다. 저장소의 `source`는 `aio-teamproject`와 `aio_LearningMaterials`로 구성됩니다.

## 포함 범위와 제외 사항

2026-11-17 소스 동기화는 로컬 작업본을 별도 임시 폴더에 복사한 뒤 수행했습니다. 그때 중첩 `.git`, 실제 `.env` 및 일부 로컬 환경설정, `.venv`, `node_modules`, 캐시, `.runtime`, 인증서·키, SQLite/DB 파일, `.DS_Store`, 실행 로그를 제외했습니다. 프로젝트별 Git 무시 규칙도 적용되므로 GitHub는 로컬 폴더와 완전히 동일하지 않습니다.

여러 `.env.example`은 포함되어 있습니다. 단, `source/aio_LearningMaterials/aidevs/02_supabase-ai-backend/.env.example`은 자격증명으로 쓰일 수 있는 값의 성격이 확인되지 않아 GitHub 업로드에서 제외했습니다. 실제 비밀값은 문서에 옮기지 말고 별도로 안전하게 관리하세요.

`source/aio-teamproject/aio-01-p5-team1/chaja-you`의 소스는 일반 파일로 포함되지만, 로컬에 있는 중첩 저장소의 `.git` 이력과 worktree 연결은 포함되지 않습니다. 이 GitHub 저장소 자체의 이력은 존재하지만 각 원본 프로젝트의 전체 브랜치·미커밋 상태·Git 설정을 대체하지 않습니다.

과거 Windows 백업에서 만든 Git bundle과 패치는 과거 이력의 민감정보 가능성 때문에 GitHub에 올리지 않았습니다. 이 맥의 현재 `/Users/rola/aio_project`에는 `git-history` 폴더가 없으므로 이전 bundle의 현재 보관 위치와 복구 가능성은 별도 확인이 필요합니다. [Git 및 플랫폼 점검](Git_플랫폼_점검.md)은 당시 기록입니다.

## 운영 시 주의

현재 로컬 루트의 Git 작업본은 대량의 미커밋 폴더 재구성이 있는 상태이며, GitHub 갱신은 별도 임시 작업본에서 이루어졌습니다. 로컬 작업을 보존한 채 상태와 차이를 확인한 후 동기화 방법을 정해야 합니다. 루트 `.gitignore`만으로 모든 비밀값과 중첩 Git 저장소가 제외되는 것은 아니므로, 파일을 일괄 추가하기 전에 업로드 범위를 확인하세요.

텍스트 패턴 검사는 모든 종류의 비밀값이나 개인정보, 바이너리 내용을 보장하지 않습니다. 외부 공유 전에는 접근 권한과 자료를 별도로 검토하세요.
