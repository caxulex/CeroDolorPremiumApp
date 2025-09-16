 

def test_daily_checkin():
    from backend.src.services.aip_service import initiate_daily_checkin
    response = initiate_daily_checkin("test_patient")
    assert isinstance(response, str)
    assert len(response) > 0