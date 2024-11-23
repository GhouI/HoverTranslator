"""
Settings window implementation
"""
import customtkinter as ctk
import logging

logger = logging.getLogger(__name__)

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.app = parent  # Get the TranslatorApp instance
        self.title("Settings")
        self.geometry("400x300")
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # API Key
        self.api_key_label = ctk.CTkLabel(self, text="OpenAI API Key:")
        self.api_key_label.grid(row=0, column=0, pady=(20,0), padx=20, sticky="w")
        
        self.api_key_entry = ctk.CTkEntry(self, width=300, show="*")
        self.api_key_entry.grid(row=1, column=0, pady=(5,20), padx=20, sticky="ew")
        if self.app.api_key:
            self.api_key_entry.insert(0, self.app.api_key)
        
        # Show/Hide API Key
        self.show_key = ctk.CTkCheckBox(self, text="Show API Key", command=self.toggle_api_key_visibility)
        self.show_key.grid(row=2, column=0, pady=5, padx=20, sticky="w")
        
        # Model Selection (for future use)
        self.model_label = ctk.CTkLabel(self, text="Model:")
        self.model_label.grid(row=3, column=0, pady=(20,0), padx=20, sticky="w")
        
        self.model_var = ctk.StringVar(master=self, value="gpt-4o-mini")
        self.model_menu = ctk.CTkOptionMenu(
            self,
            values=["gpt-4o-mini"],  # Only one model for now
            variable=self.model_var,
            state="disabled"  # Disabled for now
        )
        self.model_menu.grid(row=4, column=0, pady=(5,20), padx=20, sticky="ew")
        
        # Save Button
        self.save_btn = ctk.CTkButton(self, text="Save Settings", command=self.save_settings)
        self.save_btn.grid(row=5, column=0, pady=20, padx=20, sticky="ew")
        
    def toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        if self.show_key.get():
            self.api_key_entry.configure(show="")
        else:
            self.api_key_entry.configure(show="*")
            
    def save_settings(self):
        """Save settings and validate API key"""
        api_key = self.api_key_entry.get().strip()
        
        if not api_key:
            self.show_error("API key is required")
            return
            
        # Save settings
        settings = {
            "api_key": api_key,
            "model": self.model_var.get()
        }
        
        try:
            # Save to file
            self.app.settings_manager.save_settings(settings)
            
            # Update app settings
            self.app.api_key = api_key
            self.app.setup_services()  # Reinitialize services with new API key
            
            # Close settings window
            self.destroy()
            
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            self.show_error(str(e))
            
    def show_error(self, message):
        """Show error message"""
        error_label = ctk.CTkLabel(
            self,
            text=f"Error: {message}",
            text_color="red"
        )
        error_label.grid(row=6, column=0, pady=10, padx=20)
