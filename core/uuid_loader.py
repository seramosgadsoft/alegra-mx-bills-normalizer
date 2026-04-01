"""
UUID loader for reading and validating UUIDs from text file.
"""
import re
from typing import List, Set
import logging


logger = logging.getLogger(__name__)


class UUIDLoader:
    """Loads and validates UUIDs from a text file."""
    
    UUID_PATTERN = re.compile(
        r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    )
    
    def __init__(self, file_path: str):
        """
        Initialize the UUID loader.
        
        Args:
            file_path: Path to the text file containing UUIDs
        """
        self.file_path = file_path
    
    def load_uuids(self) -> List[str]:
        """
        Load UUIDs from the file.
        
        Returns:
            List of valid, unique UUIDs in uppercase
            
        Raises:
            FileNotFoundError: If the UUID file doesn't exist
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            uuids = []
            seen_uuids: Set[str] = set()
            invalid_count = 0
            duplicate_count = 0
            
            for line_num, line in enumerate(lines, 1):
                # Strip whitespace and skip empty lines
                uuid_str = line.strip()
                if not uuid_str:
                    continue
                
                # Normalize to uppercase
                uuid_str = uuid_str.upper()
                
                # Validate UUID format
                if not self.is_valid_uuid(uuid_str):
                    logger.warning(f"Line {line_num}: Invalid UUID format: {uuid_str}")
                    invalid_count += 1
                    continue
                
                # Check for duplicates
                if uuid_str in seen_uuids:
                    logger.warning(f"Line {line_num}: Duplicate UUID found: {uuid_str}")
                    duplicate_count += 1
                    continue
                
                uuids.append(uuid_str)
                seen_uuids.add(uuid_str)
            
            logger.info(f"Loaded {len(uuids)} valid UUIDs from {self.file_path}")
            if invalid_count > 0:
                logger.warning(f"Skipped {invalid_count} invalid UUIDs")
            if duplicate_count > 0:
                logger.warning(f"Skipped {duplicate_count} duplicate UUIDs")
            
            return uuids
            
        except FileNotFoundError:
            logger.error(f"UUID file not found: {self.file_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading UUIDs from {self.file_path}: {e}")
            raise
    
    @classmethod
    def is_valid_uuid(cls, uuid_str: str) -> bool:
        """
        Validate UUID format.
        
        Args:
            uuid_str: UUID string to validate
            
        Returns:
            True if valid UUID format, False otherwise
        """
        return bool(cls.UUID_PATTERN.match(uuid_str))
