from pathlib import Path
from typing import BinaryIO, Optional
from backend.app.services.storage.base import BaseStorageService

class LocalStorageService(BaseStorageService):
    """Local filesystem implementation of file storage abstraction using pathlib."""
    
    def __init__(self, base_dir: str = "storage/uploads"):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
    async def save_file(self, file_data: BinaryIO, destination_path: str, content_type: Optional[str] = None) -> str:
        target_path = self.base_dir / destination_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(target_path, "wb") as f:
            f.write(file_data.read())
            
        return str(target_path.relative_to(self.base_dir))
        
    async def get_file(self, file_path: str) -> bytes:
        target_path = self.base_dir / file_path
        if not target_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(target_path, "rb") as f:
            return f.read()
            
    async def delete_file(self, file_path: str) -> bool:
        target_path = self.base_dir / file_path
        if target_path.exists():
            target_path.unlink()
            return True
        return False
        
    async def file_exists(self, file_path: str) -> bool:
        target_path = self.base_dir / file_path
        return target_path.exists()
