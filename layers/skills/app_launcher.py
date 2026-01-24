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

        command = self.APP_MAPPINGS.get(app_name, app_name)
        
        logger.info(f"Launching app: {app_name} -> {command}")
        
        try:
            # os.startfile is Windows specific and very convenient as it acts like double-clicking
            # But specific commands like 'code' might need shell=True via subprocess
            if command.endswith(".exe") or app_name in self.APP_MAPPINGS:
                 subprocess.Popen(command, shell=True)
            else:
                 # Try generic start
                 os.system(f"start {command}")
                 
            return f"Opening {app_name}..."
        except Exception as e:
            logger.error(f"Failed to launch {app_name}", error=str(e))
            return f"Failed to open {app_name}."
