class DataIndexer:
    """
    Manages data indexing for fast retrieval.
    Uses SQLite FTS for text search.
    """
    def __init__(self, connection):
        self.connection = connection
        self.indexed_fields = ['type', 'source', 'metadata']

    async def index_item(self, item_id: str, data: Dict[str, Any]):
        """Index an item for searching"""
        try:
            search_text = self._prepare_search_text(data)
            async with self.connection.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO search_index (item_id, search_text)
                    VALUES (?, ?)
                """, (item_id, search_text))
        except Exception as e:
            raise IndexError(f"Failed to index item: {str(e)}")

    async def search(self, query: str) -> List[str]:
        """Search indexed data"""
        async with self.connection.cursor() as cursor:
            results = await cursor.execute("""
                SELECT item_id FROM search_index
                WHERE search_text MATCH ?
                ORDER BY rank
            """, (query,))
            return [row[0] for row in results]
