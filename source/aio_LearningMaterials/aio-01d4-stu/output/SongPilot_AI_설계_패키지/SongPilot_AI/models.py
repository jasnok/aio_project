"""SongPilot AI v1.0 데이터 계약 초안. 워크플로우/의미 검수 구현은 포함하지 않는다.

이 파일을 실행하면 같은 폴더에 package.schema.json을 생성하고 수작업 예시의
Pydantic 검증 및 JSON 직렬화 왕복을 확인한다. 외부 LLM 호출은 하지 않는다.
"""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


Text = Annotated[str, StringConstraints(min_length=1, pattern=r"\S")]
RunId = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{2,79}$")]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class RequiredMessage(Contract):
    id: Text
    text: Text


class CampaignRequest(Contract):
    purpose: Text
    audience: Text
    channel: Text
    target_duration_seconds: int = Field(default=30, ge=5, le=180)
    language: Text = "ko"
    tone: list[Text] = Field(min_length=1)
    required_messages: list[RequiredMessage] = Field(default_factory=list)
    required_phrases: list[Text] = Field(default_factory=list)
    forbidden_terms: list[Text] = Field(default_factory=list)
    expression_guidelines: list[Text] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_ids_and_exact_phrase_conflicts(self):
        if not self.required_messages and not self.required_phrases:
            raise ValueError("필수 메시지 또는 필수 문구를 최소 1개 입력해야 합니다")
        ids = [item.id for item in self.required_messages]
        if len(ids) != len(set(ids)):
            raise ValueError("required_messages.id는 중복될 수 없습니다")
        for phrase in self.required_phrases:
            if any(term in phrase for term in self.forbidden_terms):
                raise ValueError("필수 문구에 금지어가 포함되어 있습니다. 사용자 확인이 필요합니다")
        return self


class ContentPlan(Contract):
    target_summary: Text
    concept: Text
    sections: list[Text] = Field(min_length=1)
    message_ids: list[Text] = Field(default_factory=list)


class MusicStyle(Contract):
    prompt: Text
    bpm: int = Field(ge=40, le=220)
    target_duration_seconds: int = Field(ge=5, le=180)


class ReviewCheck(Contract):
    id: Text
    kind: Literal["deterministic", "semantic", "estimate", "human"]
    status: Literal["pass", "fail", "uncertain", "not_run"]
    evidence: str = ""
    message: Text


class ReviewReport(Contract):
    content_revision: int = Field(ge=1)
    checks: list[ReviewCheck] = Field(min_length=1)
    duration_verified: Literal[False] = False

    @model_validator(mode="after")
    def unique_check_ids(self):
        ids = [check.id for check in self.checks]
        if len(ids) != len(set(ids)):
            raise ValueError("review.checks.id는 중복될 수 없습니다")
        return self


class Approval(Contract):
    status: Literal["pending", "approved", "rejected"] = "pending"
    reviewer: Text | None = None
    decided_at: datetime | None = None
    approved_revision: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def decision_metadata(self):
        if self.status == "pending":
            if any(value is not None for value in
                   (self.reviewer, self.decided_at, self.approved_revision)):
                raise ValueError("승인 대기 상태에는 승인 메타데이터를 기록하지 않습니다")
        elif not self.reviewer or not self.decided_at:
            raise ValueError("승인/반려에는 담당자와 판단 시각이 필요합니다")
        if self.decided_at and self.decided_at.utcoffset() is None:
            raise ValueError("판단 시각에는 시간대가 필요합니다")
        if self.status == "approved" and self.approved_revision is None:
            raise ValueError("승인에는 승인한 revision이 필요합니다")
        if self.status == "rejected" and self.approved_revision is not None:
            raise ValueError("반려 상태에는 approved_revision을 기록하지 않습니다")
        return self


class HistoryEvent(Contract):
    node: Literal["intake", "plan", "copy", "style", "review", "repair", "approval", "export"]
    status: Literal["started", "succeeded", "failed", "waiting", "skipped"]
    revision: int = Field(ge=1)
    reason: Text
    recorded_at: datetime


class RunError(Contract):
    code: Text
    node: Text
    message: Text
    retryable: bool
    attempt: int = Field(ge=1)


class ProductionPackage(Contract):
    schema_version: Literal["1.0"] = "1.0"
    project: Literal["SongPilot AI"] = "SongPilot AI"
    run_id: RunId
    revision: int = Field(default=1, ge=1)
    status: Literal["draft", "running", "needs_input", "awaiting_approval", "approved", "failed"]
    execution_mode: Literal["design_example", "mock", "llm"]
    request: CampaignRequest
    plan: ContentPlan | None = None
    lyrics: Text | None = None
    style: MusicStyle | None = None
    review: ReviewReport | None = None
    approval: Approval = Field(default_factory=Approval)
    history: list[HistoryEvent] = Field(default_factory=list)
    errors: list[RunError] = Field(default_factory=list)
    max_revision_attempts: Literal[2] = 2
    revision_attempts: int = Field(default=0, ge=0, le=2)

    @model_validator(mode="after")
    def revision_and_approval_consistency(self):
        if self.style and self.style.target_duration_seconds != self.request.target_duration_seconds:
            raise ValueError("Style Prompt의 목표 길이는 요청과 일치해야 합니다")
        if self.plan:
            requested_ids = {message.id for message in self.request.required_messages}
            if set(self.plan.message_ids) != requested_ids:
                raise ValueError("기획에는 모든 필수 메시지 id를 전달해야 합니다")
        if self.review and self.review.content_revision != self.revision:
            raise ValueError("검수 결과는 현재 revision에 해당해야 합니다")
        expected_kinds = {
            "schema_format": {"deterministic"},
            "required_phrases": {"deterministic"},
            "forbidden_terms": {"deterministic"},
            "expression_guidelines": {"semantic", "human"},
        }
        expected_kinds.update({
            f"message:{item.id}": {"semantic", "human"}
            for item in self.request.required_messages
        })
        if self.review:
            for check in self.review.checks:
                if check.id in expected_kinds and check.kind not in expected_kinds[check.id]:
                    raise ValueError(f"검수 항목 {check.id}의 kind가 올바르지 않습니다")
                if check.id.startswith("message:") and check.status == "pass":
                    if not self.lyrics or not check.evidence.strip() or check.evidence not in self.lyrics:
                        raise ValueError("통과한 메시지 검수의 evidence는 실제 가사의 연속된 구절이어야 합니다")
        if any(event.revision > self.revision for event in self.history):
            raise ValueError("이력의 revision은 현재 revision을 초과할 수 없습니다")
        approved = self.approval.status == "approved"
        if approved != (self.status == "approved"):
            raise ValueError("패키지와 승인 상태가 일치해야 합니다")
        if self.execution_mode == "design_example" and approved:
            raise ValueError("설계용 예시는 실제 승인본으로 표시할 수 없습니다")
        if approved and self.approval.approved_revision != self.revision:
            raise ValueError("승인은 현재 revision에만 유효합니다. 수정 후 재검수/재승인이 필요합니다")
        if self.status in {"awaiting_approval", "approved"}:
            if not self.plan or not self.lyrics or not self.style or not self.review:
                raise ValueError("승인 단계에는 기획, 가사, 스타일, 검수 결과가 필요합니다")
            expected = set(expected_kinds)
            checks = {item.id: item for item in self.review.checks}
            if not expected.issubset(checks):
                raise ValueError("필수 검수 항목이 누락되었습니다")
            if any(checks[item].status != "pass" for item in expected):
                raise ValueError("모든 필수 검수 항목은 pass여야 합니다")
            blocking = [item for item in self.review.checks if item.kind != "estimate"]
            if any(item.status != "pass" for item in blocking):
                raise ValueError("실패/불확실/미실행 검수 항목을 해결한 후 승인 단계로 이동합니다")
            if any(not checks[item].evidence.strip() for item in expected):
                raise ValueError("필수 검수 항목에는 근거가 필요합니다")
        return self


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    schema = ProductionPackage.model_json_schema()
    (root / "package.schema.json").write_text(
        json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    sample = ProductionPackage.model_validate_json(
        (root / "example_package.json").read_text(encoding="utf-8")
    )
    restored = ProductionPackage.model_validate_json(sample.model_dump_json())
    assert restored == sample
    print("PASS: JSON Schema 생성, 수작업 설계 예시 구조 검증, JSON 왕복 검증")
    print("미실행: LLM, 의미 검수, 재시도 워크플로우, 승인 UI, 실제 음원 길이 검증")
