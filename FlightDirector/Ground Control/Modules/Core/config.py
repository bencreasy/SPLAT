class ConfigManager:
    """
    Handles all configuration loading and access.
    Single source of truth for system settings.
    """
    def __init__(self):
        self.config = {}
        self.secrets = {}
        self.module_configs = {}
        
    async def load(self):
        """Load all configuration files"""
        # Load main config
        self.config = await self.load_yaml('config/default.yml')
        
        # Load module configs
        self.module_configs = await self.load_yaml('config/modules.yml')
        
        # Load secrets (encrypted)
        self.secrets = await self.load_secrets('config/secrets.yml.enc')
        
    def get_module_config(self, module_name: str) -> dict:
        """Get configuration for specific module"""
        return self.module_configs.get(module_name, {})
        
    def get_secret(self, key: str) -> str:
        """Safely retrieve encrypted secrets"""
        if key not in self.secrets:
            raise ConfigError(f"Secret {key} not found")
        return self.secrets[key]
