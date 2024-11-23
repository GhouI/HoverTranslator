"""
Settings management utility
"""
import json
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class SettingsManager:
    def __init__(self, settings_file="settings.json"):
        self.settings_file = settings_file
        # Load environment variables from .env file
        load_dotenv()
        
    def load_settings(self):
        """Load settings from file and environment"""
        settings = {}
        try:
            # Load from settings file if it exists
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r") as f:
                    settings = json.load(f)
            
            # Check for API key in environment variables
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("api_key")
            if api_key and not settings.get("api_key"):
                settings["api_key"] = api_key
                
            return settings
            
        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")
            return settings
            
    def save_settings(self, settings):
        """Save settings to file"""
        try:
            with open(self.settings_file, "w") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            raise
