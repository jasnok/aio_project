from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


ProviderName = Literal["mock", "gemini", "openai", "ollama"]
TravelPlaceType = Literal["landmark", "food"]


class TravelModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TravelPlanAgentRequest(TravelModel):
    message: str = Field(min_length=1, max_length=2000)
    user_id: UUID | None = None
    provider: ProviderName = "mock"
    landmark_count: int = Field(default=6, ge=0, le=10)
    food_count: int = Field(default=4, ge=0, le=10)
    save_requested: bool = False


class TravelPlanGenerateRequest(TravelModel):
    message: str = Field(min_length=1, max_length=2000)
    provider: ProviderName = "mock"
    landmark_count: int = Field(default=6, ge=0, le=10)
    food_count: int = Field(default=4, ge=0, le=10)
    save_requested: bool = False


class TravelPlanIntent(TravelModel):
    destination: str = "부산"
    nights: int = Field(ge=0, le=29)
    days: int = Field(ge=1, le=30)
    preferences: list[str] = Field(default_factory=list, max_length=10)
    landmark_queries: list[str] = Field(default_factory=list, max_length=5)
    food_keyword: str = Field(default="", max_length=100)
    include_favorites: bool = False
    follow_up_question: str = Field(default="", max_length=300)

    @model_validator(mode="after")
    def validate_duration(self) -> "TravelPlanIntent":
        if self.days != self.nights + 1:
            raise ValueError("days must equal nights + 1")
        return self


class TravelCandidate(TravelModel):
    candidate_id: str = Field(min_length=1)
    internal_place_id: UUID | None = None
    name: str = Field(min_length=1)
    place_type: TravelPlaceType
    category_name: str = ""
    category_group_code: str = ""
    address: str = ""
    road_address: str = ""
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    phone: str = ""
    kakao_place_url: str
    is_favorite: bool = False


class ItinerarySelection(TravelModel):
    candidate_id: str = Field(min_length=1)
    day: int = Field(ge=1, le=30)
    order: int = Field(ge=1, le=20)
    reason: str = Field(min_length=1, max_length=300)


class ItineraryDraft(TravelModel):
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=500)
    selections: list[ItinerarySelection] = Field(default_factory=list, max_length=20)


class ScheduledTravelPlace(TravelModel):
    id: str = Field(min_length=1)
    internal_place_id: UUID | None = None
    name: str = Field(min_length=1)
    place_type: TravelPlaceType
    category_name: str = ""
    category_group_code: str = ""
    description: str = Field(min_length=1, max_length=300)
    address: str = ""
    road_address: str = ""
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    phone: str = ""
    kakao_place_url: str
    day: int = Field(ge=1, le=30)
    order: int = Field(ge=1, le=20)
    is_favorite: bool = False


class BusanTravelPlanResult(TravelModel):
    destination: str = "부산"
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=500)
    nights: int = Field(ge=0, le=29)
    days: int = Field(ge=1, le=30)
    preferences: list[str] = Field(default_factory=list, max_length=10)
    landmarks: list[ScheduledTravelPlace] = Field(default_factory=list, max_length=10)
    foods: list[ScheduledTravelPlace] = Field(default_factory=list, max_length=10)
    warnings: list[str] = Field(default_factory=list, max_length=20)
    follow_up_question: str = Field(default="", max_length=300)
    saved_plan_id: UUID | None = None

    @model_validator(mode="after")
    def validate_plan(self) -> "BusanTravelPlanResult":
        if self.days != self.nights + 1:
            raise ValueError("days must equal nights + 1")
        places = [*self.landmarks, *self.foods]
        if any(place.day > self.days for place in places):
            raise ValueError("place day exceeds trip duration")
        ids = [place.id for place in places]
        if len(ids) != len(set(ids)):
            raise ValueError("scheduled place ids must be unique")
        return self


class TravelPlanGenerateResponse(TravelModel):
    provider: ProviderName
    model: str
    latency_ms: int = Field(ge=0)
    content: BusanTravelPlanResult
    warnings: list[str] = Field(default_factory=list)
