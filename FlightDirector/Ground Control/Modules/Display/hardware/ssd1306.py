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
