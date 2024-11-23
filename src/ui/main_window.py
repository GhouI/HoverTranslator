"""
Main application window implementation
"""
import customtkinter as ctk
from services.translation_service import TranslationService
from services.ocr_service import OCRService
from utils.settings_manager import SettingsManager
from ui.settings_window import SettingsWindow
from ui.capture_window import CaptureWindow
import logging

logger = logging.getLogger(__name__)

class TranslatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize settings
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load_settings()
        self.api_key = self.settings.get("api_key")
        self.capture_window = None
        
        # Initialize language variables
        self.source_lang_var = ctk.StringVar(value="Japanese")
        self.target_lang_var = ctk.StringVar(value="English")
        
        # Setup window properties
        self.title("Screen Translator")
        self.geometry("400x600")
        
        # Initialize UI
        self.setup_ui()
        
        # Initialize services if API key is present
        if self.check_api_key():
            self.setup_services()
        else:
            self.disable_ui()
            self.show_api_key_error()
            
    def check_api_key(self):
        """Check if API key is present and valid"""
        return bool(self.api_key)
        
    def setup_services(self):
        """Initialize OCR and translation services"""
        try:
            self.ocr_service = OCRService()
            
            if not self.api_key:
                logger.warning("No API key found in settings")
                self.show_api_key_error()
                return
                
            self.translation_service = TranslationService(self.api_key)
            logger.info("Services initialized successfully")
            
            # Enable UI elements
            self.enable_ui()
            
        except Exception as e:
            logger.error(f"Error initializing services: {str(e)}")
            self.show_error_message(str(e))
            
    def enable_ui(self):
        """Enable UI elements after successful API key validation"""
        self.source_lang_combo.configure(state="normal")
        self.target_lang_combo.configure(state="normal")
        self.translate_btn.configure(state="normal")
        self.context_text.configure(state="normal")
        self.show_capture_btn.configure(state="normal")
        
    def disable_ui(self):
        """Disable UI elements when API key is invalid"""
        self.source_lang_combo.configure(state="disabled")
        self.target_lang_combo.configure(state="disabled")
        self.translate_btn.configure(state="disabled")
        self.context_text.configure(state="disabled")
        self.show_capture_btn.configure(state="disabled")
    
    def setup_ui(self):
        """Setup the main window UI components"""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        self.setup_menu_frame()
        self.setup_language_selection()
        self.setup_context_frame()
        self.setup_translation_frame()
        self.setup_status_label()
    
    def setup_menu_frame(self):
        """Setup the menu frame with settings and capture buttons"""
        self.menu_frame = ctk.CTkFrame(self)
        self.menu_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.menu_frame.grid_columnconfigure(1, weight=1)
        
        self.settings_btn = ctk.CTkButton(
            self.menu_frame,
            text="⚙️ Settings",
            command=self.open_settings,
            width=100
        )
        self.settings_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.show_capture_btn = ctk.CTkButton(
            self.menu_frame,
            text="📷 Show Capture",
            command=self.show_capture_window,
            width=100,
            state="disabled"
        )
        self.show_capture_btn.grid(row=0, column=1, padx=5, pady=5)
    
    def setup_language_selection(self):
        """Setup language selection dropdowns"""
        # Source language
        self.source_lang_label = ctk.CTkLabel(self, text="Source Language:")
        self.source_lang_label.grid(row=2, column=0, pady=(10,0), padx=10, sticky="w")
        
        self.source_lang_combo = ctk.CTkOptionMenu(
            self,
            values=['English', 'Japanese', 'Korean', 'Chinese (Simplified)', 'Chinese (Traditional)'],
            variable=self.source_lang_var,
            state="disabled"
        )
        self.source_lang_combo.grid(row=3, column=0, pady=(0,10), padx=10, sticky="ew")
        
        # Target language
        self.target_lang_label = ctk.CTkLabel(self, text="Target Language:")
        self.target_lang_label.grid(row=4, column=0, pady=(10,0), padx=10, sticky="w")
        
        self.target_lang_combo = ctk.CTkOptionMenu(
            self,
            values=['English', 'Japanese', 'Korean', 'Chinese (Simplified)', 'Chinese (Traditional)'],
            variable=self.target_lang_var,
            state="disabled"
        )
        self.target_lang_combo.grid(row=5, column=0, pady=(0,10), padx=10, sticky="ew")
    
    def setup_context_frame(self):
        """Setup the context input frame"""
        self.context_frame = ctk.CTkFrame(self)
        self.context_frame.grid(row=6, column=0, sticky="ew", padx=10, pady=5)
        self.context_frame.grid_columnconfigure(0, weight=1)
        
        self.context_label = ctk.CTkLabel(
            self.context_frame,
            text="Context (Optional):",
            anchor="w"
        )
        self.context_label.grid(row=0, column=0, sticky="w", padx=5, pady=(5,0))
        
        self.context_text = ctk.CTkTextbox(
            self.context_frame,
            height=60,
            wrap="word",
            state="disabled"
        )
        self.context_text.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.context_text.insert("1.0", "Add context to help with translation accuracy...")
        self.context_text.bind("<FocusIn>", self.clear_context_placeholder)
        self.context_text.bind("<FocusOut>", self.restore_context_placeholder)
    
    def setup_translation_frame(self):
        """Setup the translation result frame"""
        self.translation_frame = ctk.CTkFrame(self)
        self.translation_frame.grid(row=7, column=0, sticky="nsew", padx=10, pady=5)
        self.translation_frame.grid_columnconfigure(0, weight=1)
        self.translation_frame.grid_rowconfigure(0, weight=1)
        
        self.grid_rowconfigure(7, weight=1)
        
        self.translation_text = ctk.CTkTextbox(
            self.translation_frame,
            wrap="word",
            height=200,
            font=("Arial", 14)
        )
        self.translation_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Translate button
        self.translate_btn = ctk.CTkButton(
            self,
            text="Translate",
            command=self.capture_and_translate,
            state="disabled"
        )
        self.translate_btn.grid(row=8, column=0, pady=10, padx=10, sticky="ew")
    
    def setup_status_label(self):
        """Setup the status label"""
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            text_color="blue"
        )
        self.status_label.grid(row=9, column=0, pady=10, padx=10, sticky="ew")
    
    def clear_context_placeholder(self, event):
        if self.context_text.get("1.0", "end-1c") == "Add context to help with translation accuracy...":
            self.context_text.delete("1.0", "end")
    
    def restore_context_placeholder(self, event):
        """Restore the placeholder text if context is empty"""
        if not self.context_text.get("1.0", "end-1c").strip():
            self.context_text.insert("1.0", "Add context to help with translation accuracy...")
    
    def open_settings(self):
        """Open the settings window"""
        settings_window = SettingsWindow(self)
        settings_window.grab_set()
    
    def show_capture_window(self):
        """Show the capture window"""
        if self.capture_window is None or not self.capture_window.winfo_exists():
            self.capture_window = CaptureWindow(self)
        self.capture_window.deiconify()
        self.capture_window.lift()
    
    def capture_and_translate(self):
        """Handle the capture and translation process"""
        try:
            if self.capture_window is None or not self.capture_window.winfo_exists():
                self.capture_window = CaptureWindow(self)
            
            # Get the screenshot
            screenshot = self.capture_window.capture_screenshot()
            if screenshot is None:
                return
            
            # Get context and languages
            context = self.context_text.get("1.0", "end-1c")
            if context == "Add context to help with translation accuracy...":
                context = ""
            
            source_lang = self.source_lang_var.get()
            target_lang = self.target_lang_var.get()
            
            # Perform OCR
            self.status_label.configure(text="Performing OCR...")
            text = self.ocr_service.perform_ocr(screenshot, source_lang)
            
            if not text:
                self.update_translation("No text was detected in the captured area")
                return
            
            # Translate text
            self.status_label.configure(text="Translating...")
            translation = self.translation_service.translate(text, source_lang, target_lang, context)
            
            # Update UI
            self.update_translation(translation)
            self.status_label.configure(text="Done")
            
        except Exception as e:
            logger.error(f"Error in capture_and_translate: {str(e)}")
            self.update_translation(f"Error: {str(e)}")
            self.status_label.configure(text="Error occurred")
    
    def update_translation(self, text):
        """Update the translation text box"""
        self.translation_text.configure(state="normal")
        self.translation_text.delete("1.0", "end")
        self.translation_text.insert("1.0", text)
        self.translation_text.configure(state="disabled")

    def show_api_key_error(self):
        """Show API key error message"""
        self.show_error_message("Please enter your OpenAI API key in Settings")
    
    def show_error_message(self, message):
        """Show error message to user"""
        self.status_label.configure(text=message, text_color="red")
