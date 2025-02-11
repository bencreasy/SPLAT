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
