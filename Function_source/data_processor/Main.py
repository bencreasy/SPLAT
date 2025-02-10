import base64
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any

from google.cloud import bigquery
from google.cloud import storage
from google.cloud import pubsub_v1
import structlog

# Configure structured logging
logger = structlog.get_logger()

# Initialize clients
bq_client = bigquery.Client()
storage_client = storage.Client()
publisher = pubsub_v1.PublisherClient()

# Configuration
PROJECT_ID = os.getenv('PROJECT_ID')
DATASET_ID = os.getenv('DATASET_ID', 'splat_telemetry_dev')
RAW_BUCKET = os.getenv('RAW_BUCKET', 'splat-raw-dev')
ALERT_TOPIC = os.getenv('ALERT_TOPIC', 'splat-alerts-dev')

class ValidationError(Exception):
    """Custom exception for data validation errors"""
    pass

def validate_telemetry(data: Dict[str, Any]) -> None:
    """
    Validates the structure and content of telemetry data.
    Raises ValidationError if data is invalid.
    """
    required_fields = {
        'solarVoltage', 'solarCurrent', 'batteryVoltage', 
        'systemCurrent', 'temperature', 'uptime', 'errors'
    }
    
    # Check required fields
    missing_fields = required_fields - set(data.keys())
    if missing_fields:
        raise ValidationError(f"Missing required fields: {missing_fields}")
    
    # Validate value ranges
    try:
        if not (0 <= data['solarVoltage'] <= 6.0):
            raise ValidationError("Solar voltage out of range (0-6V)")
        if not (0 <= data['batteryVoltage'] <= 4.2):
            raise ValidationError("Battery voltage out of range (0-4.2V)")
        if not (-20 <= data['temperature'] <= 85):
            raise ValidationError("Temperature out of range (-20 to 85°C)")
    except (TypeError, ValueError) as e:
        raise ValidationError(f"Invalid value type: {str(e)}")

def process_telemetry(event, context):
    """
    Process incoming telemetry data from SPLAT Flight 1.
    
    Args:
        event (dict): The Pub/Sub event
        context: Execution context
    """
    try:
        # Extract and decode data
        pubsub_message = base64.b64decode(event['data']).decode('utf-8')
        telemetry_data = json.loads(pubsub_message)
        
        # Add processing metadata
        telemetry_data['processed_timestamp'] = datetime.now(timezone.utc).isoformat()
        telemetry_data['event_id'] = context.event_id
        
        # Validate data
        validate_telemetry(telemetry_data)
        
        # Store raw data
        store_raw_data(telemetry_data, context.event_id)
        
        # Process and store in BigQuery
        store_processed_data(telemetry_data)
        
        # Check for alert conditions
        check_alert_conditions(telemetry_data)
        
        logger.info(
            "telemetry_processed",
            event_id=context.event_id,
            battery_voltage=telemetry_data['batteryVoltage'],
            uptime=telemetry_data['uptime']
        )
        
    except Exception as e:
        logger.error(
            "telemetry_processing_error",
            error=str(e),
            event_id=context.event_id if context else None
        )
        raise

def store_raw_data(data: Dict[str, Any], event_id: str) -> None:
    """Store raw telemetry data in Cloud Storage"""
    bucket = storage_client.bucket(RAW_BUCKET)
    timestamp = datetime.now(timezone.utc)
    blob_name = f"{timestamp.year}/{timestamp.month}/{timestamp.day}/{event_id}.json"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(
        json.dumps(data),
        content_type='application/json'
    )

def store_processed_data(data: Dict[str, Any]) -> None:
    """Store processed telemetry data in BigQuery"""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.flight1_telemetry"
    
    # Transform data for BigQuery
    row = {
        'timestamp': data['processed_timestamp'],
        'event_id': data['event_id'],
        'solar_voltage': data['solarVoltage'],
        'solar_current': data['solarCurrent'],
        'battery_voltage': data['batteryVoltage'],
        'system_current': data['systemCurrent'],
        'temperature': data['temperature'],
        'uptime': data['uptime'],
        'error_count': data['errors']
    }
    
    errors = bq_client.insert_rows_json(table_id, [row])
    if errors:
        raise Exception(f"BigQuery insert errors: {errors}")

def check_alert_conditions(data: Dict[str, Any]) -> None:
    """Check telemetry for alert conditions"""
    alerts = []
    
    # Battery voltage alerts
    if data['batteryVoltage'] < 3.3:
        alerts.append({
            'type': 'CRITICAL',
            'message': 'Battery voltage critical',
            'value': data['batteryVoltage']
        })
    elif data['batteryVoltage'] < 3.5:
        alerts.append({
            'type': 'WARNING',
            'message': 'Battery voltage low',
            'value': data['batteryVoltage']
        })
    
    # Temperature alerts
    if data['temperature'] > 75:
        alerts.append({
            'type': 'WARNING',
            'message': 'High temperature detected',
            'value': data['temperature']
        })
    
    # Error count alerts
    if data['errors'] > 0:
        alerts.append({
            'type': 'WARNING',
            'message': f"Device reported {data['errors']} errors",
            'value': data['errors']
        })
    
    # Publish alerts if any
    if alerts:
        alert_data = {
            'timestamp': data['processed_timestamp'],
            'event_id': data['event_id'],
            'alerts': alerts
        }
        
        topic_path = publisher.topic_path(PROJECT_ID, ALERT_TOPIC)
        publisher.publish(
            topic_path,
            json.dumps(alert_data).encode('utf-8')
        )
