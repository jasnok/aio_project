# 두 계약을 합친 스키마 변경 비교

현재 `schemas.py`와 두나·해든 계약을 합쳤을 때 달라지는 부분을 비교한 문서입니다. 아래 통합안은 변경 내용을 검토하기 위한 제안이며, 실제 파일은 수정하지 않았습니다.

## 1. `CareStatusResult`

| 현재 스키마 | 통합 제안 | 반영 이유 |
|---|---|---|
| `area` 없음 | `area: str | None = None` 추가 | 병원 검색에 사용. 프로필의 집 주소에서 채우며, 없으면 기본 Mock 병원 목록 사용 |
| `fall_event` 없음 | 선택 필드 추가 | 워치 낙상, 음성 응답, 움직임 없음 시간, 머리 충격 의심 전달 |
| `signs` 없음 | 선택 필드 추가 | 이상 행동·호흡 곤란 정황 전달 |
| `cctv`에 `image_path`, `summary`, `status` | `confidence` 추가 | 낙상 판정에 CCTV 분석 확신도 사용 |

```python
class FallEvent(BaseModel):
    watch_fall: bool | None = None
    voice_response: Literal["ok", "help", "none"] | None = None
    immobile_seconds: int | None = None
    head_impact_suspected: bool | None = None


class Signs(BaseModel):
    abnormal_behavior: bool | None = None
    breathing_distress: bool | None = None


class CctvAnalysis(BaseModel):
    image_path: str | None = None
    summary: str | None = None
    status: Literal["analyzed", "unavailable", "failed"] = "unavailable"
    confidence: float | None = None


class CareStatusResult(BaseModel):
    run_id: str
    profile_id: str
    scenario: Scenario
    attempt: int = 1

    vital: VitalData | None = None
    indoor_environment: IndoorEnvironment | None = None
    devices: DeviceStatus | None = None
    cctv: CctvAnalysis | None = None

    vulnerability: Literal["상", "중", "하"] | None = None
    area: str | None = None
    fall_event: FallEvent | None = None
    signs: Signs | None = None

    source: DataSource = "mock"
    errors: list[str] = Field(default_factory=list)
```

`area`는 프로필의 집 주소에서 오케스트레이터가 채우는 값입니다. 값이 없으면 병원 조회 도구가 `None`을 받아 기본 Mock 목록을 반환합니다.

## 2. `EmergencyResult`

현재 스키마는 위험도·근거·조치 목록을 담습니다. 해든님의 위험 규칙 반환값을 위해 다음 필드가 추가될 수 있습니다.

| 필드 | 의미 |
|---|---|
| `axes` | 낙상·심뇌·호흡·환경별 판정 결과 |
| `fall_state` | 낙상 관련 상태 판정 |
| `auto_119` | 보호자 승인 전 119 연결 대상 여부와 사유 |

```python
class EmergencyResult(BaseModel):
    run_id: str
    risk_level: Literal["정상", "주의", "경고", "위급"]
    reasons: list[str] = Field(default_factory=list)
    axes: dict[str, str] = Field(default_factory=dict)
    fall_state: str | None = None
    auto_119: str | None = None
    proposed_actions: list[ProposedAction] = Field(default_factory=list)
    requires_approval: bool = True
    cctv_summary: str | None = None
```

`axes`, `fall_state`, `auto_119`의 정확한 타입과 허용값은 해든님의 `evaluate()` 반환 형식에 맞춰야 합니다. 위 코드는 필드 구성을 보여주는 비교 예시입니다.

## 3. `CareRunResponse`와 `CareApprovalResponse`

통합 계약에서는 응답 상태를 다음 다섯 값으로 맞춥니다.

```python
CareStatus = Literal[
    "no_issue",
    "pending_approval",
    "done",
    "rejected",
    "fail",
]

DecidedBy = Literal["guardian", "auto", "timeout"]
```

응답에 다음 필드를 추가합니다.

```python
approved: bool | None = None
decided_by: DecidedBy | None = None
```

| 상황 | `status` | `approved` | `decided_by` |
|---|---|---:|---|
| 정상 종료 | `no_issue` | `null` | `null` |
| 보호자 승인 대기 | `pending_approval` | `null` | `null` |
| 보호자 승인 후 완료 | `done` | `true` | `guardian` |
| 보호자 거절 | `rejected` | `false` | `guardian` |
| 승인 없이 바로 119 Mock 연결 | `done` | `null` | `auto` |
| 60초 무응답 후 119 Mock 연결 | `done` | `null` | `timeout` |
| 119 Mock 연결 실패 | `fail` | `null` | `auto` 또는 `timeout` |

시간 초과 시 승인 대기 항목이 기기 제어뿐이면 `pending_approval`을 유지하고 재알림합니다. 보호자 버튼 요청은 두나 계약의 `decision: "approve" | "reject"`를 유지할 수 있습니다.

## 4. 두나 계약에서 유지되는 항목

- `profile_id`, `run_id`, `scenario`, `fault`
- `DeviceStatus.induction_minutes` (분 단위)
- `ProposedAction.arguments` 키와 MCP 함수 인자 이름 일치
- CCTV 분석 상태: `analyzed | unavailable | failed`
- `/care/approve`는 처리 완료 후 동기 응답 반환

## 5. 통합 확정 전에 남는 결정

1. Profile Agent 취약도 표기를 `상/중/하`로 통일
2. `axes`, `fall_state`, `auto_119`의 실제 자료형과 허용값 확인
3. 거절 결과를 `approved=false`, `decided_by=guardian`로 표현할지 확정
4. 119 실패 시 `decided_by` 처리 기준 확정
5. 타임아웃 처리를 내부 승인 서비스 호출로 할지 별도 HTTP 요청으로 할지 결정
6. README의 기존 “119는 승인 후” 원칙에 자동 연결 예외를 둘지 PM·팀과 합의

## 요약

두 계약을 합치면 `CareStatusResult`에 병원 검색·낙상 맥락 필드가 추가되고, `EmergencyResult`에 위험 축·낙상 상태·자동 119 정보가 추가됩니다. 최종 API 응답에는 `approved`와 `decided_by`가 포함되어 보호자 승인, 자동 처리, 타임아웃 처리를 구분하게 됩니다.
