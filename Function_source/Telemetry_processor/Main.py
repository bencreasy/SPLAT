import base64
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from google.cloud import bigquery
from google.cloud import storage
import numpy as np
import pandas as pd
import structlog

# Configure structured logging
logger = structlog.get_logger()

# Initialize clients
bq_client = bigquery.Client()
storage_client = storage.Client()

# Configuration
PROJECT_ID = os.getenv('PROJECT_ID')
DATASET_ID = os.getenv('DATASET_ID', 'splat_telemetry_dev')
ANALYTICS_BUCKET = os.getenv('ANALYTICS_BUCKET', 'splat-analytics-dev')

@dataclass
class PowerMetrics:
    """Power system derived metrics"""
    solar_efficiency: float
    power_consumption: float
    charging_rate: float
    estimated_runtime: float

@dataclass
class SystemHealth:
    """System health metrics"""
    error_rate: float
    uptime: float
    temperature_trend: float
    health_score: float

def process_telemetry(event, context) -> None:
    """
    Transform telemetry data for analytics.
    
    Args:
        event (dict): The Cloud Storage event
        context: Execution context
    """
    try:
        # Get the trigger file from Cloud Storage
        bucket = storage_client.bucket(event['bucket'])
        blob = bucket.blob(event['name'])
        content = blob.download_as_string()
        telemetry_data = json.loads(content)

        # Process the telemetry
        processed_data = transform_telemetry(telemetry_data)
        
        # Store processed data
        store_processed_data(processed_data)
        
        # Generate and store analytics
        analytics_data = generate_analytics(processed_data)
        store_analytics(analytics_data)
        
        logger.info(
            "telemetry_transformed",
            file=event['name'],
            health_score=analytics_data['health_score']
        )
        
    except Exception as e:
        logger.error(
            "transformation_error",
            error=str(e),
            file=event['name'] if event else None
        )
        raise

def transform_telemetry(data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform raw telemetry into processed format"""
    power_metrics = calculate_power_metrics(data)
    system_health = calculate_system_health(data)
    
    return {
        'timestamp': data['processed_timestamp'],
        'event_id': data['event_id'],
        
        # Power metrics
        'solar_efficiency': power_metrics.solar_efficiency,
        'power_consumption': power_metrics.power_consumption,
        'charging_rate': power_metrics.charging_rate,
        'estimated_runtime': power_metrics.estimated_runtime,
        
        # System health
        'error_rate': system_health.error_rate,
        'uptime': system_health.uptime,
        'temperature_trend': system_health.temperature_trend,
        'health_score': system_health.health_score,
        
        # Original metrics
        'raw_metrics': {
            'solar_voltage': data['solarVoltage'],
            'solar_current': data['solarCurrent'],
            'battery_voltage': data['batteryVoltage'],
            'system_current': data['systemCurrent'],
            'temperature': data['temperature']
        }
    }

def calculate_power_metrics(data: Dict[str, Any]) -> PowerMetrics:
    """Calculate derived power system metrics"""
    # Calculate solar power efficiency
    solar_power = data['solarVoltage'] * data['solarCurrent']
    max_solar_power = 6.0 * 1000  # Maximum theoretical power (6V * 1000mA)
    solar_efficiency = (solar_power / max_solar_power) * 100 if max_solar_power > 0 else 0
    
    # Calculate power consumption
    power_consumption = data['batteryVoltage'] * data['systemCurrent']
    
    # Calculate charging rate (mA)
    charging_rate = data['solarCurrent'] - data['systemCurrent']
    
    # Estimate runtime based on battery voltage and consumption
    battery_capacity = 2600  # mAh for 18650 battery
    remaining_capacity = estimate_battery_capacity(data['batteryVoltage'])
    estimated_runtime = (remaining_capacity / data['systemCurrent']) if data['systemCurrent'] > 0 else float('inf')
    
    return PowerMetrics(
        solar_efficiency=solar_efficiency,
        power_consumption=power_consumption,
        charging_rate=charging_rate,
        estimated_runtime=estimated_runtime
    )

def calculate_system_health(data: Dict[str, Any]) -> SystemHealth:
    """Calculate system health metrics"""
    # Calculate error rate (errors per hour)
    error_rate = (data['errors'] / (data['uptime'] / 3600)) if data['uptime'] > 0 else 0
    
    # Convert uptime to hours
    uptime_hours = data['uptime'] / 3600
    
    # Get temperature trend from historical data
    temperature_trend = get_temperature_trend(data['temperature'])
    
    # Calculate overall health score (0-100)
    health_score = calculate_health_score(
        battery_voltage=data['batteryVoltage'],
        error_rate=error_rate,
        temperature=data['temperature']
    )
    
    return SystemHealth(
        error_rate=error_rate,
        uptime=uptime_hours,
        temperature_trend=temperature_trend,
        health_score=health_score
    )

def estimate_battery_capacity(voltage: float) -> float:
    """Estimate remaining battery capacity based on voltage"""
    # Simple linear approximation for Li-ion battery
    max_voltage = 4.2
    min_voltage = 3.2
    voltage_range = max_voltage - min_voltage
    
    if voltage >= max_voltage:
        return 2600  # Full capacity
    elif voltage <= min_voltage:
        return 0
    else:
        capacity_percentage = (voltage - min_voltage) / voltage_range
        return 2600 * capacity_percentage

def get_temperature_trend(current_temp: float) -> float:
    """Calculate temperature trend from historical data"""
    query = f"""
        SELECT temperature
        FROM `{PROJECT_ID}.{DATASET_ID}.flight1_telemetry`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
        ORDER BY timestamp DESC
        LIMIT 12
    """
    
    df = bq_client.query(query).to_dataframe()
    if len(df) < 2:
        return 0.0
        
    # Calculate rolling average slope
    temps = df['temperature'].values
    x = np.arange(len(temps))
    slope, _ = np.polyfit(x, temps, 1)
    
    return slope

def calculate_health_score(battery_voltage: float, error_rate: float, 
                         temperature: float) -> float:
    """Calculate overall system health score"""
    # Battery health (0-40 points)
    battery_score = 40 * (battery_voltage - 3.2) / (4.2 - 3.2)
    battery_score = max(0, min(40, battery_score))
    
    # Error rate health (0-40 points)
    error_score = 40 * np.exp(-error_rate)
    
    # Temperature health (0-20 points)
    temp_score = 20 * (1 - abs(temperature - 25) / 60)
    temp_score = max(0, min(20, temp_score))
    
    return battery_score + error_score + temp_score

def store_processed_data(data: Dict[str, Any]) -> None:
    """Store processed telemetry in BigQuery"""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.flight1_processed"
    
    errors = bq_client.insert_rows_json(table_id, [data])
    if errors:
        raise Exception(f"BigQuery insert errors: {errors}")

def store_analytics(data: Dict[str, Any]) -> None:
    """Store analytics data in Cloud Storage"""
    timestamp = datetime.now(timezone.utc)
    blob_name = (f"flight1/analytics/{timestamp.year}/{timestamp.month}/"
                f"{timestamp.day}/{data['event_id']}_analytics.json")
    
    bucket = storage_client.bucket(ANALYTICS_BUCKET)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(
        json.dumps(data),
        content_type='application/json'
    )

def generate_analytics(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate analytics data for visualization and analysis"""
    return {
        'timestamp': data['timestamp'],
        'event_id': data['event_id'],
        
        # Core metrics
        'health_score': data['health_score'],
        'power_efficiency': data['solar_efficiency'],
        'estimated_runtime': data['estimated_runtime'],
        
        # Derived metrics
        'metrics': {
            'power': {
                'efficiency': data['solar_efficiency'],
                'consumption': data['power_consumption'],
                'charging_rate': data['charging_rate'],
                'runtime_hours': data['estimated_runtime']
            },
            'health': {
                'score': data['health_score'],
                'error_rate': data['error_rate'],
                'uptime_hours': data['uptime'],
                'temperature_trend': data['temperature_trend']
            }
        },
        
        # Raw data reference
        'raw_metrics': data['raw_metrics']
    }
