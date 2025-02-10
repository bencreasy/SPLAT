import base64
import json
import pytest
from unittest.mock import Mock, patch

import main

@pytest.fixture
def valid_telemetry():
    return {
        'solarVoltage': 5.1,
        'solarCurrent': 100.0,
        'batteryVoltage': 3.7,
        'systemCurrent': 50.0,
        'temperature': 25.0,
        'uptime': 3600,
        'errors': 0
    }

@pytest.fixture
def pubsub_event(valid_telemetry):
    return {
        'data': base64.b64encode(json.dumps(valid_telemetry).encode('utf-8'))
    }

@pytest.fixture
def context():
    return Mock(event_id='test-event-123')

def test_validate_telemetry_valid(valid_telemetry):
    # Should not raise any exceptions
    main.validate_telemetry(valid_telemetry)

def test_validate_telemetry_missing_field():
    invalid_data = {
        'solarVoltage': 5.1,
        # Missing required fields
    }
    with pytest.raises(main.ValidationError):
        main.validate_telemetry(invalid_data)

def test_validate_telemetry_invalid_range():
    invalid_data = {
        'solarVoltage': 10.0,  # Too high
        'solarCurrent': 100.0,
        'batteryVoltage': 3.7,
        'systemCurrent': 50.0,
        'temperature': 25.0,
        'uptime': 3600,
        'errors': 0
    }
    with pytest.raises(main.ValidationError):
        main.validate_telemetry(invalid_data)

@patch('main.store_raw_data')
@patch('main.store_processed_data')
@patch('main.check_alert_conditions')
def test_process_telemetry(mock_check_alerts, mock_store_processed, 
                          mock_store_raw, pubsub_event, context):
    main.process_telemetry(pubsub_event, context)
    
    mock_store_raw.assert_called_once()
    mock_store_processed.assert_called_once()
    mock_check_alerts.assert_called_once()

@patch('main.publisher')
def test_check_alert_conditions_battery_low(mock_publisher):
    data = {
        'batteryVoltage': 3.2,
        'temperature': 25.0,
        'errors': 0,
        'processed_timestamp': '2025-02-09T12:00:00Z',
        'event_id': 'test-123'
    }
    
    main.check_alert_conditions(data)
    mock_publisher.publish.assert_called_once()
