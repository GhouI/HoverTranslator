import customtkinter as ctk
import pyautogui
import easyocr
from openai import OpenAI
import torch
import os
import logging
from PIL import Image
import json
import win32gui
import win32ui
import win32con
from array import array

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.app = parent.app  # Get the TranslatorApp instance
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
        if self.show_key.get():
            self.api_key_entry.configure(show="")
        else:
            self.api_key_entry.configure(show="*")
            
    def save_settings(self):
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            self.show_error("API Key is required")
            return
            
        # Save settings
        settings = {
            "api_key": api_key,
            "model": self.model_var.get()
        }
        
        try:
            with open("settings.json", "w") as f:
                json.dump(settings, f)
            
            self.app.api_key = api_key
            if self.app.setup_openai():
                self.app.setup_ocr()
                self.app.status_label.configure(text="Ready")
                self.app.source_lang_combo.configure(state="normal")
                self.app.target_lang_combo.configure(state="normal")
                self.app.translate_btn.configure(state="normal")
                self.app.translation_text.configure(state="normal")
                self.app.translation_text.delete("1.0", "end")
                self.app.translation_text.insert("1.0", "Translation will appear here")
                self.app.translation_text.configure(state="disabled")
                self.destroy()
            else:
                self.show_error("Failed to connect to OpenAI API. Please check your API key.")
        except Exception as e:
            self.show_error(f"Error saving settings: {str(e)}")
            
    def show_error(self, message):
        error_window = ctk.CTkToplevel(self)
        error_window.title("Error")
        error_window.geometry("300x100")
        
        error_label = ctk.CTkLabel(error_window, text=message, wraplength=250)
        error_label.pack(pady=20, padx=20)
        
        ok_btn = ctk.CTkButton(error_window, text="OK", command=error_window.destroy)
        ok_btn.pack(pady=10)

class TranslatorApp:
    def __init__(self):
        self.api_key = None
        self.capture_window = None  # Initialize capture_window reference
        self.load_settings()
        
        # Create main window first
        self.root = ctk.CTk()
        self.root.title("Screen Translator")
        self.root.geometry("400x600")
        self.root.app = self  # Store reference to TranslatorApp instance
        
        # Initialize StringVars
        self.source_lang_var = ctk.StringVar(master=self.root, value="Japanese")
        self.target_lang_var = ctk.StringVar(master=self.root, value="English")
        
        # Pre-initialize capture window
        self.setup_capture_frame()
        
        if not self.check_api_key():
            self.setup_ui()  # Still setup UI, but it will show API key required message
        else:
            self.setup_ocr()
            self.setup_openai()
            self.setup_ui()
            
        # Add translate button
        self.translate_btn = ctk.CTkButton(
            self.root,
            text="Translate",
            command=self.capture_and_translate,
            state="normal" if self.api_key else "disabled"
        )
        self.translate_btn.grid(row=8, column=0, pady=10, padx=10, sticky="ew")

    def load_settings(self):
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)
                self.api_key = settings.get("api_key")
        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")

    def check_api_key(self):
        return bool(self.api_key)

    def setup_openai(self):
        if not self.api_key:
            return False
        try:
            self.client = OpenAI(api_key=self.api_key)
            # Test connection
            response = self.client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[{"role": "user", "content": "Test connection"}]
            )
            logger.info("OpenAI API connection successful")
            return True
        except Exception as e:
            logger.error(f"Error initializing OpenAI: {str(e)}")
            return False

    def setup_ui(self):
        # Configure grid
        self.root.grid_columnconfigure(0, weight=1)
        
        # Menu bar (Settings)
        self.menu_frame = ctk.CTkFrame(self.root)
        self.menu_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        self.menu_frame.grid_columnconfigure(1, weight=1)
        
        # Settings button
        self.settings_btn = ctk.CTkButton(
            self.menu_frame,
            text="⚙️ Settings",
            command=self.open_settings,
            width=100
        )
        self.settings_btn.grid(row=0, column=0, padx=5, pady=5)
        
        # Show Capture Window button
        self.show_capture_btn = ctk.CTkButton(
            self.menu_frame,
            text="📷 Show Capture",
            command=self.show_capture_window,
            width=100,
            state="normal" if self.api_key else "disabled"
        )
        self.show_capture_btn.grid(row=0, column=1, padx=5, pady=5)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.root,
            text="API Key Required - Please add in Settings" if not self.api_key else "Ready"
        )
        self.status_label.grid(row=1, column=0, pady=10, padx=10, sticky="ew")
        
        # Source language selection
        self.source_lang_label = ctk.CTkLabel(self.root, text="Source Language:")
        self.source_lang_label.grid(row=2, column=0, pady=(10,0), padx=10, sticky="w")
        
        self.source_lang_combo = ctk.CTkOptionMenu(
            self.root,
            values=['English', 'Japanese', 'Korean', 'Chinese (Simplified)', 'Chinese (Traditional)'],
            variable=self.source_lang_var,
            state="normal" if self.api_key else "disabled"
        )
        self.source_lang_combo.grid(row=3, column=0, pady=(0,10), padx=10, sticky="ew")
        
        # Context input frame
        self.context_frame = ctk.CTkFrame(self.root)
        self.context_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=5)
        self.context_frame.grid_columnconfigure(0, weight=1)
        
        # Context label
        self.context_label = ctk.CTkLabel(
            self.context_frame,
            text="Context (Optional):",
            anchor="w"
        )
        self.context_label.grid(row=0, column=0, sticky="w", padx=5, pady=(5,0))
        
        # Context text box
        self.context_text = ctk.CTkTextbox(
            self.context_frame,
            height=60,
            wrap="word"
        )
        self.context_text.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.context_text.insert("1.0", "Add context to help with translation accuracy...")
        self.context_text.bind("<FocusIn>", self.clear_context_placeholder)
        self.context_text.bind("<FocusOut>", self.restore_context_placeholder)
        
        # Target language selection
        self.target_lang_label = ctk.CTkLabel(self.root, text="Target Language:")
        self.target_lang_label.grid(row=5, column=0, pady=(10,0), padx=10, sticky="w")
        
        self.target_lang_combo = ctk.CTkOptionMenu(
            self.root,
            values=['English', 'Japanese', 'Korean', 'Chinese (Simplified)', 'Chinese (Traditional)'],
            variable=self.target_lang_var,
            state="normal" if self.api_key else "disabled"
        )
        self.target_lang_combo.grid(row=6, column=0, pady=(0,10), padx=10, sticky="ew")
        
        # Translation result frame
        self.translation_frame = ctk.CTkFrame(self.root)
        self.translation_frame.grid(row=7, column=0, sticky="nsew", padx=10, pady=5)
        self.translation_frame.grid_columnconfigure(0, weight=1)
        self.translation_frame.grid_rowconfigure(0, weight=1)
        
        # Make translation frame expandable
        self.root.grid_rowconfigure(7, weight=1)
        
        # Scrollable text widget for translation
        self.translation_text = ctk.CTkTextbox(
            self.translation_frame,
            wrap="word",
            height=200,
            font=("Arial", 14)
        )
        self.translation_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        if not self.api_key:
            self.translation_text.configure(state="normal")
            self.translation_text.insert("1.0", "Please add API Key in Settings to start translation")
            self.translation_text.configure(state="disabled")
        else:
            self.translation_text.configure(state="normal")
            self.translation_text.insert("1.0", "Translation will appear here")
            self.translation_text.configure(state="disabled")
        
    def open_settings(self):
        settings_window = SettingsWindow(self.root)
        settings_window.grab_set()  # Make the window modal
        
    def show_capture_window(self):
        if self.capture_window is None or not self.capture_window.winfo_exists():
            self.setup_capture_frame()
        self.capture_window.deiconify()
        self.capture_window.lift()

    def setup_ocr(self):
        try:
            if torch.cuda.is_available():
                gpu = True
                device = torch.cuda.get_device_name(0)
                logger.info(f"CUDA is available! Using GPU: {device}")
            else:
                gpu = False
                logger.info("CUDA is not available. Using CPU")

            # Initialize readers for different languages
            self.readers = {
                'en_ja': easyocr.Reader(['en', 'ja'], gpu=gpu),
                'en_ko': easyocr.Reader(['en', 'ko'], gpu=gpu),
                'en_ch_sim': easyocr.Reader(['en', 'ch_sim'], gpu=gpu),
                'en_ch_tra': easyocr.Reader(['en', 'ch_tra'], gpu=gpu)
            }
            logger.info("EasyOCR initialized successfully with all readers")

        except Exception as e:
            logger.error(f"Error initializing EasyOCR: {str(e)}")
            # Fallback to basic configuration
            self.readers = {
                'en_ja': easyocr.Reader(['en', 'ja'], gpu=False)
            }
            logger.warning("Falling back to basic English/Japanese support")

    def setup_capture_frame(self):
        if self.capture_window is not None:
            try:
                self.capture_window.destroy()
            except:
                pass
        
        self.capture_window = ctk.CTkToplevel(self.root)
        self.capture_window.title("")
        self.capture_window.geometry("300x200")
        self.capture_window.attributes('-alpha', 0.5)  # Make window semi-transparent
        self.capture_window.attributes('-topmost', True)
        self.capture_window.overrideredirect(True)  # Remove window decorations
        
        # Create a frame with red border
        self.capture_frame = ctk.CTkFrame(
            self.capture_window,
            fg_color="transparent",
            border_color="red",
            border_width=2
        )
        self.capture_frame.pack(expand=True, fill="both", padx=2, pady=2)
        
        # Add resize handles
        self.resize_handle = ctk.CTkLabel(
            self.capture_frame,
            text="⟲",  # Resize icon
            width=20,
            height=20,
            fg_color="red",
            text_color="white",
            corner_radius=10
        )
        self.resize_handle.place(relx=1.0, rely=1.0, anchor="se")
        
        # Add close button
        self.close_btn = ctk.CTkButton(
            self.capture_frame,
            text="×",
            width=20,
            height=20,
            fg_color="red",
            hover_color="darkred",
            command=self.capture_window.withdraw
        )
        self.close_btn.place(relx=1.0, rely=0.0, anchor="ne")
        
        # Bind mouse events for dragging and resizing
        self.capture_window.bind('<Button-1>', self.on_click)
        self.capture_window.bind('<B1-Motion>', self.on_drag)
        self.resize_handle.bind('<Button-1>', self.start_resize)
        self.resize_handle.bind('<B1-Motion>', self.on_resize)
        
        # Initially hide the capture window
        self.capture_window.withdraw()
        
    def start_resize(self, event):
        self.resize_x = event.x_root
        self.resize_y = event.y_root
        self.window_width = self.capture_window.winfo_width()
        self.window_height = self.capture_window.winfo_height()
        
    def on_resize(self, event):
        try:
            dx = event.x_root - self.resize_x
            dy = event.y_root - self.resize_y
            
            new_width = max(100, self.window_width + dx)  # Minimum width of 100
            new_height = max(100, self.window_height + dy)  # Minimum height of 100
            
            self.capture_window.geometry(f"{new_width}x{new_height}")
        except Exception as e:
            logger.error(f"Error in on_resize: {str(e)}")

    def capture_and_translate(self):
        try:
            if self.capture_window is None or not self.capture_window.winfo_exists():
                self.setup_capture_frame()
            self.capture_window.deiconify()
            self.capture_window.update_idletasks()  # Force window update
            logger.info("Capture and translate started!")
            
            # Get the geometry of capture window before hiding
            x = self.capture_window.winfo_x()
            y = self.capture_window.winfo_y()
            width = self.capture_window.winfo_width()
            height = self.capture_window.winfo_height()
            
            # Hide windows temporarily for screenshot
            self.capture_window.withdraw()
            self.root.withdraw()
            self.root.update_idletasks()  # Force window update
            
            # Take screenshot using faster method
            import win32gui
            import win32ui
            import win32con
            from array import array
            
            # Get screen DC
            hwin = win32gui.GetDesktopWindow()
            hwindc = win32gui.GetWindowDC(hwin)
            srcdc = win32ui.CreateDCFromHandle(hwindc)
            memdc = srcdc.CreateCompatibleDC()
            
            try:
                # Create bitmap
                bmp = win32ui.CreateBitmap()
                bmp.CreateCompatibleBitmap(srcdc, width, height)
                memdc.SelectObject(bmp)
                
                # Copy screen
                memdc.BitBlt((0, 0), (width, height), srcdc, (x, y), win32con.SRCCOPY)
                
                # Convert to PIL Image
                bmpinfo = bmp.GetInfo()
                bmpstr = bmp.GetBitmapBits(True)
                img = Image.frombuffer(
                    'RGB',
                    (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                    bmpstr, 'raw', 'BGRX', 0, 1
                )
            finally:
                # Clean up Win32 resources
                memdc.DeleteDC()
                srcdc.DeleteDC()
                win32gui.ReleaseDC(hwin, hwindc)
                win32gui.DeleteObject(bmp.GetHandle())
            
            # Show windows again immediately
            self.root.deiconify()
            self.capture_window.deiconify()
            
            # Update status
            self.status_label.configure(text="Processing image...")
            
            # Save screenshot temporarily
            temp_path = "temp_screenshot.png"
            img.save(temp_path)
            
            # Get selected languages
            source_lang = self.source_lang_var.get()
            target_lang = self.target_lang_var.get()
            
            # Get context if provided
            context = self.context_text.get("1.0", "end-1c")
            
            # Perform OCR
            self.status_label.configure(text="Performing OCR...")
            
            # Get appropriate reader
            if source_lang == "Japanese":
                reader = self.readers['en_ja']
            elif source_lang == "Korean":
                reader = self.readers['en_ko']
            elif source_lang == "Chinese (Simplified)":
                reader = self.readers['en_ch_sim']
            elif source_lang == "Chinese (Traditional)":
                reader = self.readers['en_ch_tra']
            else:
                reader = self.readers['en_ja']
            
            result = reader.readtext(temp_path)
            
            if not result:
                self.status_label.configure(text="No text detected")
                self.translation_text.configure(state="normal")
                self.translation_text.delete("1.0", "end")
                self.translation_text.insert("1.0", "No text was detected in the captured area")
                self.translation_text.configure(state="disabled")
                return
            
            # Extract text
            text = ' '.join([entry[1] for entry in result])
            
            # Translate text
            self.status_label.configure(text="Translating...")
            
            # Call OpenAI API for translation
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": self.translate_text(source_lang, target_lang, context)
                    },
                    {"role": "user", "content": text}
                ]
            )

            translation = response.choices[0].message.content.strip()
            
            # Update UI with translation
            self.translation_text.configure(state="normal")
            self.translation_text.delete("1.0", "end")
            self.translation_text.insert("1.0", translation)
            self.translation_text.configure(state="disabled")
            self.status_label.configure(text="Done")
            
            # Clean up
            os.remove(temp_path)
            
        except Exception as e:
            logger.error(f"Error in capture_and_translate: {str(e)}")
            self.translation_text.configure(state="normal")
            self.translation_text.delete("1.0", "end")
            self.translation_text.insert("1.0", f"Error: {str(e)}")
            self.translation_text.configure(state="disabled")
            self.status_label.configure(text="Error occurred")
        finally:
            # Ensure windows are shown
            self.root.deiconify()
            self.capture_window.deiconify()

    def translate_text(self, source_lang, target_lang, context=None):
        """
        Translate the given text from {source_lang} to {target_lang}.
        Optional context can be provided to improve translation accuracy.
        """
        prompt = (
            f"You are a professional translator. Translate the following text from {source_lang} to {target_lang}.\n\n"
        )
        
        if context and context.strip() and context != "Add context to help with translation accuracy...":
            prompt += (
                f"Context for translation:\n"
                f"{context}\n\n"
            )
        
        prompt += (
            f"Guidelines:\n"
            f"1. Provide ONLY the translated text\n"
            f"2. Maintain the original tone and context\n"
            f"3. Use natural {target_lang} expressions\n"
            f"4. Preserve formatting and line breaks\n"
            f"5. NO explanations or additional text\n"
            f"6. Consider the provided context (if any) for more accurate translation"
        )
        return prompt

    def clear_context_placeholder(self, event):
        if self.context_text.get("1.0", "end-1c") == "Add context to help with translation accuracy...":
            self.context_text.delete("1.0", "end")

    def restore_context_placeholder(self, event):
        if not self.context_text.get("1.0", "end-1c").strip():
            self.context_text.delete("1.0", "end")
            self.context_text.insert("1.0", "Add context to help with translation accuracy...")

    def on_click(self, event):
        self.x = event.x
        self.y = event.y

    def on_drag(self, event):
        if not hasattr(self, 'capture_window') or self.capture_window is None:
            return
            
        try:
            x = self.capture_window.winfo_x()
            y = self.capture_window.winfo_y()
            dx = event.x - self.x
            dy = event.y - self.y
            self.capture_window.geometry(f"+{x + dx}+{y + dy}")
        except Exception as e:
            logger.error(f"Error in on_drag: {str(e)}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = TranslatorApp()
    app.run()
