from time import perf_counter
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.agents.busan_travel_plan_agent import BusanTravelPlanAgent
from app.auth.models import AuthUser
from app.auth.service import InvalidCredentialsError, get_auth_service
from app.config import settings
from app.favorites.repository import create_favorite_repository
from app.places.repository import create_place_repository
from app.routers.landmark_router import get_landmark_search_service
from app.routers.place_router import get_place_search_service
from app.tools.get_favorite_places import GetFavoritePlacesTool
from app.tools.save_travel_plan import SaveTravelPlanTool
from app.tools.search_landmarks import SearchLandmarksTool
from app.tools.search_places import SearchPlacesTool
from app.travel.llm_service import TravelPlanLLMService
from app.travel.mock_services import MockLandmarkSearchService, MockPlaceSearchService
from app.travel.models import (
    ProviderName,
    TravelPlanAgentRequest,
    TravelPlanGenerateRequest,
    TravelPlanGenerateResponse,
)
from app.travel.repository import create_travel_plan_repository


router = APIRouter(tags=["Food"])
agent_router = router
structured_output_router = APIRouter()
_optional_bearer = HTTPBearer(auto_error=False)


def optional_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_optional_bearer),
    ],
) -> AuthUser | None:
    if credentials is None:
        return None
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    try:
        return get_auth_service().authenticate(credentials.credentials)
    except InvalidCredentialsError as error:
        raise HTTPException(status_code=401, detail="로그인 세션이 만료되었습니다.") from error


def create_travel_plan_agent(
    request: Request,
    user: AuthUser | None,
    provider: ProviderName,
) -> BusanTravelPlanAgent:
    if provider == "mock":
        landmark_service = MockLandmarkSearchService()
        place_service = MockPlaceSearchService()
    else:
        landmark_service = get_landmark_search_service(request)
        place_service = get_place_search_service(request)

    favorites_tool = None
    save_tool = None
    if user is not None:
        favorites_tool = GetFavoritePlacesTool(create_favorite_repository())
        save_tool = SaveTravelPlanTool(
            create_travel_plan_repository(),
            create_place_repository(),
        )
    return BusanTravelPlanAgent(
        TravelPlanLLMService(provider),
        SearchLandmarksTool(landmark_service),
        SearchPlacesTool(place_service),
        favorites_tool,
        save_tool,
    )


def _provider_model(provider: ProviderName) -> str:
    return {
        "mock": "deterministic-travel-plan-mock",
        "gemini": settings.gemini_model,
        "openai": settings.openai_model,
        "ollama": settings.ollama_model,
    }[provider]


@router.post(
    "/api/travel-plans/generate",
    response_model=TravelPlanGenerateResponse,
)
async def generate_travel_plan(
    payload: TravelPlanGenerateRequest,
    request: Request,
    user: Annotated[AuthUser | None, Depends(optional_current_user)],
) -> TravelPlanGenerateResponse:
    started_at = perf_counter()
    agent = create_travel_plan_agent(request, user, payload.provider)
    try:
        content = await agent.run(
            TravelPlanAgentRequest(
                **payload.model_dump(),
                user_id=user.id if user else None,
            )
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="여행 일정 생성에 실패했습니다.") from error
    return TravelPlanGenerateResponse(
        provider=payload.provider,
        model=_provider_model(payload.provider),
        latency_ms=int((perf_counter() - started_at) * 1000),
        content=content,
        warnings=content.warnings,
    )
