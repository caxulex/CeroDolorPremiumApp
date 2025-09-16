 

def test_pain_registration():
    from backend.src.services.aip_service import register_pain
    result = register_pain("test_patient", 7, "punzante")
    assert result is not None