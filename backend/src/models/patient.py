from .pain_record import PainRecord


class Patient:
    def __init__(self, patient_id: str, name: str):
        self.id = patient_id
        self.name = name
        self.pain_history: list[PainRecord] = []

    def add_pain_record(self, record: PainRecord) -> None:
        self.pain_history.append(record)
