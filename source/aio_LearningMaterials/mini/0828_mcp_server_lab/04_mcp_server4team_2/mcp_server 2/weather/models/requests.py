from pydantic import BaseModel, Field, model_validator


class WeatherRequest(BaseModel):
    city: str = Field(min_length=1, max_length=100)
    days: int = Field(default=3, ge=1, le=7)

    @model_validator(mode="after")
    def strip_city(self):
        self.city = self.city.strip()
        if not self.city:
            raise ValueError("city는 비어 있을 수 없습니다.")
        return self
