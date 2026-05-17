from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator


class IESEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    platform_version: str = "2.0.0"
    module: dict
    asset: dict
    event: dict
    data: dict
    metadata: dict = Field(default_factory=dict)

    @field_validator("platform_version")
    @classmethod
    def validate_platform_version(cls, v: str) -> str:
        if v != "2.0.0":
            raise ValueError("platform_version must be exactly '2.0.0'")
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        if not v.endswith("Z"):
            raise ValueError("timestamp must end with 'Z' (UTC)")
        return v

    @field_validator("event_id")
    @classmethod
    def validate_event_id(cls, v: str) -> str:
        if len(v) != 36 or v.count("-") != 4:
            raise ValueError("event_id must be a valid UUID v4")
        return v

    @field_validator("data")
    @classmethod
    def validate_no_payload(cls, v: dict) -> dict:
        return v

    def model_post_init(self, __context) -> None:
        # Garantizar snake_case en event.type y module.id
        if "type" in self.event:
            et = self.event["type"]
            if et != et.lower().replace("-", "_"):
                raise ValueError(f"event.type must be snake_case, got: {et}")
        if "id" in self.module:
            mid = self.module["id"]
            if mid != mid.lower().replace("-", "_"):
                raise ValueError(f"module.id must be snake_case, got: {mid}")
        valid_categories = {
            "quality",
            "productivity",
            "maintenance",
            "energy",
            "safety",
            "configuration",
            "system",
        }
        if "category" in self.event and self.event["category"] not in valid_categories:
            raise ValueError(f"event.category must be one of {valid_categories}")
        valid_severities = {"low", "medium", "high", "critical"}
        if "severity" in self.event and self.event["severity"] not in valid_severities:
            raise ValueError(f"event.severity must be one of {valid_severities}")
