sudo apt update
sudo apt upgrade -y

# Enable SPI interface
sudo raspi-config
# Navigate to "Interface Options" -> "SPI" -> Enable

# Install packages needed for the display
sudo apt install -y python3-pip python3-pil python3-numpy
sudo pip3 install RPi.GPIO spidev

# Create a new virtual environment directory
mkdir -p /opt/eden/venv

# Install virtualenv if not already installed
sudo apt install -y python3-virtualenv

# Create the virtual environment
python3 -m virtualenv /opt/eden/venv


# Install RPi.GPIO if not already installed
sudo apt install -y python3-rpi.gpio

# Create a simple test script
cat > ~/test_relay.py << 'EOL'
import RPi.GPIO as GPIO
import time

# Set up GPIO using BCM numbering
GPIO.setmode(GPIO.BCM)

# Define relay pins
relay_pins = [5, 6, 13, 16, 19, 20, 21, 26]

# Set up all pins as outputs
for pin in relay_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)  # Start with relays off

try:
    # Test each relay
    for pin in relay_pins:
        print(f"Testing relay on GPIO {pin}")
        GPIO.output(pin, GPIO.HIGH)  # Turn on
        time.sleep(1)
        GPIO.output(pin, GPIO.LOW)   # Turn off
        time.sleep(0.5)
    
    print("All relays tested")
    
except KeyboardInterrupt:
    print("Test interrupted")
finally:
    GPIO.cleanup()  # Clean up GPIO on exit
EOL

# Run the test
sudo python3 ~/test_relay.py
