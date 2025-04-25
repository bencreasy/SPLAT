import os
import sys
import time
import signal
import logging
import argparse

from eden_control.core.system_manager import SystemManager
from eden_control.core.event_bus import EventBus
from eden_control.core.config_manager import ConfigManager
from eden_control.communication.cloud_manager import CloudManager
from eden_control.ui.display_manager import DisplayManager
from eden_control.ui.dashboard import Dashboard
from eden_control.data.log_manager import LogManager

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Eden Control System")
    parser.add_argument("--config", default="config/default.yml", help="Path to configuration file")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Create config directory if it doesn't exist
    os.makedirs(os.path.dirname(args.config), exist_ok=True)
    
    # Basic logging setup (will be enhanced by LogManager)
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("Eden.Main")
    
    # Create event bus
    event_bus = EventBus()
    
    # Create config manager
    config_manager = ConfigManager(args.config)
    if not os.path.exists(args.config):
        # Create default config if not exists
        default_config = {
            "system": {
                "id": "eden-prototype",
                "name": "Eden Prototype",
                "version": "0.1.0"
            },
            "display": {
                "width": 800,
                "height": 480,
                "fps": 30
            },
            "cloud": {
                "api_url": "https://api.example.com/v1",
                "api_key": "your-api-key-here",
                "sync_interval": 60
            },
            "logging": {
                "directory": "logs",
                "level": "INFO",
                "max_size": 10485760,
                "backup_count": 5
            }
        }
        
        import yaml
        with open(args.config, 'w') as f:
            yaml.dump(default_config, f)
        logger.info(f"Created default configuration at {args.config}")
    
    # Load configuration
    config_manager.load()
    
    # Create system manager
    system_manager = SystemManager(args.config, event_bus)
    
    try:
        # Initialize components
        log_manager = LogManager(config_manager, event_bus)
        cloud_manager = CloudManager(config_manager, event_bus)
        display_manager = DisplayManager(config_manager, event_bus)
        dashboard = Dashboard(config_manager, event_bus)
        
        # Register components with system manager
        system_manager.register_component("event_bus", event_bus)
        system_manager.register_component("config_manager", config_manager)
        system_manager.register_component("log_manager", log_manager)
        system_manager.register_component("cloud_manager", cloud_manager)
        system_manager.register_component("display_manager", display_manager)
        
        # Set up display
        display_manager.register_view("dashboard", dashboard)
        display_manager.set_view("dashboard")
        
        # Set up signal handling
        def signal_handler(sig, frame):
            logger.info("Shutdown signal received")
            system_manager.stop()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
      
      # Start system
        event_bus.start()
        system_manager.start()
        
        # Start main loop
        logger.info("Eden Control System running - press Ctrl+C to exit")
        
        # Publish system online event
        event_bus.publish("system.status", {
            "status": "Online",
            "startup_time": time.time()
        })
        
        # Add an initial system message
        event_bus.publish("system.message", {
            "message": "System initialized successfully"
        })
        
        # Send cloud connected status after a brief delay
        time.sleep(2)
        event_bus.publish("cloud.status", {
            "status": "Connected",
            "timestamp": time.time()
        })
        
        # Main loop - keep running until terminated
        while True:
            # Publish heartbeat event periodically
            event_bus.publish("system.heartbeat", {
                "timestamp": time.time()
            })
            
            # Add periodic system messages for demonstration
            if int(time.time()) % 60 == 0:  # Once per minute
                event_bus.publish("system.message", {
                    "message": f"LaunchPad heartbeat received"
                })
            
            # Sleep to prevent CPU spinning
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
    finally:
        # Stop system
        system_manager.stop()
        
if __name__ == "__main__":
    main()
