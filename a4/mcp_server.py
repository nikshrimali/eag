import time
import subprocess
import pyautogui
import Quartz
from AppKit import NSWorkspace

import sys

from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types

# instantiate an MCP server client
mcp = FastMCP("Writer")

def focus_application(app_name):
    """Focus on a specific application by name"""
    apps = NSWorkspace.sharedWorkspace().runningApplications()
    for app in apps:
        if app_name.lower() in app.localizedName().lower():
            app.activateWithOptions_(Quartz.NSApplicationActivateIgnoringOtherApps)
            return True
    return False

# Opening Libreoffice tool
@mcp.tool()
def open_libreoffice():
    """Open LibreOffice Draw tool"""
    try:
        # Start LibreOffice
        subprocess.Popen(['open', '-a', 'LibreOffice'])
        time.sleep(2)  # Wait for LibreOffice to start
        
        # Focus on LibreOffice
        if not focus_application("LibreOffice"):
            raise Exception("Could not focus on LibreOffice")
        
        # Click "Draw" from the Start Center
        open_draw_x, open_draw_y = 150, 475
        pyautogui.click(open_draw_x, open_draw_y)
        
        time.sleep(3)
        is_initialized = True

        return {
                "content": [
                    TextContent(
                        type="text",
                        text="LibreOffice Draw opened successfully"
                    )
                ]
            }


    except Exception as e:
        return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"Unable to open LibreOffice: error {str(e)}"
                    )
                ]
            }


@mcp.tool()
def draw_rectangle(x1:int=1050, y1:int=375, x2:int=1350, y2:int=675):
    """Draw a rectangle in LibreOffice Draw"""
    try:
        
        # Focus on LibreOffice
        if not focus_application("LibreOffice"):
            return {"status": "error", "message": "Could not focus on LibreOffice Draw"}
        
        # Click on Rectangle tool
        rect_tool_x, rect_tool_y = 90, 247
        pyautogui.moveTo(rect_tool_x, rect_tool_y, duration=0.5)
        pyautogui.click()
        time.sleep(1)
        
        # Draw the rectangle
        pyautogui.moveTo(x1, y1, duration=0.5)
        pyautogui.mouseDown()
        time.sleep(0.5)
        pyautogui.moveTo(x2, y2, duration=0.5)
        pyautogui.mouseUp()
        time.sleep(0.5)
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2})"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error drawing rectangle: {str(e)}"
                )
            ]
        }

@mcp.tool()
def enter_text_in_rectangle(self, text):
    """Enters text into the rectangle"""
    try:
        
        # Focus on LibreOffice
        if not focus_application("LibreOffice"):
            return {"status": "error", "message": "Could not focus on LibreOffice Draw"}
        
        # Position for text entry
        x_coord, y_coord = 1195, 520
        
        # Double click to activate text entry
        pyautogui.moveTo(x_coord, y_coord)
        pyautogui.doubleClick()
        time.sleep(2)
        
        # Type the text
        pyautogui.typewrite(text)
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Text:'{text}' added successfully"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )
            ]
        }
if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
