#!/usr/bin/env python3
import yaml
import jsonschema
import sys

def load_schema():
    """Load configuration schema"""
    with open('config/schema.yml', 'r') as f:
        return yaml.safe_load(f)

def validate_config(config_path):
    """Validate configuration file"""
    schema = load_schema()
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    try:
        jsonschema.validate(config, schema)
        print(f"Configuration {config_path} is valid")
        return True
    except jsonschema.exceptions.ValidationError as e:
        print(f"Configuration error: {str(e)}")
        return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: validate.py <config_file>")
        sys.exit(1)
        
    if not validate_config(sys.argv[1]):
        sys.exit(1)
