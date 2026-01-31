import os
import subprocess
import structlog
from typing import Dict, Any
from interfaces.skill import Skill
from core.exceptions import ComponentException, FailureType

logger = structlog.get_logger()

class AppLauncher(Skill):
    """
    Skill to launch applications on Windows.
    """
    
    # Common mappings to help the system guess
    APP_MAPPINGS = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "chrome": "chrome.exe",
        "command prompt": "cmd.exe",
        "explorer": "explorer.exe",
        "code": "code",
    }

    @property
    def name(self) -> str:
        return "AppLauncher"

    async def execute(self, params: Dict[str, Any]) -> str:
        app_name = params.get("app_name", "").lower().strip()
        
        if not app_name:
            return "No application name provided."

        logger.info(f"Launching app: {app_name}")
        
        import sys
        
        try:
            if sys.platform == "darwin":
                # macOS implementation
                cmd = ["open"]
                # Map common names if needed, otherwise just try the name
                # Chrome example: "Google Chrome"
                if app_name == "chrome":
                    cmd.extend(["-a", "Google Chrome"])
                elif app_name == "terminal":
                    cmd.extend(["-a", "Terminal"])
                elif app_name == "code":
                    subprocess.Popen("code", shell=True) # VS Code usually in path
                    return f"Opening {app_name}..."
                else:
                    cmd.extend(["-a", app_name])
                    
                subprocess.Popen(cmd)
                return f"Opening {app_name} on Mac..."
                
            elif sys.platform == "win32":
                # Windows implementation
                command = self.APP_MAPPINGS.get(app_name, app_name)
                
                if command.endswith(".exe") or app_name in self.APP_MAPPINGS:
                     subprocess.Popen(command, shell=True)
                else:
                     os.system(f"start {command}")
                return f"Opening {app_name}..."
            else:
                return "Unsupported platform for AppLauncher."
                
        except Exception as e:
            logger.error(f"Failed to launch {app_name}", error=str(e))
            return f"Failed to open {app_name}."
