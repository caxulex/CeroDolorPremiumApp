 

def test_mood_sleep_registration():
    from backend.src.services.aip_service import register_mood_sleep
    result = register_mood_sleep("test_patient", "ansioso", "mal")
    assert result is not None