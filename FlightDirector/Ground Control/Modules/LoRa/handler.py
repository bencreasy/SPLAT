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
