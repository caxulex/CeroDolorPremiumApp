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
