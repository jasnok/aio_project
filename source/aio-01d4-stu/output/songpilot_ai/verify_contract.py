"""데이터 계약 경계의 회귀 검사. LLM/실제 업무/워크플로우 테스트가 아니다."""

from copy import deepcopy
import json
from pathlib import Path

from pydantic import ValidationError

from models import ProductionPackage


ROOT = Path(__file__).resolve().parent
sample = json.loads((ROOT / "example_package.json").read_text(encoding="utf-8"))


def load(data):
    return ProductionPackage.model_validate_json(json.dumps(data, ensure_ascii=False))


def rejects(name, data):
    try:
        load(data)
    except ValidationError:
        print(f"PASS reject: {name}")
        return
    raise AssertionError(f"Unexpected acceptance: {name}")


def change(data, mutate):
    changed = deepcopy(data)
    mutate(changed)
    return changed


# 승인 게이트를 검증하기 위한 메모리 내부의 합성 fixture다.
# 실제 LLM 실행이나 담당자 검수/승인을 의미하지 않으며 산출물로 저장하지 않는다.
ready = deepcopy(sample)
ready["execution_mode"] = "llm"
ready["status"] = "awaiting_approval"
spans = {
    "message:msg-01": "물을 마셔요",
    "message:msg-02": "그늘에서 잠시 쉬어요",
    "message:msg-03": "한낮에는 바깥 활동 줄여요",
}
for check in ready["review"]["checks"]:
    if check["kind"] != "estimate":
        check["status"] = "pass"
        check["evidence"] = spans.get(check["id"], "synthetic test evidence")

approved = deepcopy(ready)
approved["status"] = "approved"
approved["approval"] = {
    "status": "approved",
    "reviewer": "synthetic-test-reviewer",
    "decided_at": "2026-10-26T12:00:00+09:00",
    "approved_revision": 1,
}


def check_by_id(data, check_id):
    return next(item for item in data["review"]["checks"] if item["id"] == check_id)


load(sample)
load(ready)
load(approved)
print("PASS accept: draft example, synthetic awaiting approval, synthetic approved")

rejects("strict integer type", change(sample, lambda d: d["request"].update(target_duration_seconds="30")))
rejects("unknown top-level field", change(sample, lambda d: d.update(unknown=True)))
rejects("duplicate message ids", change(sample, lambda d: d["request"]["required_messages"].append(deepcopy(d["request"]["required_messages"][0]))))
rejects("required phrase conflicts with forbidden term", change(sample, lambda d: d["request"].update(required_phrases=["무조건 안전"])))
rejects("no required messages or phrases", change(sample, lambda d: d["request"].update(required_messages=[], required_phrases=[])))
rejects("stale review revision", change(sample, lambda d: d.update(revision=2)))
rejects("incomplete approval", change(approved, lambda d: d["approval"].update(reviewer=None)))
rejects("stale approved revision", change(approved, lambda d: d["approval"].update(approved_revision=2)))
rejects("design example cannot be approved", change(approved, lambda d: d.update(execution_mode="design_example")))
rejects("unfinished required check", change(ready, lambda d: check_by_id(d, "schema_format").update(status="not_run")))
rejects("failed required check relabeled as estimate", change(ready, lambda d: check_by_id(d, "required_phrases").update(kind="estimate", status="fail")))
rejects("passed required check relabeled as estimate", change(ready, lambda d: check_by_id(d, "required_phrases").update(kind="estimate", status="pass")))
rejects("semantic check relabeled as deterministic", change(ready, lambda d: check_by_id(d, "message:msg-01").update(kind="deterministic")))
rejects("invented semantic evidence", change(ready, lambda d: check_by_id(d, "message:msg-01").update(evidence="실제 가사에 없는 인용문")))
rejects("empty semantic evidence", change(ready, lambda d: check_by_id(d, "message:msg-01").update(evidence="")))
rejects("missing required check", change(ready, lambda d: d["review"].update(checks=[c for c in d["review"]["checks"] if c["id"] != "forbidden_terms"])))
rejects("duplicate review check id", change(ready, lambda d: d["review"]["checks"].append(deepcopy(d["review"]["checks"][0]))))
rejects("revision retry limit", change(sample, lambda d: d.update(revision_attempts=3)))
rejects("actual duration cannot be verified in MVP", change(sample, lambda d: d["review"].update(duration_verified=True)))

print("PASS: 3 acceptance cases and 19 rejection cases")
print("Scope: data contract only; no LLM, semantic evaluation, workflow, approval UI, or audio execution")
