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
