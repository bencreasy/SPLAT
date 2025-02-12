# SPLAT Flight Director - Path to Flight 1 🚀

## Hardware Requirements

### Ground Control Station v0.1
```yaml
Core Hardware:
  Computer:
    - Raspberry Pi 4B (4GB minimum)
    - 32GB High-endurance SD card
    - 5V/3A USB-C power supply
    - Cooling case or heatsinks
    - Optional: UPS HAT for power monitoring

  LoRa Hardware:
    - RAK2287 Concentrator
    - LoRa antenna (915 MHz)
    - Pigtail cables
    - Outdoor antenna housing (if external)
    - Lightning protection (if external)

  Storage:
    - 256GB SSD (recommended)
    - USB 3.0 enclosure
    - Optional: RAID1 setup for redundancy

  Monitoring:
    - BME280 sensor (temperature/humidity)
    - Optional: SSD1306 OLED display
    - Status LEDs
```

### Test Node (SPLAT Hopper)
```yaml
Test Hardware:
  - ESP32-WROOM-32
  - RFM95W LoRa module
  - 18650 battery + holder
  - Solar charging module
  - Basic sensors package
  - Weatherproof enclosure
```

## Directory Setup

1. Create Base Directory Structure:
```bash
# Create main directories
sudo mkdir -p /opt/splat
cd /opt/splat

# Create subdirectories
for dir in flight-director ground-control data config logs keys backups monitoring; do
    sudo mkdir -p $dir
done

# Set permissions
sudo chown -R splat:splat /opt/splat
sudo chmod 755 /opt/splat
sudo chmod 700 /opt/splat/keys
```

2. Initialize Flight Director:
```bash
cd /opt/splat/flight-director

# Create application directories
for dir in src ansible config scripts tests; do
    mkdir -p $dir
done

# Copy repository files
cp -r /path/to/repo/src/* src/
cp -r /path/to/repo/ansible/* ansible/
cp -r /path/to/repo/config/* config/
cp -r /path/to/repo/scripts/* scripts/
cp -r /path/to/repo/tests/* tests/
```

## Remaining Development Tasks

### 1. Core Components
```yaml
Required Development:
  Ground Control Interface:
    - Implement LoRa packet handler
    - Add basic data validation
    - Create local storage manager
    - Setup monitoring service
    
  LaunchPad Integration:
    - Complete GCP project setup
    - Implement cloud sync
    - Add error handling
    - Create backup system
    
  Security Implementation:
    - Generate production keys
    - Implement encryption
    - Setup secure communication
    - Configure firewalls
```

### 2. Testing Framework
```yaml
Test Development:
  Unit Tests:
    - Complete core module tests
    - Add deployment tests
    - Create security tests
    - Implement validation tests
    
  Integration Tests:
    - Setup test environment
    - Create test scenarios
    - Add performance tests
    - Implement stress tests
```

### 3. Documentation
```yaml
Documentation Needs:
  - Installation guide
  - Configuration manual
  - API documentation
  - Testing procedures
  - Troubleshooting guide
```

## Flight 1 Test Campaign

### Test Setup
```yaml
Environment:
  Location: Test Field Site
  Duration: 72 hours
  Nodes: 2 SPLAT Hoppers
  Ground Control: 1 station

Monitoring:
  - System stability
  - Communication reliability
  - Power consumption
  - Data integrity
  - Environmental factors
```

### Test Sequence

1. Pre-deployment (24 hours):
```bash
# System setup
./scripts/install.sh --env test
./scripts/generate_keys.sh flight1

# Configuration
./scripts/configure.sh -s gc-test-01 --template flight1
./scripts/deploy.sh -e test -s gc-test-01
```

2. Deployment (72 hours):
```yaml
Steps:
  - Ground Control deployment
  - Node activation
  - System verification
  - Data collection start
  - Regular health checks
```

3. Monitoring:
```yaml
Metrics:
  System:
    - CPU usage
    - Memory usage
    - Storage usage
    - Temperature
    
  Communication:
    - Packet success rate
    - Signal strength
    - Error rates
    - Latency
    
  Data:
    - Collection rate
    - Processing time
    - Storage efficiency
    - Upload reliability
```

## Success Criteria

### Minimum Requirements
```yaml
System Performance:
  - 95% uptime
  - <1% packet loss
  - <500ms latency
  - Zero data loss

Data Collection:
  - Consistent sampling
  - Accurate timestamps
  - Complete metadata
  - Proper storage

Security:
  - Secure communication
  - Key management
  - Access control
  - Audit logging
```

## Next Steps

1. Hardware Procurement:
- Order Raspberry Pi and components
- Assemble Ground Control station
- Build test nodes
- Test hardware components

2. Environment Setup:
- Configure development environment
- Setup test environment
- Prepare deployment tools
- Create monitoring system

3. Initial Testing:
- Component testing
- System integration
- Performance verification
- Security validation

4. Documentation:
- Update installation guide
- Create test procedures
- Document configurations
- Prepare training materials

## Timeline

```yaml
Week 1:
  - Hardware procurement
  - Development environment setup
  - Initial component testing

Week 2:
  - Ground Control assembly
  - Software deployment
  - Integration testing
  - Security implementation

Week 3:
  - Test node preparation
  - System integration
  - Field site setup
  - Pre-deployment testing

Week 4:
  - Flight 1 deployment
  - 72-hour test campaign
  - Data analysis
  - Results documentation
```

Remember:
- Keep detailed logs of all setup procedures
- Document any deviations from plans
- Monitor all system metrics
- Maintain backup of all data
- Regular status updates
- Security first approach

This initial test campaign will provide valuable data for future development and deployment optimization.
