import os
import structlog
from typing import Dict, Any, List
from datetime import datetime
from interfaces.skill import Skill

logger = structlog.get_logger()

class FileManager(Skill):
    """
    Skill to manage file operations: list, read, write (later).
    """

    @property
    def name(self) -> str:
        return "FileManager"

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute file operation.
        Params:
            action (str): "list_files", "read_file"
            path (str): Target path
        """
        action = params.get("action", "list_files")
        path = params.get("path", ".")

        # Normalize path (expand user, abs path)
        if path == "~":
            path = os.path.expanduser("~")
        elif path == ".":
            path = os.getcwd()
        else:
            path = os.path.expanduser(path)
            path = os.path.abspath(path)

        if action == "list_files":
            return self._list_files(path)
        else:
            return {"error": f"Unknown file action: {action}"}

    def _list_files(self, path: str) -> Dict[str, Any]:
        """List files in directory with metadata."""
        if not os.path.exists(path):
            return {"error": f"Path not found: {path}"}
        
        if not os.path.isdir(path):
            return {"error": f"Path is not a directory: {path}"}

        try:
            logger.info(f"Listing files in '{path}'...")
            items = []
            
            # List directory content
            with os.scandir(path) as it:
                for entry in it:
                    try:
                        stat = entry.stat()
                        items.append({
                            "name": entry.name,
                            "type": "directory" if entry.is_dir() else "file",
                            "size": stat.st_size,
                            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "path": entry.path
                        })
                    except Exception as e:
                        logger.warning(f"Error reading entry {entry.name}: {e}")
                        continue
            
            # Sort: Directories first, then files
            items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
            
            return {
                "path": path,
                "total": len(items),
                "items": items
            }
            
        except Exception as e:
            logger.error(f"List files error", error=str(e))
            return {"error": str(e)}
