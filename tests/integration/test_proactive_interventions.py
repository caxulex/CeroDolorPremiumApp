 

def test_proactive_interventions():
    from backend.src.services.aiper_service import generate_intervention
    intervention = generate_intervention("test_patient")
    assert isinstance(intervention, str)