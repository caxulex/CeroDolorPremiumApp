from .pain_record import PainRecord


class Patient:
    def __init__(self, patient_id: str, name: str):
        self.id = patient_id
        self.name = name
        self.pain_history: list[PainRecord] = []

    def add_pain_record(self, record: PainRecord) -> None:
        self.pain_history.append(record)

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"Patient(id={self.id!r}, name={self.name!r}, pain_history={len(self.pain_history)} records)"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Patient):
            return False
        return self.id == other.id and self.name == other.name and self.pain_history == other.pain_history
