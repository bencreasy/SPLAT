from dataclasses import dataclass
import asyncio

@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int
    base_delay: float
    max_delay: float
    jitter: float

class RetryHandler:
    """
    Handles retry logic for failed operations.
    Implements exponential backoff.
    """
    def __init__(self, config: RetryConfig):
        self.config = config
        
    async def execute(self, operation, *args, **kwargs):
        """Execute operation with retry"""
        last_error = None
        
        for attempt in range(self.config.max_attempts):
            try:
                return await operation(*args, **kwargs)
                
            except Exception as e:
                last_error = e
                if not self._should_retry(e):
                    raise
                    
                delay = self._calculate_delay(attempt)
                await asyncio.sleep(delay)
                
        raise MaxRetriesError(f"Max retries exceeded: {str(last_error)}")
        
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff"""
        delay = min(
            self.config.base_delay * (2 ** attempt),
            self.config.max_delay
        )
        jitter = random.uniform(0, self.config.jitter)
        return delay + jitter
