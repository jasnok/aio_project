from ..models.weather import Location

CITY_COORDINATES = {
    "서울": (37.5665, 126.9780, 60, 127),
    "부산": (35.1796, 129.0756, 98, 76),
}


async def resolve_location(city: str) -> Location:
    if city in CITY_COORDINATES:
        lat, lon, nx, ny = CITY_COORDINATES[city]
        return Location(city, lat, lon, nx, ny)
    raise ValueError(f"지원하지 않는 도시입니다: {city}")
