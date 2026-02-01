import os
import structlog
from typing import List, Dict, Any
from layers.cognitive.memory import SemanticMemory

logger = structlog.get_logger()

class ContextLoader:
    """
    Loads and indexes codebase files into Semantic Memory.
    """
    
    def __init__(self, memory: SemanticMemory):
        self.memory = memory
        self.exclude_dirs = {'.git', 'venv', '__pycache__', 'node_modules', '.idea', '.vscode', 'chroma_db'}
        self.include_exts = {'.py', '.md', '.txt', '.bat', '.json'}

    def load_directory(self, root_path: str):
        """
        Recursively walk the directory and index files.
        """
        logger.info("Starting context loading", root_path=root_path)
        count = 0
        
        for dirpath, dirnames, filenames in os.walk(root_path):
            # Filter directories
            dirnames[:] = [d for d in dirnames if d not in self.exclude_dirs]
            
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in self.include_exts:
                    full_path = os.path.join(dirpath, filename)
                    try:
                        self.process_file(full_path, root_path)
                        count += 1
                    except Exception as e:
                        logger.error("Failed to process file", file=filename, error=str(e))
                        
        logger.info("Context loading complete", files_processed=count)

    def process_file(self, file_path: str, root_path: str):
        """
        Read, chunk, and save a single file.
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            if not content.strip():
                return
                
            # Create relative path for metadata
            rel_path = os.path.relpath(file_path, root_path)
            
            # Simple chunking for now
            chunks = self.chunk_text(content)
            
            for i, chunk in enumerate(chunks):
                metadata = {
                    "source": "codebase",
                    "file_path": rel_path,
                    "filename": os.path.basename(file_path),
                    "chunk_index": i,
                    "type": "code" if file_path.endswith(".py") else "document"
                }
                
                # Add file context to chunk
                decorated_chunk = f"File: {rel_path}\n---\n{chunk}"
                
                self.memory.save_context(decorated_chunk, metadata)
                
        except Exception as e:
            logger.error("Error reading file", path=file_path, error=str(e))
            raise

    def chunk_text(self, text: str, chunk_size: int = 1500, overlap: int = 200) -> List[str]:
        """
        Split text into chunks with overlap.
        """
        chunks = []
        if len(text) <= chunk_size:
            return [text]
            
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap
            
        return chunks
