from enum import Enum

class LEDState(Enum):
    OFF = 0
    ON = 1
    BLINK_SLOW = 2
    BLINK_FAST = 3
    PULSE = 4

class LEDIndicators:
    """
    Manages LED status indicators.
    Provides visual system status.
    """
    def __init__(self):
        self.leds = {
            'power': {'pin': 17, 'state': LEDState.OFF},
            'radio': {'pin': 27, 'state': LEDState.OFF},
            'cloud': {'pin': 22, 'state': LEDState.OFF},
            'alert': {'pin': 23, 'state': LEDState.OFF}
        }
        self.blink_tasks = {}
        
    async def set_indicator(self, name: str, state: LEDState):
        """Set LED state"""
        if name not in self.leds:
            raise ValueError(f"Unknown LED: {name}")
            
        led = self.leds[name]
        led['state'] = state
        
        # Cancel existing blink task
        if name in self.blink_tasks:
            self.blink_tasks[name].cancel()
            
        # Handle different states
        if state == LEDState.ON:
            await self._set_led(led['pin'], True)
        elif state == LEDState.OFF:
            await self._set_led(led['pin'], False)
        elif state in [LEDState.BLINK_SLOW, LEDState.BLINK_FAST]:
            interval = 1.0 if state == LEDState.BLINK_SLOW else 0.2
            self.blink_tasks[name] = asyncio.create_task(
                self._blink_led(led['pin'], interval)
            )
