from datetime import datetime

PAIN_MIN = 1
PAIN_MAX = 10


class PainRecord:
    def __init__(
        self,
        date: datetime,
        pain_level: int,
        description: str | None = None,
        mood: str | None = None,
        sleep: str | None = None,
    ) -> None:
        if not PAIN_MIN <= pain_level <= PAIN_MAX:
            msg = "Pain level must be between 1 and 10"
            raise ValueError(msg)
        self.date = date
        self.pain_level = pain_level
        self.description = description
        self.mood = mood
        self.sleep = sleep

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return (
            f"PainRecord(date={self.date.isoformat()}, pain_level={self.pain_level}, "
            f"mood={self.mood!r}, sleep={self.sleep!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PainRecord):  # pragma: no cover - defensive
            return False
        return (
            self.date == other.date
            and self.pain_level == other.pain_level
            and self.description == other.description
            and self.mood == other.mood
            and self.sleep == other.sleep
        )
