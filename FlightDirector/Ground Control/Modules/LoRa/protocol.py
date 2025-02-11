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
