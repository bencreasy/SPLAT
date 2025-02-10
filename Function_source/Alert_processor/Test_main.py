import base64
import json
from datetime import datetime, timezone
import pytest
from unittest.mock import Mock, patch

import main
from main import AlertType, AlertCategory, Alert

@pytest.fixture
def sample_alert_data():
    return {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event_id': 'test-event-123',
        'alerts': [
            {
                'type': 'CRITICAL',
                'message': 'Battery voltage critical',
                'value': 3.2
            },
            {
                'type': 'WARNING',
                'message': 'High temperature detected',
                'value': 76.5
            }
        ]
    }

@pytest.fixture
def pubsub_event(sample_alert_data):
    return {
        'data': base64.b64encode(json.dumps(sample_alert_data).encode('utf-8'))
    }

@pytest.fixture
def context():
    return Mock(event_id='test-event-123')

def test_process_single_alert():
    alert = {
        'type': 'CRITICAL',
        'message': 'Battery voltage critical',
        'value': 3.2
    }
    event_id = 'test-123'
    timestamp = datetime.now(timezone.utc).isoformat()
    
    result = main.process_single_alert(alert, event_id, timestamp)
    
    assert result['type'] == AlertType.CRITICAL
    assert result['category'] == AlertCategory.POWER
    assert result['value'] == 3.2
    assert result['event_id'] == event_id

@patch('main.store_alerts')
@patch('main.send_notifications')
def test_process_alert(mock_send_notifications, mock_store_alerts, 
                      pubsub_event, context):
    main.process_alert(pubsub_event, context)
    
    mock_store_alerts.assert_called_once()
    mock_send_notifications.assert_called_once()

@patch('main.publisher')
def test_send_notifications(mock_publisher):
    alerts = [
        {
            'type': AlertType.CRITICAL,
            'message': 'Test alert',
            'value': 1.0,
            'category': AlertCategory.SYSTEM,
            'event_id': 'test-123',
            'timestamp': datetime.now(timezone.utc)
        }
    ]
    
    main.send_notifications(alerts)
    mock_publisher.publish.assert_called_once()

def test_create_notification():
    alert = {
        'type': AlertType.CRITICAL,
        'message': 'Test alert',
        'value': 1.0,
        'category': AlertCategory.SYSTEM,
        'event_id': 'test-123',
        'timestamp': datetime.now(timezone.utc)
    }
    
    notification = main.create_notification(alert)
    
    assert 'title' in notification
    assert 'message' in notification
    assert 'value' in notification
    assert 'event_id' in notification
