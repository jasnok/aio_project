from fastapi.testclient import TestClient

from app.main import create_app


def test_mock_travel_plan_endpoint_returns_grounded_schedule() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/api/travel-plans/generate", json={
            "message": "부산 2박 3일 가족여행 코스 짜줘. 바다와 맛집을 좋아해.",
            "provider": "mock", "landmark_count": 2, "food_count": 2,
        })
    assert response.status_code == 200
    content = response.json()["content"]
    assert content["days"] == 3
    assert len(content["landmarks"]) == 2
    assert len(content["foods"]) == 2
    assert all(place["day"] <= 3 for place in [*content["landmarks"], *content["foods"]])


def test_unauthenticated_save_request_does_not_write_and_returns_warning() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/api/travel-plans/generate", json={
            "message": "부산 하루 코스를 저장해줘", "provider": "mock",
            "landmark_count": 1, "food_count": 1, "save_requested": True,
        })
    assert response.status_code == 200
    content = response.json()["content"]
    assert content["saved_plan_id"] is None
    assert any("로그인" in warning for warning in content["warnings"])
