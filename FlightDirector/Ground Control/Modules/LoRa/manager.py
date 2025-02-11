@dataclass
class LoRaDevice:
    """Known device information"""
    node_id: str
    last_seen: datetime
    rssi_history: List[int]
    packet_count: int
    status: str
    config: dict

class DeviceManager:
    """
    Manages known LoRa devices and their state.
    Handles registration and tracking.
    """
    def __init__(self, config: dict, event_bus):
        self.config = config
        self.event_bus = event_bus
        self.devices = {}
        
    async def register_device(self, node_id: str, initial_data: dict):
        """Register new device or update existing"""
        if node_id in self.devices:
            await self._update_device(node_id, initial_data)
        else:
            await self._add_device(node_id, initial_data)
            
        # Notify system of new/updated device
        await self.event_bus.publish({
            'type': 'device_updated',
            'source': 'device_manager',
            'data': {
                'node_id': node_id,
                'status': self.devices[node_id].status
            }
        })
        
    async def _update_device(self, node_id: str, data: dict):
        """Update existing device information"""
        device = self.devices[node_id]
        device.last_seen = datetime.now()
        device.rssi_history.append(data.get('rssi', 0))
        device.packet_count += 1
        
        # Keep RSSI history manageable
        if len(device.rssi_history) > 100:
            device.rssi_history = device.rssi_history[-100:]
