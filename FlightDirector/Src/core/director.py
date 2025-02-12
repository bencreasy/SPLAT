# src/core/director.py

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

from .events import EventBus, Event, EventType, setup_event_logging

class FlightDirector:
    """
    Core class for managing SPLAT deployments and ground control stations
    """
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        setup_event_logging(self.config.get('log_level', 'INFO'))
        
        self.logger = logging.getLogger('FlightDirector.Core')
        self.event_bus = EventBus()
        self.stations: Dict[str, Dict[str, Any]] = {}
        self.deployments: Dict[str, Dict[str, Any]] = {}
        self._running = False
        
        # Initialize subsystems
        self.deployment_lock = asyncio.Lock()
        self._setup_event_handlers()

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_event_handlers(self) -> None:
        """Setup internal event handlers"""
        self.event_bus.subscribe(EventType.STATION_REGISTERED, self._handle_station_registered)
        self.event_bus.subscribe(EventType.DEPLOYMENT_COMPLETE, self._handle_deployment_complete)
        self.event_bus.subscribe(EventType.SYSTEM_ERROR, self._handle_system_error)

    async def start(self) -> None:
        """Start Flight Director services"""
        if self._running:
            return
            
        self._running = True
        self.logger.info("Starting Flight Director")
        
        # Start event bus
        asyncio.create_task(self.event_bus.start())
        
        # Start monitoring task
        asyncio.create_task(self._monitor_deployments())
        
        await self.event_bus.publish(Event(
            type=EventType.SYSTEM_ERROR,
            source="FlightDirector",
            data={"message": "Flight Director started"}
        ))

    async def stop(self) -> None:
        """Stop Flight Director services"""
        if not self._running:
            return
            
        self._running = False
        self.logger.info("Stopping Flight Director")
        
        # Stop event bus
        await self.event_bus.stop()
        
        await self.event_bus.publish(Event(
            type=EventType.SYSTEM_ERROR,
            source="FlightDirector",
            data={"message": "Flight Director stopped"}
        ))

    async def register_station(self, station_config: Dict[str, Any]) -> str:
        """Register a new ground control station"""
        station_id = station_config.get('station_id', f"gc-{len(self.stations) + 1}")
        
        self.stations[station_id] = {
            **station_config,
            'registered_at': datetime.utcnow(),
            'status': 'registered'
        }
        
        await self.event_bus.publish(Event(
            type=EventType.STATION_REGISTERED,
            source="FlightDirector",
            data={
                'station_id': station_id,
                'config': station_config
            }
        ))
        
        self.logger.info(f"Registered new station: {station_id}")
        return station_id

    async def deploy_station(self, station_id: str) -> bool:
        """Deploy a ground control station"""
        if station_id not in self.stations:
            self.logger.error(f"Station {station_id} not found")
            return False
            
        async with self.deployment_lock:
            try:
                deployment_id = f"deploy-{station_id}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
                
                self.deployments[deployment_id] = {
                    'station_id': station_id,
                    'status': 'in_progress',
                    'started_at': datetime.utcnow()
                }
                
                await self.event_bus.publish(Event(
                    type=EventType.DEPLOYMENT_STARTED,
                    source="FlightDirector",
                    data={
                        'deployment_id': deployment_id,
                        'station_id': station_id
                    }
                ))
                
                # TODO: Implement actual deployment logic
                # This will be integrated with Ansible deployment
                success = True
                
                if success:
                    self.deployments[deployment_id]['status'] = 'complete'
                    self.deployments[deployment_id]['completed_at'] = datetime.utcnow()
                    
                    await self.event_bus.publish(Event(
                        type=EventType.DEPLOYMENT_COMPLETE,
                        source="FlightDirector",
                        data={
                            'deployment_id': deployment_id,
                            'station_id': station_id
                        }
                    ))
                    
                    self.logger.info(f"Deployment complete: {deployment_id}")
                    return True
                else:
                    self.deployments[deployment_id]['status'] = 'failed'
                    await self.event_bus.publish(Event(
                        type=EventType.DEPLOYMENT_FAILED,
                        source="FlightDirector",
                        data={
                            'deployment_id': deployment_id,
                            'station_id': station_id,
                            'error': 'Deployment failed'
                        }
                    ))
                    return False
                    
            except Exception as e:
                self.logger.error(f"Error deploying station {station_id}: {str(e)}")
                await self.event_bus.publish(Event(
                    type=EventType.SYSTEM_ERROR,
                    source="FlightDirector",
                    data={
                        'message': f"Deployment error: {str(e)}",
                        'station_id': station_id
                    }
                ))
                return False

    async def get_station_status(self, station_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a ground control station"""
        if station_id not in self.stations:
            return None
        return self.stations[station_id]

    async def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific deployment"""
        if deployment_id not in self.deployments:
            return None
        return self.deployments[deployment_id]

    async def _monitor_deployments(self) -> None:
        """Monitor active deployments"""
        while self._running:
            try:
                for deployment_id, deployment in self.deployments.items():
                    if deployment['status'] == 'in_progress':
                        # TODO: Implement deployment monitoring logic
                        pass
                        
                await asyncio.sleep(self.config.get('monitoring_interval', 60))
            except Exception as e:
                self.logger.error(f"Error monitoring deployments: {str(e)}")

    async def _handle_station_registered(self, event: Event) -> None:
        """Handle station registration events"""
        station_id = event.data['station_id']
        self.logger.info(f"Processing registration for station: {station_id}")

    async def _handle_deployment_complete(self, event: Event) -> None:
        """Handle deployment completion events"""
        deployment_id = event.data['deployment_id']
        station_id = event.data['station_id']
        self.logger.info(f"Processing deployment completion: {deployment_id}")
        
        if station_id in self.stations:
            self.stations[station_id]['status']
