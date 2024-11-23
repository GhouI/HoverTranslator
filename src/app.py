"""
Main entry point for the Screen Translator application
"""
import logging
from ui.main_window import TranslatorApp

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Initialize and run the application"""
    app = TranslatorApp()
    app.mainloop()

if __name__ == "__main__":
    main()
