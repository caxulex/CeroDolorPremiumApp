 

def test_empathetic_feedback():
    from backend.src.services.aip_service import provide_feedback
    response = provide_feedback("test_patient", "high pain")
    assert "empathetic" in response.lower()