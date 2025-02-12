import lz4.frame
import json

class CompressionManager:
    """
    Handles data compression and decompression.
    Optimizes storage space.
    """
    def __init__(self, config: dict):
        self.compression_level = config.get('compression_level', 0)
        self.min_size = config.get('min_compress_size', 1024)

    async def should_compress(self, data: bytes) -> bool:
        """Determine if data should be compressed"""
        return len(data) > self.min_size

    async def compress(self, data: Dict[str, Any]) -> bytes:
        """Compress data with metadata"""
        try:
            json_data = json.dumps(data)
            if not await self.should_compress(json_data.encode()):
                return json_data.encode()

            compressed = lz4.frame.compress(
                json_data.encode(),
                compression_level=self.compression_level
            )
            return compressed
        except Exception as e:
            raise CompressionError(f"Compression failed: {str(e)}")

    async def decompress(self, data: bytes) -> Dict[str, Any]:
        """Decompress data and restore structure"""
        try:
            # Check if data is compressed
            if data.startswith(b'\x04\x22\x4D\x18'):  # LZ4 frame magic number
                decompressed = lz4.frame.decompress(data)
                return json.loads(decompressed)
            return json.loads(data)
        except Exception as e:
            raise CompressionError(f"Decompression failed: {str(e)}")
