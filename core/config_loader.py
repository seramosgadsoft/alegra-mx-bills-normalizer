"""
Configuration loader for the Mexico Bills Normalization system.
"""
import json
import os
from typing import Dict, Any


class ConfigLoader:
    """Loads and manages application configuration."""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the config loader.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_alegra_config(self, country: str = "MX") -> Dict[str, Any]:
        """
        Get Alegra configuration for a specific country.
        
        Args:
            country: Country code (default: MX)
            
        Returns:
            Dictionary with Alegra configuration
        """
        return self.config.get("erp", {}).get("Alegra", {}).get(country, {})
    
    def get_invoice_analyzer_config(self) -> Dict[str, Any]:
        """
        Get Invoice Analyzer API configuration.
        
        Returns:
            Dictionary with Invoice Analyzer configuration
        """
        return self.config.get("adsoft_service", {})
    
    def get_tax_map(self, country: str = "MX") -> list:
        """
        Get tax mapping for a specific country.
        
        Args:
            country: Country code (default: MX)
            
        Returns:
            List of tax mappings
        """
        alegra_config = self.get_alegra_config(country)
        return alegra_config.get("tax_map", [])
    
    def get_error_mappings(self) -> Dict[str, Dict[str, str]]:
        """
        Get error message mappings.
        
        Returns:
            Dictionary of error mappings
        """
        return self.config.get("labels", {}).get("error_mappings", {})
    
    def get_full_config(self) -> Dict[str, Any]:
        """
        Get the complete configuration.
        
        Returns:
            Full configuration dictionary
        """
        return self.config
