# Ground Control LoRa Module

## Directory Structure
```
modules/lora/
├── __init__.py
├── handler.py      # Main LoRa handling
├── decoder.py      # Packet processing
├── manager.py      # Device management
├── protocol.py     # Protocol definitions
└── hardware/       # Hardware interfaces
    ├── __init__.py
    ├── rak2287.py  # RAK2287 specific
    └── spi.py      # SPI communication
```

## Core Components

### 1. LoRa Handler (handler.py)
```python
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class LoRaPacket:
    """Raw LoRa packet structure"""
    data: bytes
    rssi: int
    snr: float
    frequency: float
    sf: int          # Spreading Factor
    timestamp: datetime
    error_check: bool

class LoRaHandler:
    """
    Main LoRa communication handler.
    Manages radio operations and packet processing.
    """
    def __init__(self, config: dict, event_bus):
        self.config = config
        self.event_bus = event_bus
        self.devices = {}  # Known devices
        self.running = False
        
        # Initialize hardware
        self.radio = self._setup_radio()
        
    async def start(self):
        """Start LoRa operations"""
        self.running = True
        await self._init_radio()
        await self._start_receive_loop()
        
    async def stop(self):
        """Stop LoRa operations"""
        self.running = False
        await self._cleanup_radio()
        
    async def _receive_loop(self):
        """Main receive loop"""
        while self.running:
            try:
                packet = await self.radio.receive_packet()
                if packet:
                    await self._handle_packet(packet)
            except Exception as e:
                await self._handle_error(e)
                await asyncio.sleep(1)  # Prevent tight loop on error
                
    async def _handle_packet(self, raw_packet: LoRaPacket):
        """Process received packet"""
        try:
            # Decode packet
            packet = await self.decoder.decode(raw_packet)
            
            # Validate packet
            if not self._validate_packet(packet):
                return
                
            # Process based on type
            if packet.type == 'registration':
                await self._handle_registration(packet)
            elif packet.type == 'data':
                await self._handle_data(packet)
            elif packet.type == 'alert':
                await self._handle_alert(packet)
                
            # Publish packet event
            await self.event_bus.publish({
                'type': 'lora_packet_received',
                'source': 'lora_handler',
                'data': packet.to_dict()
            })
            
        except Exception as e:
            await self._handle_error(e)
```

### 2. Packet Decoder (decoder.py)
```python
class PacketDecoder:
    """
    Handles packet decoding and validation.
    Supports multiple packet formats.
    """
    def __init__(self):
        self.protocols = {
            0x01: self._decode_v1,
            0x02: self._decode_v2
        }
        
    async def decode(self, raw_packet: LoRaPacket) -> dict:
        """Decode raw packet into structured data"""
        try:
            # Extract protocol version
            protocol = raw_packet.data[0]
            
            # Find appropriate decoder
            if protocol in self.protocols:
                decoder = self.protocols[protocol]
                return await decoder(raw_packet.data[1:])
            else:
                raise ValueError(f"Unknown protocol: {protocol}")
                
        except Exception as e:
            raise PacketDecodeError(f"Failed to decode: {str(e)}")
            
    async def _decode_v1(self, data: bytes) -> dict:
        """
        Decode version 1 packet format:
        [protocol][node_id][type][payload][checksum]
        """
        try:
            # Extract fields
            node_id = data[0:4]
            packet_type = data[4]
            payload = data[5:-2]
            checksum = data[-2:]
            
            # Verify checksum
            if not self._verify_checksum(data[:-2], checksum):
                raise ChecksumError("Invalid checksum")
                
            return {
                'node_id': node_id.hex(),
                'type': packet_type,
                'payload': payload
            }
            
        except Exception as e:
            raise PacketDecodeError(f"V1 decode failed: {str(e)}")
```

### 3. Device Manager (manager.py)
```python
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
```

### 4. Protocol Definitions (protocol.py)
```python
from enum import IntEnum

class PacketType(IntEnum):
    """Packet type definitions"""
    REGISTRATION = 0x01
    DATA = 0x02
    ALERT = 0x03
    CONFIG = 0x04
    ACK = 0x05

class PacketPriority(IntEnum):
    """Packet priority levels"""
    LOW = 0x01
    NORMAL = 0x02
    HIGH = 0x03
    CRITICAL = 0x04

class PacketFormat:
    """Packet format definitions"""
    HEADER_SIZE = 6
    MAX_PAYLOAD = 222  # 255 - HEADER_SIZE - FOOTER_SIZE
    FOOTER_SIZE = 2    # Checksum
    
    @staticmethod
    def create_packet(type: PacketType, node_id: bytes, 
                     payload: bytes, priority: PacketPriority) -> bytes:
        """Create properly formatted packet"""
        if len(payload) > PacketFormat.MAX_PAYLOAD:
            raise ValueError("Payload too large")
            
        packet = bytearray()
        packet.extend(node_id)
        packet.append(type)
        packet.append(priority)
        packet.extend(payload)
        checksum = PacketFormat.calculate_checksum(packet)
        packet.extend(checksum)
        
        return bytes(packet)
```

## Usage Example

```python
# Example of LoRa module usage
async def main():
    # Initialize LoRa module
    config = {
        'frequency': 915.0,
        'bandwidth': 125000,
        'coding_rate': 5,
        'spreading_factor': 7
    }
    
    lora_handler = LoRaHandler(config, event_bus)
    
    # Subscribe to packet events
    event_bus.subscribe('lora_packet_received', handle_packet)
    
    # Start LoRa operations
    await lora_handler.start()
    
    # Example packet handling
    async def handle_packet(event):
        packet = event['data']
        if packet['type'] == PacketType.DATA:
            # Process data packet
            await process_sensor_data(packet)
        elif packet['type'] == PacketType.ALERT:
            # Handle alert
            await handle_alert(packet)
```

## Key Features

1. Robust Packet Handling:
   - Error checking
   - Multiple protocols
   - Priority levels
   - Efficient processing

2. Device Management:
   - Auto registration
   - Status tracking
   - Performance monitoring
   - Configuration management

3. Error Recovery:
   - Hardware failures
   - Packet corruption
   - Connection issues
   - Device problems

4. Performance Optimization:
   - Efficient processing
   - Memory management
   - Battery consideration
   - Bandwidth optimization
