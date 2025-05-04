# modules/action.py

from typing import Dict, Any, Union
from pydantic import BaseModel
import ast

from logging import Logger
# Initialize logger
logger = Logger(__name__)

# Optional logging fallback
try:
    from agent import log
except ImportError:
    import datetime
    def log(stage: str, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")


class ToolCallResult(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Union[str, list, dict]
    raw_response: Any



import json
import ast
from typing import Dict, Any, Tuple

def log(tag: str, message: str) -> None:
    """Helper function for logging."""
    print(f"[{tag}] {message}")

def parse_function_call(response: str) -> Tuple[str, Dict[str, Any]]:
    """
    Parses a FUNCTION_CALL string that contains direct JSON input.
    
    Format expected:
    "FUNCTION_CALL: tool_name|{'json_string_here'}"
    
    Example:
    "FUNCTION_CALL: search|{'query': 'Current F1 Point Standings', 'max_results': 5}"
    
    Args:
        response: String containing the function call
        
    Returns:
        A tuple of (tool_name, arguments_dict)
    """
    try:
        # Check if the response starts with the expected prefix
        if not response.startswith("FUNCTION_CALL:"):
            raise ValueError("Invalid function call format. Must start with 'FUNCTION_CALL:'")
        
        log("parser", "Function call format validated")
        
        # Split into prefix and content
        _, raw = response.split(":", 1)
        raw = raw.strip()
        log("parser", f"Parsing function call: {raw}")
        
        # Split by the first pipe character to separate tool name and data
        parts = raw.split("|", 1)
        if len(parts) != 2:
            raise ValueError("Invalid format. Expected 'tool_name|{json}'")
        
        tool_name = parts[0].strip()
        json_str = parts[1].strip()
        
        log("parser", f"Tool name: {tool_name}")
        log("parser", f"JSON data: {json_str}")
        
        # Parse the JSON string
        try:
            # First try direct JSON parsing
            args = json.loads(json_str)
        except json.JSONDecodeError:
            # If that fails, try using ast.literal_eval which can handle both JSON and Python literals
            try:
                args = ast.literal_eval(json_str)
            except (SyntaxError, ValueError):
                raise ValueError(f"Invalid JSON format: {json_str}")
        
        log("parser", f"Parsed: {tool_name} → {args}")
        return tool_name, args
    
    except Exception as e:
        log("parser", f"❌ Parse failed: {e}")
        raise


def parse_function_call1(response: str) -> tuple[str, Dict[str, Any]]:
    """
    Parses a FUNCTION_CALL string like:
    "FUNCTION_CALL: add|a=5|b=7"
    Into a tool name and a dictionary of arguments.
    """
    try:
        if not response.startswith("FUNCTION_CALL:"):
            raise ValueError("Invalid function call format.")

        _, raw = response.split(":", 1)
        logger.info(f"\n\n\n @@@###$$$$ Parsing function call: {raw}")
        parts = [p.strip() for p in raw.split("|")]
        tool_name, param_parts = parts[0], parts[1:]

        logger.info(f"\n\n\n @@@###$$$$ Parts: {parts[0]} \n\n {parts[1:]}")

        args = {}
        for part in param_parts:
            if "=" not in part:
                raise ValueError(f"Invalid parameter: {part}")
            key, val = part.split("=", 1)

            # Try parsing as literal, fallback to string
            try:
                parsed_val = ast.literal_eval(val)
            except Exception:
                parsed_val = val.strip()

            # Support nested keys (e.g., input.value)
            keys = key.split(".")
            current = args
            for k in keys[:-1]:
                current = current.setdefault(k, {})
            current[keys[-1]] = parsed_val

        log("parser", f"Parsed: {tool_name} → {args}")
        return tool_name, args

    except Exception as e:
        log("parser", f"❌ Parse failed: {e}")
        raise
