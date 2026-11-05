from typing import Protocol
from uuid import UUID

from supabase import Client, create_client

from app.config import settings


class TravelPlanRepository(Protocol):
    def create_plan(
        self,
        user_id: UUID,
        title: str,
        summary: str,
        days: int,
    ) -> UUID: ...

    def add_places(self, plan_id: UUID, places: list[dict]) -> None: ...

    def delete_plan(self, plan_id: UUID) -> None: ...


class SupabaseTravelPlanRepository:
    def __init__(self, client: Client) -> None:
        self.client = client

    def create_plan(
        self,
        user_id: UUID,
        title: str,
        summary: str,
        days: int,
    ) -> UUID:
        result = self.client.table("travel_plans").insert(
            {
                "user_id": str(user_id),
                "title": title,
                "summary": summary,
                "days": days,
            }
        ).execute()
        return UUID(result.data[0]["id"])

    def add_places(self, plan_id: UUID, places: list[dict]) -> None:
        if places:
            self.client.table("travel_plan_places").insert(
                [{"plan_id": str(plan_id), **item} for item in places]
            ).execute()

    def delete_plan(self, plan_id: UUID) -> None:
        self.client.table("travel_plans").delete().eq("id", str(plan_id)).execute()


def create_travel_plan_repository() -> SupabaseTravelPlanRepository:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("SUPABASE_URL과 SUPABASE_SERVICE_ROLE_KEY 설정이 필요합니다.")
    return SupabaseTravelPlanRepository(
        create_client(settings.supabase_url, settings.supabase_service_role_key)
    )
