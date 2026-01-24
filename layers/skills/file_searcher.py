import os
import structlog
import fnmatch
from typing import Dict, Any
from interfaces.skill import Skill

logger = structlog.get_logger()

class FileSearcher(Skill):
    """
    Skill to search for files in the filesystem.
    """

    @property
    def name(self) -> str:
        return "FileSearcher"

    async def execute(self, params: Dict[str, Any]) -> str:
        """
        Execute file search.
        Command format: "pattern path?"
        Example: "*.py C:/Users/vishw/jarvis"
        """
        raw_cmd = params.get("command", "").strip()
        parts = raw_cmd.split(" ", 1)
        
        pattern = parts[0]
        # Default to current directory if no path provided
        root_path = parts[1] if len(parts) > 1 else "."
        
        # Normalize path
        if root_path == ".":
            root_path = os.getcwd()
            
        if not os.path.exists(root_path):
            return f"Path not found: {root_path}"

        logger.info(f"Searching for '{pattern}' in '{root_path}'...")
        
        matches = []
        try:
            # Walk the directory tree
            for root, dirs, files in os.walk(root_path):
                # Filter files matching the pattern
                for filename in fnmatch.filter(files, pattern):
                    full_path = os.path.join(root, filename)
                    matches.append(full_path)
                    
                    # Safety limit to prevent overwhelming output/memory
                    if len(matches) >= 10:
                        break
                if len(matches) >= 10:
                    break
            
            if not matches:
                return f"No files found matching '{pattern}' in '{root_path}'."
            
            # Format output
            output = f"Found {len(matches)} files:\n"
            for m in matches:
                output += f"- {m}\n"
            
            if len(matches) == 10:
                output += "...and more (limit reached)."
                
            return output

        except Exception as e:
            logger.error(f"FileSearcher Error", error=str(e))
            return f"Search Error: {str(e)}"
