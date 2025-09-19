import json
import os

import jsonschema
import pytest


def test_aip_to_asd_contract():
    # Load schema
    schema_path = os.path.join(os.path.dirname(__file__), '..', '..', 'specs', '001-description-esta-secci', 'contracts', 'aip_to_asd.json')
    with open(schema_path) as f:
        schema = json.load(f)
    
    # Sample valid message
    valid_message = {
        "message_type": "pain_submission",
        "patient_id": "123",
        "timestamp": "2025-09-15T10:00:00Z",
        "pain_data": {
            "level": 7,
            "description": "dolor punzante",
            "mood": "ansioso",
            "sleep_quality": "mal"
        }
    }
    
    # Should not raise exception
    jsonschema.validate(valid_message, schema)
    
    # Invalid message should raise
    invalid_message = {"invalid": "data"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(invalid_message, schema)