"""여행 도메인 Agent의 역할·지침·Tool을 정의합니다."""

from typing import Any

from app.agents.runtime import ToolDecision, run_agent, select_tool
from app.schemas.stage_03 import ToolCompleteResult
from app.tools.registry import get_tool_definitions


TRAVEL_AGENT_NAME = "travel_lookup_agent"

# 시스템 메세지 형태랑 동일하다..그래서 즉 시스템 메시지이다?
TRAVEL_AGENT_INSTRUCTIONS = """
당신은 여행 조회 Agent입니다.
사용자의 질문을 해결하기 위해 필요한 경우 날씨, 숙소 또는 관광지 Tool 하나를 선택하세요.
필수 입력값이 부족하면 추측하지 말고, 허용된 Tool 외에는 선택하지 마세요.
""".strip()

TRAVEL_FINAL_ANSWER_INSTRUCTIONS = """
당신은 친절한 여행 도우미입니다.
Tool Result에 포함된 정보만 사용해 한국어로 답변하고, 결과에 없는 값은 추측하지 마세요.
""".strip()


def get_travel_tools() -> list[dict[str, Any]]:
    """여행 Agent가 사용할 수 있는 Tool 목록입니다."""
    return get_tool_definitions()


def select_travel_tool(
    message: str,
    tool_choice: str = "auto",
) -> ToolDecision:
    """여행 Agent의 지침과 Tool을 사용해 실행할 Tool을 선택합니다."""
    return select_tool(
        message=message,
        instructions=TRAVEL_AGENT_INSTRUCTIONS,
        tools=get_travel_tools(),
        tool_choice=tool_choice, # 현재는 auto 이지만 여기선 특정 툴을 사용하게만 할 수도 있다.
    )


def run_travel_agent(
    message: str,
    tool_choice: str = "auto",
) -> ToolCompleteResult:
    """여행 질문을 Tool 선택 → 실행 → 최종 답변 순서로 처리합니다."""
    # run_agent가 없다면 이 안에서 엄청난 작업하는 부분이 있어야하다보니, Agent를 실행하는 역할을 분리했다...그 부분이 runtime.py이 하는 역할이다..
    # 아래 형식대로 주기만 하면 agent를 실행한다 
    # 이렇게 심플해진 이유는 runtime.py을 구현해놨기때문에 그것을 사용하기만 하면 되어서이다..
    return run_agent(
        message=message,
        instructions=TRAVEL_AGENT_INSTRUCTIONS,
        final_answer_instructions=TRAVEL_FINAL_ANSWER_INSTRUCTIONS,
        tools=get_travel_tools(), # registry에 등록한 tool list를 가져오는것이다.
        tool_choice=tool_choice,
    )
