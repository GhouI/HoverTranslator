"""
Capture window implementation for screen capture functionality
"""
import customtkinter as ctk
from PIL import Image
import win32gui
import win32ui
import win32con
import logging

logger = logging.getLogger(__name__)

class CaptureWindow(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setup_window()
        self.setup_ui()
        
    def setup_window(self):
        """Configure the capture window properties"""
        self.title("")
        self.geometry("300x200")
        self.attributes('-alpha', 0.5)
        self.overrideredirect(True)
        
        # Initialize drag variables
        self.x = None
        self.y = None
        
        # Bind events
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)
        
    def setup_ui(self):
        """Setup the capture window UI components"""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create main frame with red border
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=2, border_color="red")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Close button
        self.close_btn = ctk.CTkButton(
            self,
            text="×",
            width=20,
            height=20,
            command=self.withdraw,
            fg_color="red",
            hover_color="darkred"
        )
        self.close_btn.place(relx=1, rely=0, anchor="ne")
        
        # Resize handle
        self.resize_btn = ctk.CTkButton(
            self,
            text="⟲",
            width=20,
            height=20,
            command=None,
            fg_color="red",
            hover_color="darkred"
        )
        self.resize_btn.place(relx=1, rely=1, anchor="se")
        self.resize_btn.bind("<B1-Motion>", self.on_resize)
        
    def on_click(self, event):
        """Handle mouse click event"""
        self.x = event.x
        self.y = event.y
        
    def on_drag(self, event):
        """Handle window dragging"""
        try:
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.winfo_x() + deltax
            y = self.winfo_y() + deltay
            self.geometry(f"+{x}+{y}")
        except Exception as e:
            logger.error(f"Error in on_drag: {str(e)}")
            
    def on_resize(self, event):
        """Handle window resizing"""
        try:
            x = max(self.winfo_width() + (event.x - self.winfo_width()), 100)
            y = max(self.winfo_height() + (event.y - self.winfo_height()), 100)
            self.geometry(f"{x}x{y}")
        except Exception as e:
            logger.error(f"Error in on_resize: {str(e)}")
            
    def capture_screenshot(self):
        """Capture the screen area within the window"""
        try:
            self.update_idletasks()
            
            # Get window geometry
            x = self.winfo_x()
            y = self.winfo_y()
            width = self.winfo_width()
            height = self.winfo_height()
            
            # Hide windows
            self.withdraw()
            self.app.root.withdraw()
            self.app.root.update_idletasks()
            
            try:
                # Setup screen capture
                hwin = win32gui.GetDesktopWindow()
                hwindc = win32gui.GetWindowDC(hwin)
                srcdc = win32ui.CreateDCFromHandle(hwindc)
                memdc = srcdc.CreateCompatibleDC()
                
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
                
                return img
                
            finally:
                # Cleanup
                memdc.DeleteDC()
                srcdc.DeleteDC()
                win32gui.ReleaseDC(hwin, hwindc)
                win32gui.DeleteObject(bmp.GetHandle())
                
                # Show windows
                self.app.root.deiconify()
                self.deiconify()
                
        except Exception as e:
            logger.error(f"Error in capture_screenshot: {str(e)}")
            return None
