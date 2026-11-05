"""선택 이미지 식별 결과는 검증한 문자열만 사진 짝짓기에 전달합니다."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, field_validator, ValidationError


class ImageLabel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    house_name: str = ""
    kind: Literal["", "위치도", "평면도", "외관", "실내", "주차장", "안내그림", "로고"] = ""

    @field_validator("house_name", "kind", mode="before")
    @classmethod
    def trim_nullable_text(cls, value):
        if value is None:
            return ""
        return value.strip() if isinstance(value, str) else value


def validated_image_labels(items: list, count: int) -> list[dict]:
    labels = []
    for index in range(count):
        item = items[index] if index < len(items) else {}
        try:
            label = ImageLabel.model_validate(item)
        except ValidationError:
            label = ImageLabel()
        labels.append(label.model_dump())
    return labels
