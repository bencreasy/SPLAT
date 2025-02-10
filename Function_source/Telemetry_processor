import json
from datetime import datetime, timezone
import pytest
from unittest.mock import Mock, patch
import numpy as np

import main

@pytest.fixture
def sample_telemetry():
    return {
        'processed_timestamp': datetime.now(timezone.utc).isoformat(),
        'event_id': 'test-event-123',
        'solarVoltage': 5.1,
        'solarCurrent': 100.0,
        'batteryVoltage': 3.7,
        'systemCurrent': 50.0,
        'temperature': 25.0,
        'uptime': 3600,
        'errors': 0
    }

@pytest.fixture
def gcs_event():
    return {
        'bucket': 'test-bucket',
        'name': 'test/path/data.json'
    }

def test_calculate_power_metrics(sample_telemetry):
    metrics = main.calculate_power_metrics(sample_telemetry)
    
    assert isinstance(metrics, main.PowerMetrics)
    assert 0 <= metrics.solar_efficiency <= 100
    assert metrics.power_consumption > 0
    assert isinstance(metrics.estimated_runtime, float)

def test_calculate_system_health(sample_telemetry):
    with patch('main.get_temperature_trend', return_value=0.0):
        health = main.calculate_system_health(sample_telemetry)
    
    assert isinstance(health, main.SystemHealth)
    assert 0 <= health.health_score <= 100
    assert health.error_rate >= 0

def test_estimate_battery_capacity():
    assert main.estimate_battery_capacity(4.2) == 2600  # Full
    assert main.estimate_battery_capacity(3.2) == 0     # Empty
    assert 0 < main.estimate_battery_capacity(3.7) < 2600  # Partial

def test_calculate_health_score():
    score = main.calculate_health_score(
        battery_voltage=3.7,
        error_rate=0.1,
        temperature=25.0
    )
    assert 0 <= score <= 100

@patch('main.storage_client')
@patch('main.bq_client')
def test_process_telemetry(mock_bq, mock_storage, sample_telemetry, gcs_event):
    # Mock storage blob
    mock_blob = Mock()
    mock_blob.download_as_string.return_value = json.dumps(sample_telemetry).encode()
    mock_bucket = Mock()
    mock_bucket.blob.return_value = mock_blob
    mock_storage.bucket.return_value = mock_bucket
    
    # Process telemetry
    main.process_telemetry(gcs_event, None)
    
    # Verify storage and BigQuery were called
    assert mock_storage.bucket.called
    assert mock_bq.insert_rows_json.called
