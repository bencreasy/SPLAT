# Eden Control System

A control system for the Eden hydroponic cabinet, based on the SPLAT architecture.

## Overview

The Eden Control System provides a framework for monitoring and controlling hydroponic systems. This prototype implementation connects to the LaunchPad cloud system and provides basic status display.

## Directory Structure
eden_control/
  init.py             # Package initialization
  main.py                 # Main application entry point
  core/                   # Core system components
    init.py
    system_manager.py   # System coordination
    event_bus.py        # Event distribution system
    config_manager.py   # Configuration handling
    error_handler.py    # Error management

  communication/          # Communication components
    init.py
    cloud_manager.py    # LaunchPad cloud integration

  ui/                     # User interface components
    init.py
    display_manager.py  # Display initialization and management
    dashboard.py        # Main dashboard view

  data/                   # Data management components
    init.py
    log_manager.py      # Logging system

  hardware/               # Hardware control (stubbed)
    init.py
    relay_controller.py # Relay control interface
    ensor_manager.py   # Sensor management

   modules/                # Subsystem modules (future)
    init.py
    water_module.py     # Water management (stub)  
    light_module.py     # Lighting control (stub)
    nutrient_module.py  # Nutrient control (stub)
config/  
  default.yml             # Default configuration file
logs/                       # Log directory
  eden.log                # System log file
scripts/
  install.sh              # Installation script
  update.sh               # Update script

## Features

- System monitoring and control
- Touchscreen interface
- Cloud connectivity
- Event-driven architecture
- Extensible component system

## Installation

1. Clone the repository
2. Run the installation script as root:
sudo ./install.sh
3. The system will start automatically and run as a service

## Development

To set up a development environment:

1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

2. Install dependencies
pip install -r requirements.txt

3. Run the system in development mode
python -m eden_control.main --debug

## Architecture

The Eden Control System is based on a modular, event-driven architecture:

- **Core**: System management, configuration, and event handling
- **Communication**: Cloud connectivity and data synchronization
- **UI**: Touchscreen interface and dashboard display
- **Data**: Logging and data management
- **Hardware**: (Stubbed for future development) Relay control, sensor reading, etc.

## Configuration

System configuration is stored in YAML files. The default configuration is created at `config/default.yml` on first run, or can be specified with the `--config` option.

## Cloud Integration

The system connects to the LaunchPad cloud platform for remote monitoring and control. Configuration for the cloud connection is stored in the configuration file.
