import subprocess
import structlog
from typing import Dict, Any
from interfaces.skill import Skill

logger = structlog.get_logger()

class GitController(Skill):
    """
    Skill to manage git operations.
    """

    @property
    def name(self) -> str:
        return "GitController"

    async def execute(self, params: Dict[str, Any]) -> str:
        """
        Execute git commands.
        Expected params: {'action': str, 'args': str}
        Example: {'action': 'commit', 'args': '-m "Initial commit"'}
        """
        # We accept direct command strings for simplicity via [[GIT: command]]
        # e.g. [[GIT: commit -m "foo"]]
        git_cmd = params.get("command", "").strip()

        if not git_cmd:
            return "No git command provided."

        # Safety: We assume the user says "Jarvis, git push", so LLM extracts "push".
        # Or LLM provides the full "git push origin main".
        # We will prefix with "git" if missing, or handle full `[[GIT: ...]]`.
        
        full_command = f"git {git_cmd}"
        
        logger.info(f"Executing git command: {full_command}")

        try:
            result = subprocess.run(full_command, shell=True, capture_output=True, text=True, timeout=30)
            
            output = result.stdout.strip()
            error = result.stderr.strip()
            
            if result.returncode == 0:
                return f"Git Executed. {output[:200]}" if output else "Git command successful."
            else:
                return f"Git Error: {error[:200]}"
                
        except Exception as e:
            logger.error(f"Failed to execute git: {full_command}", error=str(e))
            return f"Failed to execute git: {str(e)}"
