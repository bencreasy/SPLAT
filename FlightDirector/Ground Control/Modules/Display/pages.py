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
