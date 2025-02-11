# Ground Control Display Module

## Directory Structure
```
modules/display/
├── __init__.py
├── manager.py      # Display management
├── pages.py        # Display pages/screens
├── indicators.py   # LED indicators
├── hardware/       # Hardware interfaces
│   ├── __init__.py
│   ├── ssd1306.py # OLED display driver
│   ├── st7789.py  # LCD display driver
│   └── led.py     # LED controller
└── layouts/        # Screen layouts
    ├── __init__.py
    ├── status.py   # Status screens
    ├── debug.py    # Debug information
    └── alert.py    # Alert displays
```

## Core Components

### 1. Display Manager (manager.py)
```python
from typing import Optional, Dict, Any
from dataclasses import dataclass
import asyncio

@dataclass
class DisplayConfig:
    """Display configuration"""
    type: str           # 'oled', 'lcd', 'none'
    width: int
    height: int
    rotation: int = 0
    contrast: int = 255
    address: int = 0x3C  # I2C address
    brightness: int = 255

class DisplayManager:
    """
    Manages display hardware and content.
    Coordinates different display types and LED indicators.
    """
    def __init__(self, config: DisplayConfig, event_bus):
        self.config = config
        self.event_bus = event_bus
        self.current_page = None
        self.pages = {}
        self.display = None
        self.indicators = None
        self.update_lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize display hardware"""
        try:
            # Initialize main display
            if self.config.type == 'oled':
                from .hardware.ssd1306 import SSD1306
                self.display = SSD1306(self.config)
            elif self.config.type == 'lcd':
                from .hardware.st7789 import ST7789
                self.display = ST7789(self.config)
                
            # Initialize LED indicators
            from .hardware.led import LEDController
            self.indicators = LEDController()
            
            # Initialize default pages
            self._setup_pages()
            
            await self.display.initialize()
            await self.indicators.initialize()
            
        except Exception as e:
            raise DisplayError(f"Display initialization failed: {str(e)}")
            
    async def show_page(self, page_name: str, data: Optional[Dict] = None):
        """Switch to specified page"""
        async with self.update_lock:
            if page_name not in self.pages:
                raise ValueError(f"Unknown page: {page_name}")
                
            self.current_page = self.pages[page_name]
            await self._update_display(data)
            
    async def _update_display(self, data: Optional[Dict] = None):
        """Update display content"""
        if self.current_page and self.display:
            content = await self.current_page.render(data)
            await self.display.clear()
            await self.display.draw(content)
            await self.display.show()
```

### 2. Page Definitions (pages.py)
```python
class BasePage:
    """Base class for display pages"""
    def __init__(self, display_config: DisplayConfig):
        self.config = display_config
        self.width = display_config.width
        self.height = display_config.height
        
    async def render(self, data: Optional[Dict] = None) -> bytes:
        """Render page content"""
        raise NotImplementedError

class StatusPage(BasePage):
    """Main status display page"""
    async def render(self, data: Optional[Dict] = None) -> bytes:
        # Create status display
        canvas = self._create_canvas()
        
        # Draw status information
        await self._draw_header(canvas, data)
        await self._draw_metrics(canvas, data)
        await self._draw_alerts(canvas, data)
        
        return canvas.tobytes()
        
    async def _draw_header(self, canvas, data):
        """Draw header with basic info"""
        if data:
            # Draw time
            time_str = datetime.now().strftime("%H:%M:%S")
            canvas.text((2, 2), time_str, fill=1)
            
            # Draw node count
            nodes = data.get('node_count', 0)
            canvas.text((64, 2), f"Nodes: {nodes}", fill=1)

class DebugPage(BasePage):
    """System debugging information"""
    async def render(self, data: Optional[Dict] = None) -> bytes:
        canvas = self._create_canvas()
        
        if data:
            # System metrics
            memory = data.get('memory_used', 0)
            cpu = data.get('cpu_usage', 0)
            temp = data.get('temperature', 0)
            
            canvas.text((2, 2), f"Mem: {memory}%", fill=1)
            canvas.text((2, 12), f"CPU: {cpu}%", fill=1)
            canvas.text((2, 22), f"Temp: {temp}°C", fill=1)
            
        return canvas.tobytes()
```

### 3. LED Indicator Manager (indicators.py)
```python
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
```

### 4. Hardware Interface Example (hardware/ssd1306.py)
```python
from PIL import Image, ImageDraw
import adafruit_ssd1306

class SSD1306:
    """
    Driver for SSD1306 OLED display.
    Handles low-level display operations.
    """
    def __init__(self, config: DisplayConfig):
        self.config = config
        self.display = None
        self.image = None
        self.draw = None
        
    async def initialize(self):
        """Initialize display"""
        import board
        i2c = board.I2C()
        
        self.display = adafruit_ssd1306.SSD1306_I2C(
            self.config.width,
            self.config.height,
            i2c,
            addr=self.config.address
        )
        
        # Create image buffer
        self.image = Image.new('1', (self.config.width, self.config.height))
        self.draw = ImageDraw.Draw(self.image)
        
        # Initial setup
        await self.clear()
        await self.set_contrast(self.config.contrast)
        
    async def clear(self):
        """Clear display"""
        self.draw.rectangle(
            (0, 0, self.config.width, self.config.height),
            fill=0
        )
        
    async def draw(self, content: bytes):
        """Draw content to display"""
        self.image = Image.frombytes(
            '1',
            (self.config.width, self.config.height),
            content
        )
        
    async def show(self):
        """Update display with current buffer"""
        self.display.image(self.image)
        self.display.show()
```

## Usage Example

```python
# Example display usage
async def main():
    # Initialize display
    config = DisplayConfig(
        type='oled',
        width=128,
        height=64,
        rotation=0
    )
    
    display = DisplayManager(config, event_bus)
    await display.initialize()
    
    # Show status page
    status_data = {
        'node_count': 5,
        'memory_used': 45,
        'cpu_usage': 12,
        'temperature': 38
    }
    
    await display.show_page('status', status_data)
    
    # Set LED indicators
    await display.indicators.set_indicator('power', LEDState.ON)
    await display.indicators.set_indicator('radio', LEDState.BLINK_SLOW)
```

## Key Features

1. Display Management:
   - Multiple display types
   - Page system
   - LED indicators
   - Status feedback

2. Information Organization:
   - Clear layouts
   - Priority information
   - Easy navigation
   - Visual alerts

3. Hardware Support:
   - Different displays
   - LED indicators
   - I2C/SPI interfaces
   - Power management

4. User Interface:
   - Status updates
   - System metrics
   - Alert display
   - Debug information
