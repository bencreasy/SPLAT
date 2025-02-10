import base64
import json
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List

from google.cloud import firestore
from google.cloud import pubsub_v1
import structlog

# Configure structured logging
logger = structlog.get_logger()

# Initialize clients
db = firestore.Client()
publisher = pubsub_v1.PublisherClient()

# Configuration
PROJECT_ID = os.getenv('PROJECT_ID')
NOTIFICATION_TOPIC = os.getenv('NOTIFICATION_TOPIC', 'splat-notifications-dev')

class AlertType(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"

class AlertCategory(str, Enum):
    POWER = "POWER"
    SYSTEM = "SYSTEM"
    SENSOR = "SENSOR"

class Alert:
    def __init__(self, alert_type: AlertType, message: str, 
                 value: float, category: AlertCategory):
        self.type = alert_type
        self.message = message
        self.value = value
        self.category = category
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'message': self.message,
            'value': self.value,
            'category': self.category,
            'timestamp': self.timestamp,
        }

def process_alert(event, context) -> None:
    """
    Process incoming alerts from SPLAT Flight 1.
    
    Args:
        event (dict): The Pub/Sub event
        context: Execution context
    """
    try:
        # Extract and decode alert data
        pubsub_message = base64.b64decode(event['data']).decode('utf-8')
        alert_data = json.loads(pubsub_message)
        
        # Process each alert in the message
        alerts = alert_data.get('alerts', [])
        event_id = alert_data.get('event_id')
        timestamp = alert_data.get('timestamp')
        
        processed_alerts = []
        for alert in alerts:
            processed_alert = process_single_alert(alert, event_id, timestamp)
            if processed_alert:
                processed_alerts.append(processed_alert)
        
        # Store alerts in Firestore
        if processed_alerts:
            store_alerts(processed_alerts, event_id)
            
            # Send notifications if needed
            send_notifications(processed_alerts)
            
        logger.info(
            "alerts_processed",
            event_id=event_id,
            alert_count=len(processed_alerts)
        )
        
    except Exception as e:
        logger.error(
            "alert_processing_error",
            error=str(e),
            event_id=context.event_id if context else None
        )
        raise

def process_single_alert(alert: Dict[str, Any], event_id: str, 
                        timestamp: str) -> Dict[str, Any]:
    """Process a single alert and determine its category and severity"""
    alert_type = AlertType(alert['type'])
    value = alert['value']
    message = alert['message']
    
    # Categorize the alert
    if 'voltage' in message.lower():
        category = AlertCategory.POWER
    elif 'temperature' in message.lower():
        category = AlertCategory.SENSOR
    else:
        category = AlertCategory.SYSTEM
    
    # Create alert object
    processed_alert = Alert(
        alert_type=alert_type,
        message=message,
        value=value,
        category=category
    )
    
    return {
        **processed_alert.to_dict(),
        'event_id': event_id,
        'original_timestamp': timestamp
    }

def store_alerts(alerts: List[Dict[str, Any]], event_id: str) -> None:
    """Store alerts in Firestore"""
    # Get alerts collection
    alerts_ref = db.collection('flight1_alerts')
    
    # Create a batch write
    batch = db.batch()
    
    for alert in alerts:
        # Create a new document with auto-generated ID
        alert_ref = alerts_ref.document()
        batch.set(alert_ref, alert)
    
    # Commit the batch
    batch.commit()

def send_notifications(alerts: List[Dict[str, Any]]) -> None:
    """Send notifications for alerts based on severity and rules"""
    notifications = []
    
    for alert in alerts:
        # Only send notifications for CRITICAL alerts in Flight 1
        if alert['type'] == AlertType.CRITICAL:
            notification = create_notification(alert)
            notifications.append(notification)
    
    if notifications:
        # Publish notifications
        topic_path = publisher.topic_path(PROJECT_ID, NOTIFICATION_TOPIC)
        
        for notification in notifications:
            publisher.publish(
                topic_path,
                json.dumps(notification).encode('utf-8')
            )

def create_notification(alert: Dict[str, Any]) -> Dict[str, Any]:
    """Create a notification message from an alert"""
    return {
        'timestamp': alert['timestamp'].isoformat(),
        'title': f"SPLAT Alert: {alert['category']} - {alert['type']}",
        'message': alert['message'],
        'value': alert['value'],
        'event_id': alert['event_id']
    }

def check_alert_deduplication(alert: Dict[str, Any]) -> bool:
    """Check if a similar alert was recently processed"""
    # Get recent alerts
    five_minutes_ago = datetime.now(timezone.utc).timestamp() - (5 * 60)
    
    alerts_ref = db.collection('flight1_alerts')
    recent_alerts = alerts_ref.where(
        'category', '==', alert['category']
    ).where(
        'type', '==', alert['type']
    ).where(
        'timestamp', '>=', five_minutes_ago
    ).limit(1).stream()
    
    return any(recent_alerts)
