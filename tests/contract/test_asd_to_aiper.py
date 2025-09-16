import json
import jsonschema
import pytest
import os

def test_asd_to_aiper_contract():
    # Load schema
    schema_path = os.path.join(os.path.dirname(__file__), '..', '..', 'specs', '001-description-esta-secci', 'contracts', 'asd_to_aiper.json')
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    # Sample valid message
    valid_message = {
        "message_type": "insights",
        "patient_id": "123",
        "timestamp": "2025-09-15T10:00:00Z",
        "insights": {
            "patterns_detected": ["patron de dolor matutino"],
            "trend_analysis": "dolor aumenta con ansiedad",
            "risk_flags": ["riesgo de depresión"]
        }
    }
    
    # Should not raise exception
    jsonschema.validate(valid_message, schema)
    
    # Invalid message should raise
    invalid_message = {"invalid": "data"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(invalid_message, schema)