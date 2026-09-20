from abc import ABC, abstractmethod
from typing import BinaryIO, Optional

class BaseStorageService(ABC):
    """Abstract storage interface supporting local filesystem and cloud storage backends."""
    
    @abstractmethod
    async def save_file(self, file_data: BinaryIO, destination_path: str, content_type: Optional[str] = None) -> str:
        """Saves file to storage and returns the relative file reference or path."""
        pass
        
    @abstractmethod
    async def get_file(self, file_path: str) -> bytes:
        """Retrieves raw bytes of stored file."""
        pass
        
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Deletes file from storage."""
        pass
        
    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """Checks if file exists in storage."""
        pass
