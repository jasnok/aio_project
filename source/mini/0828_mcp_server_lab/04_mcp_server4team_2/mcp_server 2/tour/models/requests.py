from pydantic import BaseModel, Field


class HotelSearchRequest(BaseModel):
    city: str = Field(min_length=1)
    max_price: int | None = Field(default=None, ge=1)
    keyword: str | None = None


class SpotSearchRequest(BaseModel):
    city: str = Field(min_length=1)
    category: str | None = None
    keyword: str | None = None
