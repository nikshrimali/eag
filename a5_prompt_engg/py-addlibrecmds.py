import time
import subprocess
import pyautogui
import Quartz
from AppKit import NSWorkspace, NSScreen
import os

# Initialize global variables
draw_app = None
screen_width, screen_height = 0, 0
draw_window_position = (0, 0)
draw_window_size = (0, 0)

def get_screen_dimensions():
    """Get the dimensions of all connected screens"""
    global screen_width, screen_height
    
    # Get the main screen dimensions
    main_screen = NSScreen.mainScreen()
    if main_screen:
        screen_width = main_screen.frame().size.width
        screen_height = main_screen.frame().size.height
    else:
        # Fallback to pyautogui if NSScreen fails
        screen_width, screen_height = pyautogui.size()
    
    return screen_width, screen_height

def wait_for_element(template_path, timeout=10, confidence=0.8):
    """Wait for an element to appear on screen before proceeding"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            location = pyautogui.locateOnScreen(template_path, confidence=confidence)
            if location:
                return location
        except Exception:
            pass
        time.sleep(0.5)
    
    raise TimeoutError(f"Element {template_path} not found after {timeout} seconds")

def focus_application(app_name):
    """Focus on a specific application by name"""
    apps = NSWorkspace.sharedWorkspace().runningApplications()
    for app in apps:
        if app_name.lower() in app.localizedName().lower():
            app.activateWithOptions_(Quartz.NSApplicationActivateIgnoringOtherApps)
            return True
    return False

def get_relative_coordinates(x, y):
    """Convert absolute coordinates to coordinates relative to the Draw window"""
    global draw_window_position, draw_window_size
    
    rel_x = x - draw_window_position[0]
    rel_y = y - draw_window_position[1]
    
    # Ensure coordinates are within the window
    rel_x = max(0, min(rel_x, draw_window_size[0]))
    rel_y = max(0, min(rel_y, draw_window_size[1]))
    
    return rel_x, rel_y

def scale_coordinates(x, y, target_width=1920, target_height=1080):
    """Scale coordinates based on target resolution vs actual screen resolution"""
    global screen_width, screen_height
    
    # Calculate scaling factors
    width_scale = screen_width / target_width
    height_scale = screen_height / target_height
    
    # Scale coordinates
    scaled_x = int(x * width_scale)
    scaled_y = int(y * height_scale)
    
    return scaled_x, scaled_y

async def open_libreoffice_draw():
    """Open LibreOffice Draw maximized"""
    global draw_app, draw_window_position, draw_window_size, screen_width, screen_height
    
    try:
        # Get screen dimensions
        get_screen_dimensions()
        
        # Start LibreOffice Draw
        subprocess.Popen(['open', '-a', 'LibreOffice'])
        time.sleep(2)  # Wait for LibreOffice to start
        
        # Focus on LibreOffice
        if not focus_application("LibreOffice"):
            raise Exception("Could not focus on LibreOffice")
        
        time.sleep(1)
        
        # Select "Draw" from the Start Center using keyboard
        pyautogui.hotkey('tab', interval=0.2)  # Move to document type selection
        for _ in range(4):  # Tab to Draw (adjust if needed)
            pyautogui.hotkey('tab', interval=0.2)
        pyautogui.hotkey('space')  # Select Draw
        
        # Wait for Draw to open (look for toolbar or other static element)
        # For production code, replace 'draw_toolbar.png' with an actual screenshot of a Draw element
        # wait_for_element('draw_toolbar.png', timeout=10)
        time.sleep(5)  # Fallback waiting time
        
        # Maximize window
        pyautogui.hotkey('command', 'option', 'm')
        time.sleep(1)
        
        # Get the active window position and size 
        # (In production, replace with actual window detection logic)
        draw_window_position = (0, 0)  # Top-left corner
        draw_window_size = (screen_width, screen_height)  # Full screen
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": "LibreOffice Draw opened successfully and maximized"
                }
            ]
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error opening LibreOffice Draw: {str(e)}"
                }
            ]
        }

async def draw_rectangle(x1, y1, x2, y2):
    """Draw a rectangle in LibreOffice Draw from (x1,y1) to (x2,y2)"""
    global draw_app
    
    try:
        # Focus on LibreOffice
        if not focus_application("LibreOffice"):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "LibreOffice Draw is not open. Please call open_libreoffice_draw first."
                    }
                ]
            }
        
        # Scale coordinates based on screen resolution
        x1, y1 = scale_coordinates(x1, y1)
        x2, y2 = scale_coordinates(x2, y2)
        
        # Wait for Draw to be ready (look for a static element)
        time.sleep(1)
        
        # Select Rectangle tool using keyboard shortcuts
        pyautogui.hotkey('f4')  # Opens shape toolbar
        time.sleep(0.5)
        
        # Navigate to Rectangle (might need adjustments based on actual LibreOffice Draw interface)
        pyautogui.hotkey('down')  # Navigate to rectangle
        time.sleep(0.2)
        pyautogui.hotkey('return')  # Select rectangle
        time.sleep(0.5)
        
        # Draw the rectangle
        pyautogui.moveTo(x1, y1)
        pyautogui.mouseDown()
        pyautogui.moveTo(x2, y2)
        pyautogui.mouseUp()
        
        # Return to selection tool
        pyautogui.hotkey('escape')
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2})"
                }
            ]
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error drawing rectangle: {str(e)}"
                }
            ]
        }

async def add_text_in_draw(text):
    """Add text in LibreOffice Draw"""
    try:
        # Focus on LibreOffice
        if not focus_application("LibreOffice"):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "LibreOffice Draw is not open. Please call open_libreoffice_draw first."
                    }
                ]
            }
        
        # Wait for Draw to be ready
        time.sleep(1)
        
        # Get coordinates for text placement (center of screen by default)
        x, y = scale_coordinates(screen_width // 2, screen_height // 2)
        
        # Select Text tool using keyboard shortcut
        pyautogui.hotkey('f2')  # Text tool shortcut in LibreOffice Draw
        time.sleep(0.5)
        
        # Click where to add text
        pyautogui.click(x, y)
        time.sleep(0.5)
        
        # Type the text
        pyautogui.write(text)
        time.sleep(0.5)
        
        # Finish text entry
        pyautogui.hotkey('escape')
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Text: '{text}' added successfully"
                }
            ]
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error adding text: {str(e)}"
                }
            ]
        }

# Additional helper functions

async def save_document(filename):
    """Save the current LibreOffice Draw document"""
    try:
        # Focus on LibreOffice
        if not focus_application("LibreOffice"):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "LibreOffice Draw is not open. Please call open_libreoffice_draw first."
                    }
                ]
            }
        
        # Save using keyboard shortcut
        pyautogui.hotkey('command', 's')
        time.sleep(1)
        
        # Type filename
        pyautogui.write(filename)
        time.sleep(0.5)
        
        # Press Enter to save
        pyautogui.hotkey('return')
        time.sleep(1)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Document saved as '{filename}'"
                }
            ]
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text", 
                    "text": f"Error saving document: {str(e)}"
                }
            ]
        }

# Initialize screen dimensions on module load
get_screen_dimensions()