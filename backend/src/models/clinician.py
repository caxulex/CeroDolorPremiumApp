class Clinician:
    def __init__(self, clinician_id: str, name: str):
        self.id = clinician_id
        self.name = name
        self.patients: list[str] = []  # list of patient ids

    def add_patient(self, patient_id: str):
        if patient_id not in self.patients:
            self.patients.append(patient_id)
