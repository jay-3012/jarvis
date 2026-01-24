import os
import structlog
from typing import Dict, Any
from interfaces.skill import Skill

logger = structlog.get_logger()

class CodeAssistant(Skill):
    """
    Skill to manage file operations (Read/List).
    Writing is often better done via SystemCommander or specialized handling,
    but we can support simple writes.
    """

    @property
    def name(self) -> str:
        return "CodeAssistant"

    async def execute(self, params: Dict[str, Any]) -> str:
        """
        Execute code operations.
        Command format: "action filename content?"
        Proprietary syntax:
        - read filename
        - list folder
        - create filename content...
        """
        raw_cmd = params.get("command", "").strip()
        parts = raw_cmd.split(" ", 2)
        
        if not parts:
            return "No code command provided."
            
        action = parts[0].lower()
        
        try:
            if action == "read":
                if len(parts) < 2: return "Please specify a file to read."
                path = parts[1]
                if not os.path.exists(path): return f"File not found: {path}"
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                # Truncate for TTS
                summary = content[:500] + ("..." if len(content) > 500 else "")
                return f"Contents of {path}:\n{summary}"

            elif action == "list":
                path = parts[1] if len(parts) > 1 else "."
                if not os.path.exists(path): return f"Path not found: {path}"
                files = os.listdir(path)
                return f"Files in {path}: {', '.join(files[:20])}"
                
            elif action == "create":
                if len(parts) < 3: return "Usage: create filename content"
                path = parts[1]
                content = parts[2]
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"Created file {path}."
                
            else:
                return f"Unknown code action: {action}"

        except Exception as e:
            logger.error(f"CodeAssistant Error: {raw_cmd}", error=str(e))
            return f"Code Error: {str(e)}"
