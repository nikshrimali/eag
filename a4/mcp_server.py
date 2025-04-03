import time
import subprocess
import pyautogui
import Quartz
from AppKit import NSWorkspace
import math
from PIL import Image as PILImage


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
        open_draw_x, open_draw_y = 200, 500
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
def draw_rectangle(x1:int=550, y1:int=400, x2:int=850, y2:int=600):
    """Draw a rectangle in LibreOffice Draw"""
    try:
        
        # Focus on LibreOffice
        if not focus_application("LibreOffice"):
            return {"status": "error", "message": "Could not focus on LibreOffice Draw"}
        
        # Click on Rectangle tool
        rect_tool_x, rect_tool_y = 95, 268 
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
def enter_text_in_rectangle(text):
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
    
# DEFINE TOOLS

#addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print("CALLED: add(a: int, b: int) -> int:")
    return int(a + b)

@mcp.tool()
def add_list(l: list) -> int:
    """Add all numbers in a list"""
    print("CALLED: add(l: list) -> int:")
    return sum(l)

# subtraction tool
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    print("CALLED: subtract(a: int, b: int) -> int:")
    return int(a - b)

# multiplication tool
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    print("CALLED: multiply(a: int, b: int) -> int:")
    return int(a * b)

#  division tool
@mcp.tool() 
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    print("CALLED: divide(a: int, b: int) -> float:")
    return float(a / b)

# power tool
@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    print("CALLED: power(a: int, b: int) -> int:")
    return int(a ** b)

# square root tool
@mcp.tool()
def sqrt(a: int) -> float:
    """Square root of a number"""
    print("CALLED: sqrt(a: int) -> float:")
    return float(a ** 0.5)

# cube root tool
@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    print("CALLED: cbrt(a: int) -> float:")
    return float(a ** (1/3))

# factorial tool
@mcp.tool()
def factorial(a: int) -> int:
    """factorial of a number"""
    print("CALLED: factorial(a: int) -> int:")
    return int(math.factorial(a))

# log tool
@mcp.tool()
def log(a: int) -> float:
    """log of a number"""
    print("CALLED: log(a: int) -> float:")
    return float(math.log(a))

# remainder tool
@mcp.tool()
def remainder(a: int, b: int) -> int:
    """remainder of two numbers divison"""
    print("CALLED: remainder(a: int, b: int) -> int:")
    return int(a % b)

# sin tool
@mcp.tool()
def sin(a: int) -> float:
    """sin of a number"""
    print("CALLED: sin(a: int) -> float:")
    return float(math.sin(a))

# cos tool
@mcp.tool()
def cos(a: int) -> float:
    """cos of a number"""
    print("CALLED: cos(a: int) -> float:")
    return float(math.cos(a))

# tan tool
@mcp.tool()
def tan(a: int) -> float:
    """tan of a number"""
    print("CALLED: tan(a: int) -> float:")
    return float(math.tan(a))

# mine tool
@mcp.tool()
def mine(a: int, b: int) -> int:
    """special mining tool"""
    print("CALLED: mine(a: int, b: int) -> int:")
    return int(a - b - b)

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    print("CALLED: create_thumbnail(image_path: str) -> Image:")
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")

@mcp.tool()
def strings_to_chars_to_int(string: str) -> list[int]:
    """Return the ASCII values of the characters in a word"""
    print("CALLED: strings_to_chars_to_int(string: str) -> list[int]:")
    return [int(ord(char)) for char in string]

@mcp.tool()
def int_list_to_exponential_sum(int_list: list) -> float:
    """Return sum of exponentials of numbers in a list"""
    print("CALLED: int_list_to_exponential_sum(int_list: list) -> float:")
    return sum(math.exp(i) for i in int_list)

@mcp.tool()
def fibonacci_numbers(n: int) -> list:
    """Return the first n Fibonacci Numbers"""
    print("CALLED: fibonacci_numbers(n: int) -> list:")
    if n <= 0:
        return []
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence[:n]

if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
