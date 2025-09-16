 

def test_clinician_summary():
    from backend.src.services.aic_service import generate_summary
    summary = generate_summary("test_patient")
    assert "summary" in summary.lower()