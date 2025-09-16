class Clinician:
    def __init__(self, clinician_id: str, name: str):
        self.id = clinician_id
        self.name = name
        self.patients: list[str] = []  # list of patient ids

    def add_patient(self, patient_id: str):
        if patient_id not in self.patients:
            self.patients.append(patient_id)

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"Clinician(id={self.id!r}, name={self.name!r}, patients={len(self.patients)})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Clinician):  # pragma: no cover - defensive
            return False
        return self.id == other.id and self.name == other.name and self.patients == other.patients
