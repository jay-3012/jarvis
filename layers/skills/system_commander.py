import subprocess
import structlog
from typing import Dict, Any
from interfaces.skill import Skill

logger = structlog.get_logger()

class SystemCommander(Skill):
    """
    Skill to execute shell commands.
    """

    @property
    def name(self) -> str:
        return "SystemCommander"

    async def execute(self, params: Dict[str, Any]) -> str:
        command = params.get("command", "").strip()

        if not command:
            return "No command provided."

        logger.info(f"Executing shell command: {command}")

        try:
            # Capture output with timeout
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
            
            output = result.stdout.strip()
            error = result.stderr.strip()
            
            if result.returncode == 0:
                if output:
                    # Truncate output if too long for TTS
                    return f"Output: {output[:100]}..." if len(output) > 100 else f"Output: {output}"
                return "Command executed successfully."
            else:
                return f"Error: {error[:100]}"
                
        except Exception as e:
            logger.error(f"Failed to execute command: {command}", error=str(e))
            return f"Failed to execute command: {str(e)}"
