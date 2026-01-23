import pyautogui
import subprocess
import platform
import logging
from typing import Dict, List

# Configure logging for security auditing
logging.basicConfig(
    filename='logs/jarvis_security.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SystemTools:
    # Whitelist of allowed applications (security measure)
    ALLOWED_APPS: Dict[str, List[str]] = {
        "Windows": [
            "notepad", "calc", "calculator", "mspaint", "paint",
            "explorer", "cmd", "powershell", "chrome", "firefox",
            "edge", "msedge", "spotify", "discord", "vscode", "code"
        ],
        "Darwin": [  # macOS
            "Safari", "Google Chrome", "Firefox", "TextEdit",
            "Calculator", "Notes", "Spotify", "Discord", "VSCode"
        ],
        "Linux": [
            "firefox", "chromium", "gedit", "kate", "gnome-calculator",
            "spotify", "discord", "code"
        ]
    }
    
    # Whitelist of allowed key presses
    ALLOWED_KEYS = [
        "volumemute", "volumeup", "volumedown", "playpause",
        "nexttrack", "prevtrack", "stop", "mute"
    ]

    @staticmethod
    def press_key(key: str) -> str:
        """Presses a keyboard key with validation."""
        try:
            # Sanitize and validate input
            key = key.strip().lower()
            
            if not key:
                return "Error: Empty key provided"
            
            # Security: Only allow whitelisted media keys
            if key not in SystemTools.ALLOWED_KEYS:
                logging.warning(f"Attempted to press non-whitelisted key: {key}")
                return f"Error: Key '{key}' is not allowed for security reasons"
            
            pyautogui.press(key)
            logging.info(f"Successfully pressed key: {key}")
            return f"Pressed key: {key}"
        except Exception as e:
            logging.error(f"Failed to press key {key}: {str(e)}")
            return f"Failed to press key: {str(e)}"

    @staticmethod
    def open_application(app_name: str) -> str:
        """Safely opens an application using subprocess with whitelist validation."""
        system = platform.system()
        
        try:
            # Sanitize input
            app_name = app_name.strip().lower()
            
            if not app_name:
                return "Error: No application name provided"
            
            # Validate length to prevent abuse
            if len(app_name) > 50:
                logging.warning(f"Attempted to open app with suspiciously long name: {app_name[:50]}...")
                return "Error: Application name too long"
            
            # Check whitelist
            allowed_apps = SystemTools.ALLOWED_APPS.get(system, [])
            allowed_apps_lower = [app.lower() for app in allowed_apps]
            
            if app_name not in allowed_apps_lower:
                logging.warning(f"Attempted to open non-whitelisted application: {app_name}")
                return f"Error: Application '{app_name}' is not in the allowed list for security reasons"
            
            # Use subprocess.run with shell=False to prevent command injection
            if system == "Windows":
                # Map common names to Windows executables
                app_map = {
                    "calculator": "calc",
                    "paint": "mspaint"
                }
                app_executable = app_map.get(app_name, app_name)
                
                result = subprocess.run(
                    ["cmd", "/c", "start", "", app_executable],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            elif system == "Darwin":  # macOS
                result = subprocess.run(
                    ["open", "-a", app_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            else:  # Linux
                result = subprocess.run(
                    ["xdg-open", app_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            
            logging.info(f"Successfully opened application: {app_name}")
            return f"Opened {app_name}"
            
        except subprocess.TimeoutExpired:
            logging.error(f"Timeout opening application: {app_name}")
            return f"Timeout trying to open {app_name}"
        except FileNotFoundError:
            logging.error(f"Application not found: {app_name}")
            return f"Application '{app_name}' not found on this system"
        except Exception as e:
            logging.error(f"Failed to open application {app_name}: {str(e)}")
            return f"Failed to open application: {str(e)}"

    @staticmethod
    def set_volume(action: str) -> str:
        """Controls volume with validation (mute/unmute/up/down)."""
        try:
            # Sanitize and validate input
            action = action.strip().lower()
            
            valid_actions = ["mute", "unmute", "up", "down"]
            if action not in valid_actions:
                return f"Error: Invalid volume action. Use: {', '.join(valid_actions)}"
            
            if action == "mute":
                pyautogui.press("volumemute")
            elif action == "unmute":
                pyautogui.press("volumemute")  # Toggle
            elif action == "up":
                pyautogui.press("volumeup")
            elif action == "down":
                pyautogui.press("volumedown")
            
            logging.info(f"Volume action executed: {action}")
            return f"Volume {action} executed"
        except Exception as e:
            logging.error(f"Failed to control volume with action {action}: {str(e)}")
            return f"Failed to control volume: {str(e)}"
