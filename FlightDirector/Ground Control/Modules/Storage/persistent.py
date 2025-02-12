import sqlite3
from pathlib import Path

class DataStore:
    """
    Manages persistent storage using SQLite.
    Handles data organization and retrieval.
    """
    def __init__(self, config: dict):
        self.db_path = Path(config['storage_path']) / 'data.db'
        self.max_size = config['max_storage_gb'] * 1024 * 1024 * 1024
        self.connection = None
        self.ensure_directory()

    async def initialize(self):
        """Set up database structure"""
        self.connection = await self._get_connection()
        await self._create_tables()

    async def store(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Store data with metadata"""
        try:
            # Compress if needed
            if data.get('compress', False):
                data = await self._compress_data(data)

            # Store with metadata
            async with self.connection.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO data (timestamp, type, priority, data, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    metadata['timestamp'],
                    metadata['type'],
                    metadata['priority'],
                    data,
                    json.dumps(metadata)
                ))
                return cursor.lastrowid

        except Exception as e:
            raise StorageError(f"Failed to store data: {str(e)}")

    async def query(self, criteria: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """Query data based on criteria"""
        query = """
            SELECT * FROM data WHERE 1=1
        """
        params = []

        # Build query based on criteria
        if 'start_time' in criteria:
            query += " AND timestamp >= ?"
            params.append(criteria['start_time'])
        if 'end_time' in criteria:
            query += " AND timestamp <= ?"
            params.append(criteria['end_time'])
        if 'type' in criteria:
            query += " AND type = ?"
            params.append(criteria['type'])
        if 'priority' in criteria:
            query += " AND priority >= ?"
            params.append(criteria['priority'])

        async with self.connection.cursor() as cursor:
            async for row in cursor.execute(query, params):
                yield self._row_to_dict(row)
