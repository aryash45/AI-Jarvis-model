import pyautogui
import os
import platform

class SystemTools:
    @staticmethod
    def press_key(key: str) -> str:
        """Presses a keyboard key."""
        try:
            pyautogui.press(key)
            return f"Pressed key: {key}"
        except Exception as e:
            return f"Failed to press key: {str(e)}"

    @staticmethod
    def open_application(app_name: str) -> str:
        """Attempts to open an application."""
        system = platform.system()
        try:
            if system == "Windows":
                os.system(f"start {app_name}")
            elif system == "Darwin": # macOS
                os.system(f"open -a {app_name}")
            else: # Linux
                os.system(f"xdg-open {app_name}")
            return f"Attempted to open {app_name}"
        except Exception as e:
            return f"Failed to open application: {str(e)}"

    @staticmethod
    def set_volume(action: str) -> str:
        """Controls volume (mute/unmute/up/down)."""
        # Simple implementation using pyautogui media keys
        try:
            if action == "mute":
                pyautogui.press("volumemute")
            elif action == "unmute":
                pyautogui.press("volumemute") # Toggle
            elif action == "up":
                pyautogui.press("volumeup")
            elif action == "down":
                pyautogui.press("volumedown")
            return f"Volume action executed: {action}"
        except Exception as e:
            return f"Failed to control volume: {str(e)}"
