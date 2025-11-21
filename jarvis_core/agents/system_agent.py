from jarvis_core.tools.system_tools import SystemTools

class SystemAgent:
    def __init__(self):
        self.tools = SystemTools()

    def handle(self, command: str) -> str:
        """
        Unified handler for all system commands.
        """
        command_lower = command.lower()
        
        # Volume control
        if "mute" in command_lower:
            return self.handle_volume("mute")
        elif "unmute" in command_lower:
            return self.handle_volume("unmute")
        elif "volume up" in command_lower:
            return self.handle_volume("up")
        elif "volume down" in command_lower:
            return self.handle_volume("down")
        
        # App opening
        elif "open" in command_lower or "launch" in command_lower:
            app = command_lower.replace("open", "").replace("launch", "").strip()
            return self.open_app(app)
        
        # Media control
        elif "pause" in command_lower or "play" in command_lower:
            return self.control_media(command)
        
        return "I'm not sure how to handle that system command."

    def handle_volume(self, action: str) -> str:
        """Handles volume control."""
        return self.tools.set_volume(action)

    def open_app(self, app_name: str) -> str:
        """Handles opening applications."""
        return self.tools.open_application(app_name)

    def control_media(self, action: str) -> str:
        """Handles media keys (play/pause)."""
        if action in ['play', 'pause', 'stop']:
            # Mapping common media keys
            key_map = {'play': 'playpause', 'pause': 'playpause', 'stop': 'stop'}
            return self.tools.press_key(key_map.get(action, ''))
        return "Unknown media action."
