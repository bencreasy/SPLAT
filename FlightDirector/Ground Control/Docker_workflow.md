# Ground Control Docker and GitHub Configuration

## Directory Structure
```
ground_control/
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   └── containers/
│       ├── base/
│       │   └── Dockerfile
│       ├── display/
│       │   └── Dockerfile
│       └── lora/
│           └── Dockerfile
│
└── .github/
    └── workflows/
        ├── test.yml
        ├── build.yml
        ├── release.yml
        └── deploy.yml
```

## Docker Configuration

### 1. Base Dockerfile (docker/containers/base/Dockerfile)
```dockerfile
# Use official Python image for ARM
FROM python:3.9-slim-bullseye

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    i2c-tools \
    spi-tools \
    && rm -rf /var/lib/apt/lists/*

# Create ground control user
RUN useradd -m -r -s /bin/bash ground_control

# Create necessary directories
RUN mkdir -p /opt/ground_control /data/ground_control /var/log/ground_control \
    && chown -R ground_control:ground_control \
        /opt/ground_control \
        /data/ground_control \
        /var/log/ground_control

# Set working directory
WORKDIR /opt/ground_control

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Switch to non-root user
USER ground_control

# Command to run
CMD ["python3", "-m", "ground_control"]
```

### 2. LoRa Container (docker/containers/lora/Dockerfile)
```dockerfile
FROM ground_control/base:latest

# Install LoRa dependencies
RUN apt-get update && apt-get install -y \
    spi-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy LoRa module code
COPY modules/lora /opt/ground_control/modules/lora

# Required for SPI access
VOLUME ["/dev/spidev0.0"]

# Module-specific command
CMD ["python3", "-m", "ground_control.modules.lora"]
```

### 3. Display Container (docker/containers/display/Dockerfile)
```dockerfile
FROM ground_control/base:latest

# Install display dependencies
RUN apt-get update && apt-get install -y \
    i2c-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy display module code
COPY modules/display /opt/ground_control/modules/display

# Required for I2C access
VOLUME ["/dev/i2c-1"]

# Module-specific command
CMD ["python3", "-m", "ground_control.modules.display"]
```

### 4. Docker Compose (docker/docker-compose.yml)
```yaml
version: '3.8'

services:
  core:
    build:
      context: .
      dockerfile: docker/containers/base/Dockerfile
    image: ground_control/core:${VERSION:-latest}
    restart: unless-stopped
    volumes:
      - ./config:/opt/ground_control/config
      - ./data:/data/ground_control
      - ./logs:/var/log/ground_control
    environment:
      - GC_ENV=${GC_ENV:-production}
    depends_on:
      - lora
      - display

  lora:
    build:
      context: .
      dockerfile: docker/containers/lora/Dockerfile
    image: ground_control/lora:${VERSION:-latest}
    restart: unless-stopped
    devices:
      - "/dev/spidev0.0:/dev/spidev0.0"
    privileged: true
    environment:
      - GC_ENV=${GC_ENV:-production}

  display:
    build:
      context: .
      dockerfile: docker/containers/display/Dockerfile
    image: ground_control/display:${VERSION:-latest}
    restart: unless-stopped
    devices:
      - "/dev/i2c-1:/dev/i2c-1"
    privileged: true
    environment:
      - GC_ENV=${GC_ENV:-production}
```

### 5. Development Compose (docker/docker-compose.dev.yml)
```yaml
version: '3.8'

services:
  core:
    build:
      context: .
      dockerfile: docker/containers/base/Dockerfile
    volumes:
      - .:/opt/ground_control
      - ./data:/data/ground_control
      - ./logs:/var/log/ground_control
    environment:
      - GC_ENV=development
      - PYTHONPATH=/opt/ground_control
    command: python3 -m debugpy --listen 0.0.0.0:5678 -m ground_control

  lora:
    build:
      context: .
      dockerfile: docker/containers/lora/Dockerfile
    volumes:
      - .:/opt/ground_control
    environment:
      - GC_ENV=development
      - PYTHONPATH=/opt/ground_control
    command: python3 -m debugpy --listen 0.0.0.0:5679 -m ground_control.modules.lora

  display:
    build:
      context: .
      dockerfile: docker/containers/display/Dockerfile
    volumes:
      - .:/opt/ground_control
    environment:
      - GC_ENV=development
      - PYTHONPATH=/opt/ground_control
    command: python3 -m debugpy --listen 0.0.0.0:5680 -m ground_control.modules.display
```

## GitHub Workflows

### 1. Test Workflow (.github/workflows/test.yml)
```yaml
name: Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run tests
      run: |
        pytest tests/ --cov=ground_control

    - name: Lint code
      run: |
        flake8 ground_control tests
        black --check ground_control tests

    - name: Type check
      run: |
        mypy ground_control
```

### 2. Build Workflow (.github/workflows/build.yml)
```yaml
name: Build

on:
  push:
    branches: [ main, develop ]
    tags: [ 'v*' ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2

    - name: Set up QEMU
      uses: docker/setup-qemu-action@v1

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v1

    - name: Login to GitHub Container Registry
      uses: docker/login-action@v1
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Build and push
      uses: docker/build-push-action@v2
      with:
        context: .
        platforms: linux/arm/v7,linux/arm64
        push: true
        tags: |
          ghcr.io/${{ github.repository }}/ground-control:latest
          ghcr.io/${{ github.repository }}/ground-control:${{ github.sha }}
```

### 3. Release Workflow (.github/workflows/release.yml)
```yaml
name: Release

on:
  push:
    tags: [ 'v*' ]

jobs:
  release:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2

    - name: Build release assets
      run: |
        make dist

    - name: Create Release
      id: create_release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: ${{ github.ref }}
        release_name: Release ${{ github.ref }}
        draft: false
        prerelease: false

    - name: Upload Release Assets
      uses: actions/upload-release-asset@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        upload_url: ${{ steps.create_release.outputs.upload_url }}
        asset_path: ./dist/ground-control.tar.gz
        asset_name: ground-control.tar.gz
        asset_content_type: application/gzip
```

### 4. Deploy Workflow (.github/workflows/deploy.yml)
```yaml
name: Deploy

on:
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        default: 'development'

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment || 'production' }}
    
    steps:
    - uses: actions/checkout@v2

    - name: Configure SSH
      uses: webfactory/ssh-agent@v0.5.3
      with:
        ssh-private-key: ${{ secrets.DEPLOY_KEY }}

    - name: Deploy to Device
      run: |
        ssh ${{ secrets.DEPLOY_HOST }} 'bash -s' << 'EOF'
          cd /opt/ground_control
          docker-compose pull
          docker-compose up -d
        EOF
```

## Usage Instructions

### Development Setup
```bash
# Start development environment
docker-compose -f docker/docker-compose.dev.yml up -d

# View logs
docker-compose -f docker/docker-compose.dev.yml logs -f

# Run tests
docker-compose -f docker/docker-compose.dev.yml exec core pytest

# Debug with VS Code
# Configure launch.json for remote debugging
```

### Production Deployment
```bash
# Build and start production containers
docker-compose -f docker/docker-compose.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Update to latest version
docker-compose pull
docker-compose up -d
```

## Key Features

1. Container Structure:
   - Modular design
   - Hardware access
   - Development support
   - Easy updates

2. Build Process:
   - Multi-arch support
   - Automated testing
   - Version control
   - Release management

3. Deployment:
   - Automated deployment
   - Environment management
   - Logging system
   - Debug support
