"""
XML file searcher for finding invoice files by UUID.
"""
import os
import re
from typing import List
import logging
from models.models import FileSearchResult


logger = logging.getLogger(__name__)


class XMLFileSearcher:
    """Searches for XML files containing a specific UUID in their filename."""
    
    def __init__(self, bills_directory: str = "bills"):
        """
        Initialize the XML file searcher.
        
        Args:
            bills_directory: Root directory containing the bills folders
        """
        self.bills_directory = bills_directory
        
        if not os.path.exists(bills_directory):
            raise FileNotFoundError(f"Bills directory not found: {bills_directory}")
    
    def search_by_uuid(self, uuid: str) -> FileSearchResult:
        """
        Search for XML files containing the given UUID.
        
        Args:
            uuid: UUID to search for (case-insensitive)
            
        Returns:
            FileSearchResult with found file paths and months
        """
        uuid_upper = uuid.upper()
        found_files = []
        found_months = []
        
        # Search through all subdirectories (01-12 for months)
        for month_dir in sorted(os.listdir(self.bills_directory)):
            month_path = os.path.join(self.bills_directory, month_dir)
            
            # Skip if not a directory
            if not os.path.isdir(month_path):
                continue
            
            # Search for files in this month directory
            for filename in os.listdir(month_path):
                # Only process .xml files
                if not filename.lower().endswith('.xml'):
                    continue
                
                # Check if UUID is in the filename (case-insensitive)
                if uuid_upper in filename.upper():
                    file_path = os.path.join(month_path, filename)
                    found_files.append(file_path)
                    found_months.append(month_dir)
                    logger.debug(f"Found UUID {uuid} in file: {file_path}")
        
        result = FileSearchResult(
            uuid=uuid,
            found=len(found_files) > 0,
            file_paths=found_files,
            months=found_months
        )
        
        if result.has_duplicates:
            logger.warning(
                f"UUID {uuid} found in multiple files ({len(found_files)}): "
                f"{', '.join(found_files)}"
            )
        elif result.is_unique:
            logger.info(f"UUID {uuid} found in: {result.single_file_path}")
        else:
            logger.info(f"UUID {uuid} not found in any files")
        
        return result
    
    def search_multiple_uuids(self, uuids: List[str]) -> List[FileSearchResult]:
        """
        Search for multiple UUIDs.
        
        Args:
            uuids: List of UUIDs to search for
            
        Returns:
            List of FileSearchResult objects
        """
        results = []
        for uuid in uuids:
            result = self.search_by_uuid(uuid)
            results.append(result)
        return results
