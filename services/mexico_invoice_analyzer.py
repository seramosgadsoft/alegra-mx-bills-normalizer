"""
Mexico Invoice Analyzer service wrapper.
"""
import os
import logging
from typing import Optional, Dict, Any
from invoice_analyzer import invoice_analyzer, login


logger = logging.getLogger(__name__)


class MexicoInvoiceAnalyzer:
    """Wrapper for Invoice Analyzer API for processing Mexican XML invoices."""
    
    def __init__(self):
        """Initialize the Mexico Invoice Analyzer."""
        pass
    
    def analyze_xml_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Analyze an XML invoice file.
        
        Args:
            file_path: Path to the XML file
            
        Returns:
            Parsed invoice data as JSON dictionary, or None if failed
        """
        try:
            # Read XML file content
            with open(file_path, 'rb') as f:
                xml_data = f.read()
            
            # Extract filename
            filename = os.path.basename(file_path)
            
            # Call the invoice analyzer API
            logger.info(f"Analyzing XML file: {filename}")
            result = invoice_analyzer(filename, xml_data)
            
            if result is None:
                logger.error(f"Invoice analyzer returned None for file: {filename}")
                return None
            
            logger.info(f"Successfully analyzed: {filename}")
            return result
            
        except FileNotFoundError:
            logger.error(f"XML file not found: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Error analyzing XML file {file_path}: {e}", exc_info=True)
            return None
    
    def extract_uuid_from_analyzed_data(self, analyzed_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract UUID from analyzed invoice data.
        
        Args:
            analyzed_data: Analyzed invoice data from API
            
        Returns:
            UUID string if found, None otherwise
        """
        try:
            # For Mexico, UUID is in cufe field
            uuid = analyzed_data.get("document_data", {}).get(
                "document_information", {}
            ).get("cufe")
            
            return uuid
        except Exception as e:
            logger.error(f"Error extracting UUID from analyzed data: {e}")
            return None
    
    def extract_issuer_id(self, analyzed_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract issuer/provider ID from analyzed data.
        
        Args:
            analyzed_data: Analyzed invoice data from API
            
        Returns:
            Issuer ID if found, None otherwise
        """
        try:
            issuer_id = analyzed_data.get("document_data", {}).get(
                "issuer", {}
            ).get("id_issuer")
            
            return issuer_id
        except Exception as e:
            logger.error(f"Error extracting issuer ID from analyzed data: {e}")
            return None
